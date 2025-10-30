import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot.handlers import key_management


class DummyMessage:
    def __init__(self) -> None:
        self.texts: list[str] = []
        self.documents: list[tuple[object, str | None]] = []

    async def answer(self, text: str) -> None:
        self.texts.append(text)

    async def answer_document(self, document: object, caption: str | None = None) -> None:
        self.documents.append((document, caption))


class DummyCallback:
    def __init__(self, data: str) -> None:
        self.data = data
        self.message = DummyMessage()
        self.from_user = SimpleNamespace(id=1)
        self.answer = AsyncMock()


def test_handle_create_key(monkeypatch, tmp_path) -> None:
    callback = DummyCallback(data="create_key")

    monkeypatch.setattr(key_management, "create_client", lambda uuid, email, path: f"vless://{uuid}")
    monkeypatch.setattr(key_management, "generate_qr_code", lambda link: BytesIO(b"qr"))
    monkeypatch.setattr(key_management, "_store_key", AsyncMock())
    monkeypatch.setattr(key_management, "reload_xray", lambda: None)
    monkeypatch.setattr(key_management, "BufferedInputFile", lambda data, filename: {"data": data, "filename": filename})
    monkeypatch.setattr(
        key_management,
        "get_settings",
        lambda: SimpleNamespace(xray_config_path=str(tmp_path / "config.json")),
    )

    asyncio.run(key_management.handle_create_key(callback))

    assert callback.answer.call_count == 1
    assert any("Ключ создан" in text for text in callback.message.texts)
    assert callback.message.documents, "QR-код не отправлен"


def test_handle_create_key_failure(monkeypatch, tmp_path) -> None:
    callback = DummyCallback(data="create_key")

    async def failing_store(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("db down")

    def raise_client(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("xray error")

    monkeypatch.setattr(key_management, "create_client", raise_client)
    monkeypatch.setattr(key_management, "_store_key", failing_store)
    monkeypatch.setattr(key_management, "reload_xray", lambda: None)
    monkeypatch.setattr(
        key_management,
        "get_settings",
        lambda: SimpleNamespace(xray_config_path=str(tmp_path / "config.json")),
    )

    asyncio.run(key_management.handle_create_key(callback))

    callback.answer.assert_called_once()
    assert not callback.message.documents


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

    asyncio.run(key_management.handle_delete_prompt(callback))

    callback.answer.assert_called_once()
