"""Middleware для проверки доступа администратора."""

from typing import Any, Awaitable, Callable, Iterable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from loguru import logger


class AdminAccessMiddleware(BaseMiddleware):
    """Проверяет, что пользователь является администратором."""

    def __init__(self, admin_id: int, allowed_commands: Iterable[str] | None = None) -> None:
        """Сохранить идентификатор администратора и список исключений.

        Аргументы:
            admin_id (int): Telegram ID пользователя-администратора.
            allowed_commands (Iterable[str] | None): Команды, доступные всем.
        """

        self._admin_id = admin_id
        self._allowed_commands = {cmd.lstrip("/").lower() for cmd in (allowed_commands or [])}

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

        if user_id != self._admin_id and not self._is_allowed(event):
            await self._reject(event)
            logger.warning("Доступ запрещён для пользователя %s", user_id)
            return None
        return await handler(event, data)

    def _is_allowed(self, event: Message | CallbackQuery) -> bool:
        if not self._allowed_commands:
            return False

        if hasattr(event, "text"):
            text = (getattr(event, "text") or "").strip()
            if text.startswith("/"):
                command = text.split()[0][1:]
                command = command.split("@", maxsplit=1)[0]
                return command.lower() in self._allowed_commands

        return False

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
