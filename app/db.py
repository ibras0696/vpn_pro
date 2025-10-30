"""Инициализация подключения к базе данных PostgreSQL."""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import text

from app.config import get_settings

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
    """Базовый класс для декларативных моделей."""


def get_engine() -> AsyncEngine:
    """Создать или получить кешированный движок SQLAlchemy."""

    global _engine, _session_factory

    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Вернуть фабрику асинхронных сессий."""

    global _session_factory

    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    return _session_factory


def reset_engine_cache() -> None:
    """Сбросить кеш движка и фабрики сессий."""

    global _engine, _session_factory

    _engine = None
    _session_factory = None


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Асинхронно предоставить сессию SQLAlchemy.

    Возвращает:
        AsyncIterator[AsyncSession]: Контекстный менеджер с открытой сессией.
    """

    session = get_session_factory()()
    try:
        yield session
    finally:
        await session.close()


async def ping_database() -> bool:
    """Проверить доступность базы данных, выполнив простой запрос.

    Возвращает:
        bool: True при успешном выполнении запроса, иначе False.
    """

    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False
