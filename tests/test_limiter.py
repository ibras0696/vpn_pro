from unittest import mock

from app.bot.services import limiter


def _write_log(path, uuid: str, ips: list[str]) -> None:
    lines = [f"time uuid={uuid} ip={ip}" for ip in ips]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_detect_overuse_returns_offenders(tmp_path) -> None:
    log_path = tmp_path / "access.log"
    uuid = "123e4567-e89b-12d3-a456-426614174000"
    _write_log(log_path, uuid, ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4"])

    offenders = limiter.detect_overuse(log_path, limit=3)

    assert uuid in offenders
    assert bool(offenders)


def test_handle_overuse_runs_tc(tmp_path) -> None:
    log_path = tmp_path / "access.log"
    uuid = "de305d54-75b4-431b-adb2-eb6b9e546014"
    _write_log(log_path, uuid, ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4"])

    with mock.patch("subprocess.run") as run_mock:
        offenders = limiter.handle_overuse(log_path, limit=3, bandwidth="512kbit")

    run_mock.assert_called_once()
    assert offenders == [uuid]
