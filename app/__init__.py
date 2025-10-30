"""Пакет приложения для Telegram-бота управления VPN."""

from importlib import import_module
from types import ModuleType
from typing import Any

__all__ = ["config", "db"]


def __getattr__(name: str) -> Any:
    """Ленивая загрузка модулей пакета."""

    if name in __all__:
        module: ModuleType = import_module(f"app.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module 'app' has no attribute {name!r}")
