import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot.middlewares.admin import AdminAccessMiddleware


class DummyMessage:
    def __init__(self, user_id: int) -> None:
        self.from_user = SimpleNamespace(id=user_id)
        self.answers: list[dict[str, object]] = []

    async def answer(self, text: str, reply_markup=None) -> None:
        self.answers.append({"text": text, "reply_markup": reply_markup})


def test_non_admin_gets_rejection() -> None:
    middleware = AdminAccessMiddleware(admin_id=1)
    message = DummyMessage(user_id=999)
    handler = AsyncMock()

    asyncio.run(middleware(handler, message, {}))

    handler.assert_not_called()
    assert message.answers and message.answers[0]["text"] == "🚫 Доступ запрещён"


def test_admin_passes_through_middleware() -> None:
    middleware = AdminAccessMiddleware(admin_id=42)
    message = DummyMessage(user_id=42)
    handler = AsyncMock(return_value="ok")

    result = asyncio.run(middleware(handler, message, {}))

    handler.assert_called_once()
    assert result == "ok"


def test_callback_rejection(monkeypatch) -> None:
    class FakeCallbackBase:
        pass

    middleware = AdminAccessMiddleware(admin_id=1)

    monkeypatch.setattr("app.bot.middlewares.admin.CallbackQuery", FakeCallbackBase)

    class FakeEvent(FakeCallbackBase):
        def __init__(self) -> None:
            self.from_user = SimpleNamespace(id=2)
            self.message = DummyMessage(user_id=2)
            self.answer = AsyncMock()

    callback = FakeEvent()
    handler = AsyncMock()

    asyncio.run(middleware(handler, callback, {}))

    callback.answer.assert_called_once()
    assert callback.message.answers
