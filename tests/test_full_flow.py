import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bot.services import scheduler, xray
from app.db import Base
from app.models.key import Key


def test_full_key_lifecycle(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    config = {"inbounds": [{"protocol": "vless", "settings": {"clients": []}}]}
    config_path.write_text(json.dumps(config), encoding="utf-8")

    settings_stub = SimpleNamespace(
        xray_config_path=str(config_path),
        xray_host="vpn.example.com",
        xray_port=443,
    )
    monkeypatch.setattr(xray, "get_settings", lambda: settings_stub)

    uuid = "c48d7f8a-0f67-421c-8f68-1f4a3a0d1234"
    email = "flow@example.com"

    async def workflow() -> None:
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
                    uuid=uuid,
                    email=email,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            await session.commit()

        link = xray.create_client(uuid, email, config_path)
        assert uuid in link

        async with session_factory() as session:
            await session.execute(
                update(Key)
                .where(Key.uuid == uuid)
                .values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=5))
            )
            await session.commit()

        removed = await scheduler.remove_expired_keys(now=datetime.now(timezone.utc))
        assert uuid in removed

        assert xray.remove_client(uuid, config_path) is True
        saved = json.loads(config_path.read_text(encoding="utf-8"))
        assert saved["inbounds"][0]["settings"]["clients"] == []

    asyncio.run(workflow())
