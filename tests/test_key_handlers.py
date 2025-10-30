import asyncio
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bot.handlers import key_management


class DummyMessage:
    def __init__(self) -> None:
        self.texts: list[str] = []
        self.documents: list[tuple[object, str | None]] = []

    async def answer(self, text: str, reply_markup=None) -> None:
        self.texts.append(text)
        if reply_markup is not None:
            self.documents.append((reply_markup, None))

    async def answer_document(self, document: object, caption: str | None = None) -> None:
        self.documents.append((document, caption))


class DummyCallback:
    def __init__(self, data: str, user_id: int = 1) -> None:
        self.data = data
        self.message = DummyMessage()
        self.from_user = SimpleNamespace(id=user_id)
        self.answer = AsyncMock()


@pytest.fixture(autouse=True)
def reset_pending():
    key_management.PENDING_CREATIONS.clear()
    yield
    key_management.PENDING_CREATIONS.clear()


def test_create_key_flow(monkeypatch, tmp_path) -> None:
    callback = DummyCallback(data="create_key")

    store_mock = AsyncMock()
    monkeypatch.setattr(key_management, "_store_key", store_mock)
    monkeypatch.setattr(key_management, "create_client", lambda uuid, email, path: f"vless://{uuid}")
    monkeypatch.setattr(key_management, "generate_qr_code", lambda link: BytesIO(b"qr"))
    monkeypatch.setattr(key_management, "reload_xray", lambda: None)
    monkeypatch.setattr(
        key_management,
        "get_settings",
        lambda: SimpleNamespace(xray_config_path=str(tmp_path / "config.json")),
    )

    asyncio.run(key_management.handle_create_key(callback))
    assert "Выберите срок" in callback.message.texts[0]

    expire_callback = DummyCallback("create_key:expires:7d")
    asyncio.run(key_management.handle_create_key_expiration(expire_callback))
    assert "ограничение по количеству устройств" in expire_callback.message.texts[0]

    devices_callback = DummyCallback("create_key:devices:3")
    asyncio.run(key_management.handle_create_key_devices(devices_callback))

    store_mock.assert_awaited_once()
    assert any("Ключ создан" in text for text in devices_callback.message.texts)
    assert devices_callback.message.documents, "Ожидался QR-код"


def test_create_key_failure(monkeypatch, tmp_path) -> None:
    callback = DummyCallback(data="create_key")

    async def failing_store(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("db down")

    def failing_client(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("xray error")

    monkeypatch.setattr(key_management, "_store_key", failing_store)
    monkeypatch.setattr(key_management, "create_client", failing_client)
    monkeypatch.setattr(key_management, "reload_xray", lambda: None)
    monkeypatch.setattr(
        key_management,
        "get_settings",
        lambda: SimpleNamespace(xray_config_path=str(tmp_path / "config.json")),
    )

    asyncio.run(key_management.handle_create_key(callback))
    expire_callback = DummyCallback("create_key:expires:permanent")
    asyncio.run(key_management.handle_create_key_expiration(expire_callback))

    devices_callback = DummyCallback("create_key:devices:unlimited")
    asyncio.run(key_management.handle_create_key_devices(devices_callback))

    devices_callback.answer.assert_called_with("Не удалось создать ключ", show_alert=True)


def test_handle_delete_key(monkeypatch, tmp_path) -> None:
    uuid = "11111111-2222-3333-4444-555555555555"
    callback = DummyCallback(data=f"delete_key:{uuid}")

    monkeypatch.setattr(key_management, "remove_client", lambda _uuid, _path: True)
    monkeypatch.setattr(key_management, "_delete_key_record", AsyncMock())
    monkeypatch.setattr(key_management, "reload_xray", lambda: None)
    monkeypatch.setattr(
        key_management,
        "get_settings",
        lambda: SimpleNamespace(xray_config_path=str(tmp_path / "config.json")),
    )

    asyncio.run(key_management.handle_delete_key(callback))

    callback.answer.assert_called_with("Ключ удалён", show_alert=True)
    assert any(uuid in text for text in callback.message.texts)


def test_handle_delete_key_not_found(monkeypatch, tmp_path) -> None:
    callback = DummyCallback(data="delete_key:missing")

    monkeypatch.setattr(key_management, "remove_client", lambda _uuid, _path: False)
    monkeypatch.setattr(key_management, "_delete_key_record", AsyncMock())
    monkeypatch.setattr(key_management, "reload_xray", lambda: None)
    monkeypatch.setattr(
        key_management,
        "get_settings",
        lambda: SimpleNamespace(xray_config_path=str(tmp_path / "config.json")),
    )

    asyncio.run(key_management.handle_delete_key(callback))

    callback.answer.assert_called_with("Ключ не найден", show_alert=True)


def test_handle_delete_key_without_uuid(monkeypatch) -> None:
    callback = DummyCallback(data="delete_key:")
    monkeypatch.setattr(key_management, "get_settings", lambda: SimpleNamespace(xray_config_path="cfg"))

    asyncio.run(key_management.handle_delete_key(callback))

    callback.answer.assert_called_with("UUID не найден", show_alert=True)


def test_handle_delete_prompt(monkeypatch) -> None:
    callback = DummyCallback(data="delete_key")

    monkeypatch.setattr(
        key_management,
        "_fetch_keys",
        AsyncMock(return_value=[SimpleNamespace(uuid="u1", email="test@example.com")]),
    )

    asyncio.run(key_management.handle_delete_prompt(callback))

    assert callback.message.texts[0].startswith("Выберите ключ")
    callback.answer.assert_called_once()


def test_handle_delete_prompt_no_keys(monkeypatch) -> None:
    callback = DummyCallback(data="delete_key")

    monkeypatch.setattr(key_management, "_fetch_keys", AsyncMock(return_value=[]))

    asyncio.run(key_management.handle_delete_prompt(callback))

    callback.answer.assert_called_with("Ключи отсутствуют", show_alert=True)


def test_handle_list_keys(monkeypatch) -> None:
    callback = DummyCallback(data="list_keys")

    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        key_management,
        "_fetch_keys",
        AsyncMock(
            return_value=[
                SimpleNamespace(uuid="u1", email="mail1", expires_at=now, device_limit=3),
                SimpleNamespace(uuid="u2", email=None, expires_at=None, device_limit=None),
            ]
        ),
    )

    asyncio.run(key_management.handle_list_keys(callback))

    text = callback.message.texts[0]
    assert "Список ключей" in text and "Лимит устройств" in text
    callback.answer.assert_called_once()


def test_handle_list_keys_empty(monkeypatch) -> None:
    callback = DummyCallback(data="list_keys")

    monkeypatch.setattr(key_management, "_fetch_keys", AsyncMock(return_value=[]))

    asyncio.run(key_management.handle_list_keys(callback))

    callback.answer.assert_called_with("Ключей пока нет", show_alert=True)


def test_handle_settings(monkeypatch) -> None:
    callback = DummyCallback(data="settings")

    monkeypatch.setattr(
        key_management,
        "get_settings",
        lambda: SimpleNamespace(
            xray_config_path="/app/xray.json",
            xray_host="example.com",
            xray_port=443,
            xray_reload_command="service xray restart",
        ),
    )

    asyncio.run(key_management.handle_settings(callback))

    assert callback.message.texts[0].startswith("⚙️ Настройки")
    callback.answer.assert_called_once()
