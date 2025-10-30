"""Планировщик для очистки просроченных ключей."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Iterable

from loguru import logger
from sqlalchemy import delete, select

from app.db import get_session
from app.models.key import Key


async def remove_expired_keys(now: datetime | None = None) -> list[str]:
    """Удалить ключи, у которых истёк срок действия.

    Аргументы:
        now (datetime | None): Текущее время, передавайте для тестов.

    Возвращает:
        list[str]: Список UUID удалённых ключей.
    """

    current_time = now or datetime.now(timezone.utc)
    async with get_session() as session:
        result = await session.execute(
            select(Key).where(Key.expires_at.is_not(None), Key.expires_at <= current_time)
        )
        expired_keys: Iterable[Key] = result.scalars().all()
        uuids = [key.uuid for key in expired_keys]

        if uuids:
            await session.execute(delete(Key).where(Key.uuid.in_(uuids)))
            await session.commit()
            logger.info("Удалены просроченные ключи: %s", uuids)
        return uuids


async def scheduler_loop(stop_event: asyncio.Event, interval_seconds: int = 3600) -> None:
    """Периодически запускать удаление просроченных ключей.

    Аргументы:
        stop_event (asyncio.Event): Событие для завершения работы цикла.
        interval_seconds (int): Пауза между проверками в секундах.
    """

    while not stop_event.is_set():
        try:
            await remove_expired_keys()
        except Exception as error:  # noqa: BLE001
            logger.exception("Ошибка при очистке ключей: %s", error)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            continue
