import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.bot.services import xray


def _write_config(path: Path) -> None:
    config = {"inbounds": [{"protocol": "vless", "settings": {"clients": []}}]}
    path.write_text(json.dumps(config), encoding="utf-8")


def test_create_client_updates_config(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    monkeypatch.setattr(
        xray,
        "get_settings",
        lambda: SimpleNamespace(xray_host="vpn.example.com", xray_port=443),
    )

    uuid = "123e4567-e89b-12d3-a456-426614174000"
    email = "user@example.com"

    link = xray.create_client(uuid, email, config_path)

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    clients = saved["inbounds"][0]["settings"]["clients"]

    assert any(client["id"] == uuid for client in clients)
    assert uuid in link


def test_generate_qr_code_returns_buffer() -> None:
    buffer = xray.generate_qr_code("vless://example")
    assert buffer.getbuffer().nbytes > 0


def test_create_client_duplicate(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)

    monkeypatch.setattr(
        xray,
        "get_settings",
        lambda: SimpleNamespace(xray_host="vpn.example.com", xray_port=443),
    )

    uuid = "123e4567-e89b-12d3-a456-426614174000"
    email = "user@example.com"

    xray.create_client(uuid, email, config_path)

    with pytest.raises(ValueError):
        xray.create_client(uuid, email, config_path)
