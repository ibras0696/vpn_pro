"""Хендлеры управления ключами XRay."""

from __future__ import annotations

from pathlib import Path
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


async def _store_key(uuid: str, email: str) -> None:
    """Сохранить информацию о ключе в базе данных.

    Аргументы:
        uuid (str): Идентификатор ключа XRay.
        email (str): Комментарий/почта владельца ключа.
    """

    async with get_session() as session:
        session.add(Key(uuid=uuid, email=email))
        await session.commit()


async def _delete_key_record(uuid: str) -> None:
    """Удалить запись ключа из базы данных.

    Аргументы:
        uuid (str): Ключ, который необходимо удалить.
    """

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
    """Создать inline-клавиатуру для удаления ключей."""

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


@router.callback_query(F.data == "create_key")
async def handle_create_key(callback: CallbackQuery) -> None:
    """Создать новый ключ доступа и отправить QR-код администратору.

    Аргументы:
        callback (CallbackQuery): Событие от inline-кнопки создания ключа.
    """

    settings = get_settings()
    config_path = Path(settings.xray_config_path)
    client_uuid = str(uuid4())
    email = f"user_{callback.from_user.id}@vpn.local"

    try:
        vless_link = create_client(client_uuid, email, config_path)
        await _store_key(client_uuid, email)
        reload_xray()
    except Exception as error:  # noqa: BLE001
        logger.exception("Ошибка при создании ключа: %s", error)
        await callback.answer("Не удалось создать ключ", show_alert=True)
        return

    qr_buffer = generate_qr_code(vless_link)
    qr_file = BufferedInputFile(qr_buffer.getvalue(), filename=f"{client_uuid}.png")

    await callback.message.answer(f"✅ Ключ создан\n{vless_link}")
    await callback.message.answer_document(qr_file, caption="QR-код для подключения")
    await callback.answer("Ключ создан", show_alert=True)
    logger.info("Создан ключ %s", client_uuid)


@router.callback_query(F.data.startswith("delete_key:"))
async def handle_delete_key(callback: CallbackQuery) -> None:
    """Удалить ключ по UUID из конфига и базы данных.

    Аргументы:
        callback (CallbackQuery): Событие от inline-кнопки с UUID ключа.
    """

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

    lines = [
        f"• {key.email or 'без_email'}\n  UUID: {key.uuid}"
        for key in keys
    ]
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
        f"• XRAY_PORT: {settings.xray_port}"
    )
    await callback.message.answer(info)
    await callback.answer()
