# VPN Project Bot

> Асинхронный Telegram-бот на Aiogram для управления VPN-доступом через XRay-core.

## ✨ Возможности
- создание и удаление VLESS-ключей с автоперезагрузкой XRay;
- хранение ключей в PostgreSQL, удаление просроченных ключей планировщиком;
- контроль одновременных подключений по access.log с автоматическим `tc`-ограничением;
- панель администратора с inline-меню и проверкой `ADMIN_ID`;
- генерация vless-ссылок и QR-кодов для мгновенной выдачи пользователям.

## 🚀 Быстрый старт
1. Скопируйте переменные окружения:
   ```bash
   cp .env.example .env
   ```
2. Установите зависимости проекта:
   ```bash
   poetry install
   ```
3. Запустите инфраструктуру:
   ```bash
   make up
   ```
4. Просмотрите логи бота:
   ```bash
   make logs
   ```

> ❗️ Для локальных тестов используется SQLite, а в контейнерах — PostgreSQL.

## 🔧 Переменные окружения
| Переменная | Назначение |
| --- | --- |
| `DATABASE_URL` | Подключение к PostgreSQL (psycopg) |
| `BOT_TOKEN` | Токен Telegram-бота |
| `ADMIN_ID` | Telegram ID администратора |
| `XRAY_CONFIG_PATH` | Путь к `config.json` XRay |
| `XRAY_HOST` | Домен для формирования vless-ссылки |
| `XRAY_PORT` | Порт сервиса XRay |
| `XRAY_RELOAD_COMMAND` | (опция) команда перезагрузки XRay, например `service xray restart` |

## 🧰 Make команды
- `make init` — подготовка `.env` и установка зависимостей через Poetry;
- `make setup-server` — автоматическая настройка Ubuntu: обновления, Docker/Compose/Poetry и предзагрузка образов;
- `make up` / `make down` / `make restart` — управление docker-compose;
- `make ps` — статус контейнеров;
- `make logs` — логи бота в реальном времени;
- `make lint` / `make fmt` — проверка и автоисправление Ruff;
- `make test` — запуск pytest с отключёнными предупреждениями;
- `make coverage` — отчёт по покрытию;
- `make clean` — очистка кэша, отчётов и временных файлов;
- `make clean-docker` — остановка контейнеров и удаление томов.
- `make ubuntu-setup-script` — создать исполняемый скрипт `ubuntu24_setup.sh` для ручной настройки Ubuntu 24.

### 📜 Как запускать скрипты на сервере
Скопируйте проект на сервер и выполните:

```bash
chmod +x scripts/setup_server.sh
./scripts/setup_server.sh
```

Либо воспользуйтесь make-обёрткой:

```bash
make setup-server
```

Чтобы получить копию скрипта под Ubuntu 24 рядом с проектом:

```bash
make ubuntu-setup-script
./ubuntu24_setup.sh
```

По завершении перелогиньтесь (если пользователь добавлен в группу `docker`), затем продолжайте с `make init` и `make up`.

## 🧪 Тесты и покрытие
```bash
pytest -q --disable-warnings
python3 -m coverage run -m pytest
python3 -m coverage report
```
Покрытие по коду `app/` — **92%**.

## 🐳 Docker-окружение
- `docker/Dockerfile.bot` — образ бота (Poetry + Aiogram + приложения);
- `docker/Dockerfile.postgres` — PostgreSQL с инициализацией;
- `docker/xray/config.json` — пример конфига XRay с пустым списком клиентов;
- `docker-compose.yml` — бот и база, readiness-healthcheck, volume хранения.

> Перед запуском укажите реальные параметры XRay в `docker/xray/config.json` и/или в `.env` переменную `XRAY_CONFIG_PATH`.

## 🗂️ Структура проекта
```text
app/
  bot/
    handlers/        # /start, создание и удаление ключей
    services/        # XRay, планировщик, ограничитель подключений
    keyboards/       # inline-меню администратора
    middlewares/     # проверка ADMIN_ID
  config.py          # Pydantic Settings + .env
  db.py              # Async SQLAlchemy + фабрика сессий
  models/            # User, Key
docker/              # Dockerfile'ы и init.sql
tests/               # unit и интеграционные сценарии
docs/                # расширенная документация
```

## 📚 Документация
- `docs/setup.md` — подготовка окружения и развертывание;
- `docs/architecture.md` — схема модулей и потоков данных;
- `docs/testing.md` — чек-лист проверок и полезные команды.

## ✅ Чек-лист перед релизом
- [ ] `make up` — проект собирается и поднимается в Docker;
- [ ] `pytest` и `coverage` выполняются без ошибок, покрытие ≥ 80%;
- [ ] `ruff`/`flake8` — линтер без предупреждений (`ruff check .`).
