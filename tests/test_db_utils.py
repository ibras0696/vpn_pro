import asyncio
from types import SimpleNamespace

from sqlalchemy import text

import app
from app import config
from app import db
from app.models.user import User


def test_config_caching(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "token-test")
    config.reset_settings_cache()

    settings = config.get_settings()

    assert settings.bot_token == "token-test"


def test_get_session_sqlite(monkeypatch) -> None:
    db.reset_engine_cache()
    monkeypatch.setattr(
        db,
        "get_settings",
        lambda: SimpleNamespace(database_url="sqlite+aiosqlite:///:memory:"),
    )

    async def run() -> bool:
        engine = db.get_engine()
        assert "sqlite" in str(engine.url)
        async with db.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        return await db.ping_database()

    assert asyncio.run(run())


def test_app_lazy_imports() -> None:
    assert hasattr(app, "config")
    assert hasattr(app, "db")


def test_user_model_instantiation() -> None:
    user = User(tg_id=123, is_admin=True)
    assert user.tg_id == 123
    assert user.is_admin is True
