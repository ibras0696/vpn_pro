"""Публичный хендлер команды /help."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.services.xray import compose_vless_link
from app.config import get_settings

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Показать справочную информацию."""

    settings = get_settings()

    example_link = compose_vless_link(
        "11111111-1111-1111-1111-111111111111",
        "user@example.com",
    )

    network = (settings.xray_network or "").lower()

    details = [
        f"• Адрес: {settings.xray_host}:{settings.xray_port}",
        f"• Сеть (type): {network or 'tcp'}",
        f"• Шифрование (security): {settings.xray_security or 'none'}",
    ]

    if network == "grpc" and settings.xray_service_name:
        details.append(f"• gRPC serviceName: {settings.xray_service_name}")
    if settings.xray_flow:
        details.append(f"• Flow: {settings.xray_flow}")

    text = (
        "ℹ️ <b>Справка</b>\n\n"
        "• /start — панель администратора (нужен доступ ADMIN_ID)\n"
        "• /help — показать это сообщение\n\n"
        "Администратор выдаёт ключ через кнопку «Создать ключ». \n"
        "Бот возвращает vless-ссылку и QR-код для подключения.\n\n"
        "Пример ссылки:\n"
        f"<code>{example_link}</code>\n\n"
        "Параметры подключения:\n"
        + "\n".join(details)
        + "\n\nСвяжитесь с администратором, чтобы получить ключ или продлить доступ."
    )

    await message.answer(text)
