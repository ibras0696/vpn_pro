"""Обработчики административных команд Telegram-бота."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from app.bot.keyboards.inline import admin_menu_keyboard

router = Router()

WELCOME_TEXT = "👋 Добро пожаловать в панель управления VPN."


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Ответить администратору меню управления.

    Аргументы:
        message (Message): Входящее сообщение с командой /start.
    """

    await message.answer(WELCOME_TEXT, reply_markup=admin_menu_keyboard())
    logger.info("Администратор %s открыл основное меню", message.from_user.id)
