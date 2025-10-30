import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot import main


class DummyDispatcher:
    def __init__(self) -> None:
        self.routers: list[object] = []
        self.message_middlewares: list[object] = []
        self.callback_middlewares: list[object] = []
        self.start_polling = AsyncMock()
        self.message = SimpleNamespace(outer_middleware=self._register_message)
        self.callback_query = SimpleNamespace(outer_middleware=self._register_callback)

    def include_router(self, router: object) -> None:
        self.routers.append(router)

    def _register_message(self, middleware: object) -> None:
        self.message_middlewares.append(middleware)

    def _register_callback(self, middleware: object) -> None:
        self.callback_middlewares.append(middleware)


class DummyBot:
    def __init__(self, token: str, default=None) -> None:
        self.token = token
        self.default = default


def test_main_starts_polling(monkeypatch) -> None:
    dispatcher = DummyDispatcher()

    monkeypatch.setattr(main, "Dispatcher", lambda: dispatcher)
    monkeypatch.setattr(main, "Bot", DummyBot)
    monkeypatch.setattr(
        main,
        "AdminAccessMiddleware",
        lambda admin_id, allowed_commands=None: f"mw:{admin_id}",
    )
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(bot_token="token", admin_id=99),
    )

    asyncio.run(main.main())

    assert dispatcher.start_polling.await_count == 1
    assert dispatcher.message_middlewares == ["mw:99"]
    assert dispatcher.callback_middlewares == ["mw:99"]
    assert len(dispatcher.routers) >= 3
