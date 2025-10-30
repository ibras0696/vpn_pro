#!/usr/bin/env bash
set -euo pipefail

SUDO=""
if [[ "${EUID}" -ne 0 ]]; then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo не найден. Запустите скрипт от root или установите sudo." >&2
    exit 1
  fi
  SUDO="sudo"
fi

echo "Обновление пакетов..."
$SUDO apt-get update -y
$SUDO apt-get upgrade -y

echo "Установка базовых зависимостей..."
$SUDO apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  software-properties-common \
  make \
  git \
  python3 \
  python3-pip \
  python3-venv

if ! command -v docker >/dev/null 2>&1; then
  echo "Установка Docker Engine..."
  $SUDO install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
  $SUDO apt-get update -y
  $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  $SUDO systemctl enable --now docker
  if [[ -n "${SUDO}" ]]; then
    CURRENT_USER=$(logname 2>/dev/null || whoami)
    $SUDO usermod -aG docker "${CURRENT_USER}"
    echo "Пользователь ${CURRENT_USER} добавлен в группу docker. Перелогиньтесь, чтобы применить изменения."
  fi
else
  echo "Docker уже установлен, пропускаем."
fi

if ! command -v docker compose >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
  echo "Docker Compose не найден. Убедитесь, что docker-compose-plugin установлен."
fi

if ! command -v poetry >/dev/null 2>&1; then
  echo "Установка Poetry..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "Poetry уже установлен, пропускаем."
fi

echo "Установка Make-команд завершена. Можно запускать 'make init' и 'make up'."
