"""Хендлеры управления ключами XRay."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.input_file import BufferedInputFile
from loguru import logger
from sqlalchemy import delete, select

from app.bot.services.xray import create_client, generate_qr_code, remove_client, reload_xray
from app.config import get_settings
from app.db import get_session
from app.models.key import Key

router = Router()

EXPIRATION_CHOICES: dict[str, tuple[str, timedelta | None]] = {
    "1d": ("1 день", timedelta(days=1)),
    "7d": ("7 дней", timedelta(days=7)),
    "30d": ("30 дней", timedelta(days=30)),
    "permanent": ("Без ограничения", None),
}

DEVICE_CHOICES: dict[str, tuple[str, int | None]] = {
    "1": ("1 устройство", 1),
    "3": ("3 устройства", 3),
    "5": ("5 устройств", 5),
    "unlimited": ("Без ограничения", None),
}

PENDING_CREATIONS: dict[int, dict[str, Any]] = {}


async def _store_key(uuid: str, email: str, *, expires_at: datetime | None, device_limit: int | None) -> None:
    """Сохранить информацию о ключе в базе данных."""

    async with get_session() as session:
        session.add(Key(uuid=uuid, email=email, expires_at=expires_at, device_limit=device_limit))
        await session.commit()


async def _delete_key_record(uuid: str) -> None:
    """Удалить запись ключа из базы данных."""

    async with get_session() as session:
        result = await session.execute(delete(Key).where(Key.uuid == uuid))
        if result.rowcount:
            await session.commit()


async def _fetch_keys() -> list[Key]:
    """Получить все ключи из базы данных."""

    async with get_session() as session:
        result = await session.execute(select(Key))
        return list(result.scalars().all())


def _build_delete_keyboard(keys: list[Key]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🗑 {key.email or key.uuid[:8]}",
                callback_data=f"delete_key:{key.uuid}",
            )
        ]
        for key in keys
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_expiration_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"create_key:expires:{value}")]
        for value, (label, _) in EXPIRATION_CHOICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_device_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"create_key:devices:{value}")]
        for value, (label, _) in DEVICE_CHOICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _format_expiration(expires_at: datetime | None) -> str:
    if not expires_at:
        return "Без ограничения по сроку"
    return "Действует до: " + expires_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _format_device_limit(limit: int | None) -> str:
    return f"Лимит устройств: {limit}" if limit else "Лимит устройств: не ограничен"


@router.callback_query(F.data == "create_key")
async def handle_create_key(callback: CallbackQuery) -> None:
    """Запустить мастер создания ключа."""

    settings = get_settings()
    user_id = callback.from_user.id
    PENDING_CREATIONS[user_id] = {
        "email": f"user_{user_id}@vpn.local",
        "config_path": Path(settings.xray_config_path),
    }

    await callback.message.answer(
        "Выберите срок действия ключа:",
        reply_markup=_build_expiration_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("create_key:expires:"))
async def handle_create_key_expiration(callback: CallbackQuery) -> None:
    """Сохранить выбранный срок действия и предложить выбрать лимит устройств."""

    user_id = callback.from_user.id
    pending = PENDING_CREATIONS.get(user_id)
    if pending is None:
        await callback.answer("Нет активного запроса", show_alert=True)
        return

    _, _, value = callback.data.split(":", maxsplit=2)
    choice = EXPIRATION_CHOICES.get(value)
    if choice is None:
        await callback.answer("Неизвестный выбор", show_alert=True)
        return

    expires_delta = choice[1]
    expires_at = None if expires_delta is None else datetime.now(timezone.utc) + expires_delta
    pending["expires_at"] = expires_at
    PENDING_CREATIONS[user_id] = pending

    await callback.message.answer(
        "Теперь выберите ограничение по количеству устройств:",
        reply_markup=_build_device_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("create_key:devices:"))
async def handle_create_key_devices(callback: CallbackQuery) -> None:
    """Завершить создание ключа с учётом выбранных параметров."""

    user_id = callback.from_user.id
    pending = PENDING_CREATIONS.get(user_id)
    if pending is None:
        await callback.answer("Нет активного запроса", show_alert=True)
        return

    _, _, value = callback.data.split(":", maxsplit=2)
    choice = DEVICE_CHOICES.get(value)
    if choice is None:
        await callback.answer("Неизвестный выбор", show_alert=True)
        return

    pending["device_limit"] = choice[1]

    try:
        await _finalize_creation(callback, pending)
        await callback.answer("Ключ создан", show_alert=True)
    except Exception as error:  # noqa: BLE001
        logger.exception("Ошибка при создании ключа: %s", error)
        await callback.answer("Не удалось создать ключ", show_alert=True)
    finally:
        PENDING_CREATIONS.pop(user_id, None)


async def _finalize_creation(callback: CallbackQuery, data: dict[str, Any]) -> None:
    client_uuid = str(uuid4())
    email: str = data["email"]
    expires_at: datetime | None = data.get("expires_at")
    device_limit: int | None = data.get("device_limit")
    config_path: Path = Path(data["config_path"])

    vless_link = create_client(client_uuid, email, config_path)
    await _store_key(client_uuid, email, expires_at=expires_at, device_limit=device_limit)
    reload_xray()

    qr_buffer = generate_qr_code(vless_link)
    qr_file = BufferedInputFile(qr_buffer.getvalue(), filename=f"{client_uuid}.png")

    info_lines = [
        "✅ Ключ создан",
        vless_link,
        _format_expiration(expires_at),
        _format_device_limit(device_limit),
    ]

    await callback.message.answer("\n".join(info_lines))
    await callback.message.answer_document(qr_file, caption="QR-код для подключения")
    logger.info(
        "Создан ключ %s (expires=%s, limit=%s)",
        client_uuid,
        expires_at,
        device_limit,
    )


@router.callback_query(F.data.startswith("delete_key:"))
async def handle_delete_key(callback: CallbackQuery) -> None:
    """Удалить ключ по UUID из конфига и базы данных."""

    _, _, uuid = callback.data.partition(":")
    settings = get_settings()
    config_path = Path(settings.xray_config_path)

    if not uuid:
        await callback.answer("UUID не найден", show_alert=True)
        return

    removed = remove_client(uuid, config_path)
    if removed:
        await _delete_key_record(uuid)
        reload_xray()
        await callback.answer("Ключ удалён", show_alert=True)
        await callback.message.answer(f"🗑 Ключ {uuid} удалён")
        logger.info("Удалён ключ %s", uuid)
    else:
        await callback.answer("Ключ не найден", show_alert=True)


@router.callback_query(F.data == "delete_key")
async def handle_delete_prompt(callback: CallbackQuery) -> None:
    """Показать список ключей для удаления."""

    keys = await _fetch_keys()
    if not keys:
        await callback.answer("Ключи отсутствуют", show_alert=True)
        return

    keyboard = _build_delete_keyboard(keys)
    await callback.message.answer("Выберите ключ для удаления:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "list_keys")
async def handle_list_keys(callback: CallbackQuery) -> None:
    """Вывести список активных ключей."""

    keys = await _fetch_keys()
    if not keys:
        await callback.answer("Ключей пока нет", show_alert=True)
        return

    lines = []
    for key in keys:
        lines.append(
            "\n".join(
                filter(
                    None,
                    [
                        f"• {key.email or 'без_email'}",
                        f"  UUID: {key.uuid}",
                        f"  {_format_expiration(key.expires_at)}",
                        f"  {_format_device_limit(key.device_limit)}",
                    ],
                )
            )
        )

    await callback.message.answer("Список ключей:\n" + "\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "settings")
async def handle_settings(callback: CallbackQuery) -> None:
    """Отправить краткую справку по настройкам."""

    settings = get_settings()
    info = (
        "⚙️ Настройки бота:\n"
        f"• XRAY_CONFIG_PATH: {settings.xray_config_path}\n"
        f"• XRAY_HOST: {settings.xray_host}\n"
        f"• XRAY_PORT: {settings.xray_port}\n"
        f"• XRAY_RELOAD_COMMAND: {settings.xray_reload_command or 'не задана'}"
    )
    await callback.message.answer(info)
    await callback.answer()
