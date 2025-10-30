"""Сервисы работы с конфигурацией XRay."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from io import BytesIO
from pathlib import Path
from typing import Any, Sequence

import qrcode
from loguru import logger

from app.config import get_settings


def _load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Конфиг не найден: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def _save_config(config: dict[str, Any], config_path: Path) -> None:
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_vless_clients(config: dict[str, Any]) -> list[dict[str, Any]]:
    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") != "vless":
            continue
        settings = inbound.setdefault("settings", {})
        return settings.setdefault("clients", [])
    raise ValueError("В конфиге отсутствует inbound с протоколом vless")


def compose_vless_link(uuid: str, email: str) -> str:
    settings = get_settings()

    params: list[tuple[str, str]] = []
    if settings.xray_flow:
        params.append(("flow", settings.xray_flow))
    if settings.xray_security:
        params.append(("security", settings.xray_security))
    if settings.xray_network:
        params.append(("type", settings.xray_network))
    if settings.xray_network.lower() == "grpc" and settings.xray_service_name:
        params.append(("serviceName", settings.xray_service_name))

    query = "&".join(f"{key}={value}" for key, value in params if value)

    base = f"vless://{uuid}@{settings.xray_host}:{settings.xray_port}"
    if query:
        base = f"{base}?{query}"
    return f"{base}#{email}"


def create_client(uuid: str, email: str, config_path: str | Path) -> str:
    """Добавить клиента в конфигурацию XRay.

    Аргументы:
        uuid (str): Уникальный идентификатор клиента.
        email (str): Комментарий/почта пользователя, который будет записан в конфиге.
        config_path (str | Path): Путь к файлу config.json.

    Возвращает:
        str: Сформированная vless-ссылка для подключения.
    """

    path = Path(config_path)
    config = _load_config(path)
    clients = _get_vless_clients(config)

    if any(client.get("id") == uuid for client in clients):
        raise ValueError("Клиент с таким UUID уже существует")

    clients.append({"id": uuid, "email": email})
    _save_config(config, path)

    return compose_vless_link(uuid, email)


def remove_client(uuid: str, config_path: str | Path) -> bool:
    """Удалить клиента по UUID из файла конфигурации.

    Аргументы:
        uuid (str): Уникальный идентификатор, который нужно удалить.
        config_path (str | Path): Путь к файлу config.json.

    Возвращает:
        bool: True если запись была удалена, иначе False.
    """

    path = Path(config_path)
    config = _load_config(path)
    clients = _get_vless_clients(config)

    initial_len = len(clients)
    clients[:] = [client for client in clients if client.get("id") != uuid]

    if len(clients) == initial_len:
        return False

    _save_config(config, path)
    return True


def _resolve_reload_command(command: Sequence[str] | None = None) -> list[str]:
    if command:
        return list(command)

    settings = get_settings()
    if settings.xray_reload_command:
        return shlex.split(settings.xray_reload_command)

    return ["systemctl", "reload", "xray"]


def reload_xray(command: Sequence[str] | None = None) -> None:
    """Перезагрузить службу XRay.

    Аргументы:
        command (Sequence[str] | None): Команда для перезагрузки (по умолчанию systemctl reload xray).

    Возвращает:
        None
    """

    cmd = _resolve_reload_command(command)
    executable = cmd[0]

    if shutil.which(executable) is None:
        logger.warning("Команда перезагрузки XRay недоступна: %s", executable)
        return

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        logger.warning("Не удалось выполнить команду перезагрузки XRay: %s", cmd)


def generate_qr_code(link: str) -> BytesIO:
    """Сгенерировать QR-код для vless-ссылки.

    Аргументы:
        link (str): Ссылка vless://, которую нужно преобразовать.

    Возвращает:
        BytesIO: Буфер PNG с изображением QR-кода.
    """

    image = qrcode.make(link)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


__all__ = [
    "create_client",
    "remove_client",
    "reload_xray",
    "generate_qr_code",
    "compose_vless_link",
]
