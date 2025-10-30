import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bot.services import scheduler
from app.db import Base
from app.models.key import Key


def test_expired_keys_are_removed(monkeypatch) -> None:
    async def run_test() -> tuple[list[str], list[str]]:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        @asynccontextmanager
        async def override_session():
            session = session_factory()
            try:
                yield session
            finally:
                await session.close()

        monkeypatch.setattr(scheduler, "get_session", override_session)

        async with session_factory() as session:
            session.add(
                Key(
                    uuid="expired",
                    email="expired@example.com",
                    expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                )
            )
            session.add(
                Key(
                    uuid="active",
                    email="active@example.com",
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            await session.commit()

        removed = await scheduler.remove_expired_keys(now=datetime.now(timezone.utc))

        async with session_factory() as session:
            result = await session.execute(select(Key.uuid))
            remaining = [row[0] for row in result]

        return removed, remaining

    removed_keys, remaining_keys = asyncio.run(run_test())

    assert "expired" in removed_keys
    assert "expired" not in remaining_keys
    assert "active" in remaining_keys


def test_scheduler_loop_respects_stop(monkeypatch) -> None:
    calls: list[int] = []

    async def fake_remove() -> list[str]:
        calls.append(1)
        return []

    monkeypatch.setattr(scheduler, "remove_expired_keys", fake_remove)

    async def run_loop() -> None:
        stop_event = asyncio.Event()
        task = asyncio.create_task(scheduler.scheduler_loop(stop_event, interval_seconds=0.1))
        await asyncio.sleep(0.25)
        stop_event.set()
        await task

    asyncio.run(run_loop())

    assert calls, "Планировщик не вызвал очистку"
