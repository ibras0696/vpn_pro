"""Точка входа Telegram-бота."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.key_management import router as key_router
from app.bot.middlewares.admin import AdminAccessMiddleware
from app.config import get_settings


async def main() -> None:
    """Инициализировать бота и запустить долгий поллинг."""

    settings = get_settings()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()

    dispatcher.include_router(admin_router)
    dispatcher.include_router(key_router)
    dispatcher.update.outer_middleware(AdminAccessMiddleware(settings.admin_id))

    logger.info("Запуск бота с ADMIN_ID=%s", settings.admin_id)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
