# Настройка окружения

## Требования

- Docker и Docker Compose
- Python 3.11+
- Poetry

## Шаги

1. (Опционально) Выполните `make setup-server`, чтобы подготовить чистую Ubuntu (Docker, Compose, Poetry).
2. Скопируйте `.env.example` в `.env` и укажите свои значения.
3. Выполните `make init` для установки зависимостей.
4. Запустите `make up`, чтобы поднять PostgreSQL и бота в Docker.

## Полезные команды

- `make ps` — статус контейнеров.
- `make logs` — поток логов бота.
- `make test` — запуск тестового набора.
- `make clean` — удалить кэш и временные файлы проекта.
- `make clean-docker` — остановить и очистить docker-тома.
- `make setup-server` — обновить систему, установить Docker/Poetry и заранее загрузить базовые образы.
