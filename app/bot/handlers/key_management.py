"""Хендлеры управления ключами XRay."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.types.input_file import BufferedInputFile
from loguru import logger
from sqlalchemy import delete

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
    """Подсказать администратору, как удалить ключ.

    Аргументы:
        callback (CallbackQuery): Событие от базовой кнопки «Удалить ключ».
    """

    await callback.answer("Выберите ключ из списка", show_alert=True)
