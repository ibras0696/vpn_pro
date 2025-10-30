"""Публичный хендлер команды /help."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import get_settings

router = Router()

HELP_TEXT_TEMPLATE = (
    "ℹ️ <b>Справка</b>\n"
    "\n"
    "• /start — панель администратора (нужен доступ ADMIN_ID)\n"
    "• /help — показать это сообщение\n"
    "\n"
    "Чтобы получить ключ, администратор нажимает кнопку «Создать ключ».\n"
    "Бот отправит vless-ссылку и QR-код для подключения.\n"
    "\n"
    "Пример ссылки:\n"
    "<code>vless://&lt;UUID&gt;@{host}:{port}?flow=xtls-rprx-vision&amp;security=tls&amp;type=grpc&amp;"
    "serviceName=grpc#user@example.com</code>\n"
    "\n"
    "Свяжитесь с администратором, чтобы получить ключ или продлить доступ."
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Показать справочную информацию."""

    settings = get_settings()
    await message.answer(HELP_TEXT_TEMPLATE.format(host=settings.xray_host, port=settings.xray_port))
