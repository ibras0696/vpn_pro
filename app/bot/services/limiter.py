"""Ограничение количества одновременных подключений."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, Set

LOG_PATTERN = re.compile(r"uuid=(?P<uuid>[0-9a-fA-F-]+).*?ip=(?P<ip>[0-9.]+)")


def parse_active_ips(log_path: str | Path) -> dict[str, set[str]]:
    """Собрать карту UUID → множество IP из access.log.

    Аргументы:
        log_path (str | Path): Путь к файлу журналов XRay.

    Возвращает:
        dict[str, set[str]]: Словарь uuid → уникальные IP-адреса.
    """

    path = Path(log_path)
    if not path.exists():
        return {}

    mapping: Dict[str, Set[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = LOG_PATTERN.search(line)
        if not match:
            continue
        uuid = match.group("uuid")
        ip = match.group("ip")
        mapping.setdefault(uuid, set()).add(ip)
    return mapping


def detect_overuse(log_path: str | Path, limit: int = 3) -> dict[str, set[str]]:
    """Найти клиентов, превысивших лимит подключений.

    Аргументы:
        log_path (str | Path): Путь к access.log.
        limit (int): Допустимое количество уникальных IP.

    Возвращает:
        dict[str, set[str]]: Нарушители и их IP.
    """

    active = parse_active_ips(log_path)
    return {uuid: ips for uuid, ips in active.items() if len(ips) > limit}


def apply_tc_limit(uuid: str, bandwidth: str = "1mbit") -> None:
    """Применить ограничение скорости через tc.

    Аргументы:
        uuid (str): Идентификатор клиента.
        bandwidth (str): Максимальная скорость, например "1mbit".
    """

    class_id = uuid.replace("-", "")[:4]
    command = [
        "tc",
        "class",
        "replace",
        "dev",
        "eth0",
        "parent",
        "1:",
        "classid",
        f"1:{class_id}",
        "htb",
        "rate",
        bandwidth,
    ]
    subprocess.run(command, check=True)


def handle_overuse(log_path: str | Path, limit: int = 3, bandwidth: str = "1mbit") -> list[str]:
    """Наложить ограничение на клиентов, превысивших лимит.

    Аргументы:
        log_path (str | Path): Файл логов с UUID и IP.
        limit (int): Максимум разрешённых устройств.
        bandwidth (str): Ограничение скорости для tc.

    Возвращает:
        list[str]: UUID, для которых применено ограничение.
    """

    offenders = detect_overuse(log_path, limit)
    for uuid in offenders:
        apply_tc_limit(uuid, bandwidth)
    return list(offenders.keys())
