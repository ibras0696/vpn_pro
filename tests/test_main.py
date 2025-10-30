import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot import main


class DummyDispatcher:
    def __init__(self) -> None:
        self.routers: list[object] = []
        self.middlewares: list[object] = []
        self.start_polling = AsyncMock()
        self.update = SimpleNamespace(outer_middleware=self._outer_middleware)

    def include_router(self, router: object) -> None:
        self.routers.append(router)

    def _outer_middleware(self, middleware: object) -> None:
        self.middlewares.append(middleware)


class DummyBot:
    def __init__(self, token: str, parse_mode: object) -> None:
        self.token = token
        self.parse_mode = parse_mode


def test_main_starts_polling(monkeypatch) -> None:
    dispatcher = DummyDispatcher()

    monkeypatch.setattr(main, "Dispatcher", lambda: dispatcher)
    monkeypatch.setattr(main, "Bot", DummyBot)
    monkeypatch.setattr(main, "AdminAccessMiddleware", lambda admin_id: f"mw:{admin_id}")
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(bot_token="token", admin_id=99),
    )

    asyncio.run(main.main())

    assert dispatcher.start_polling.await_count == 1
    assert dispatcher.middlewares == ["mw:99"]
    assert len(dispatcher.routers) >= 2
