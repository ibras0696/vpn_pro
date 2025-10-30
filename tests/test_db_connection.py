import asyncio
import importlib
from types import ModuleType, SimpleNamespace

import pytest


def test_ping_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    config_module: ModuleType = importlib.reload(importlib.import_module("app.config"))
    config_module.get_settings.cache_clear()

    db_module: ModuleType = importlib.reload(importlib.import_module("app.db"))
    db_module.reset_engine_cache()
    db_module.get_settings = lambda: SimpleNamespace(database_url="sqlite+aiosqlite:///:memory:")

    assert asyncio.run(db_module.ping_database())
