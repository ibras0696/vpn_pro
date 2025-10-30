import json
from pathlib import Path
from unittest import mock

from app.bot.services import xray


def _config_with_client(path: Path, uuid: str) -> None:
    config = {
        "inbounds": [
            {
                "protocol": "vless",
                "settings": {"clients": [{"id": uuid, "email": "old@example.com"}]},
            }
        ]
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_remove_client_deletes_entry(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    uuid = "de305d54-75b4-431b-adb2-eb6b9e546014"
    _config_with_client(config_path, uuid)

    removed = xray.remove_client(uuid, config_path)

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    clients = updated["inbounds"][0]["settings"]["clients"]

    assert removed is True
    assert not clients


def test_reload_xray_uses_subprocess(monkeypatch) -> None:
    monkeypatch.setattr(xray.shutil, "which", lambda _: "/usr/bin/systemctl")
    with mock.patch("subprocess.run") as run_mock:
        xray.reload_xray()

    run_mock.assert_called_once()


def test_reload_xray_skips_when_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(xray.shutil, "which", lambda _: None)
    with mock.patch("subprocess.run") as run_mock:
        xray.reload_xray()

    run_mock.assert_not_called()


def test_remove_client_returns_false(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    _config_with_client(config_path, "another-uuid")

    assert xray.remove_client("missing", config_path) is False
