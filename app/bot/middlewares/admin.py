"""Middleware для проверки доступа администратора."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from loguru import logger


class AdminAccessMiddleware(BaseMiddleware):
    """Проверяет, что пользователь является администратором."""

    def __init__(self, admin_id: int) -> None:
        """Сохранить идентификатор администратора.

        Аргументы:
            admin_id (int): Telegram ID пользователя-администратора.
        """

        self._admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        """Пропускает только события от администратора.

        Аргументы:
            handler (Callable): Следующий обработчик цепочки.
            event (Message | CallbackQuery): Входящее событие Telegram.
            data (dict[str, Any]): Контекст Aiogram.

        Возвращает:
            Any: Результат выполнения последующего обработчика либо None при отказе.
        """

        user = getattr(event, "from_user", None)
        user_id = getattr(user, "id", None)
        if user_id != self._admin_id:
            await self._reject(event)
            logger.warning("Доступ запрещён для пользователя %s", user_id)
            return None
        return await handler(event, data)

    @staticmethod
    async def _reject(event: Message | CallbackQuery) -> None:
        """Отправить сообщение об отказе в доступе."""

        text = "🚫 Доступ запрещён"
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
            if event.message:
                await event.message.answer(text)
        elif hasattr(event, "answer"):
            await event.answer(text)
