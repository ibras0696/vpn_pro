# Настройка окружения

## Требования

- Docker и Docker Compose
- Python 3.12+
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
- `make ubuntu-setup-script` — создать локальный скрипт `ubuntu24_setup.sh` для ручного запуска.
- `make migrate` — применить SQL-миграции (создание таблиц `users`, `keys`).
- Отредактируйте `docker/xray/config.json`, чтобы в конфиге присутствовали реальные inbound-параметры XRay.
- При необходимости задайте команду перезагрузки XRay через переменную `XRAY_RELOAD_COMMAND` (например, `service xray restart`).

### Как запустить скрипт вручную
1. Убедитесь, что файл исполняемый: `chmod +x scripts/setup_server.sh`.
2. Выполните `./scripts/setup_server.sh` или `bash scripts/setup_server.sh`.
3. После завершения при необходимости перелогиньтесь, чтобы активировать группу `docker`.

Альтернатива для Ubuntu 24:

```bash
make ubuntu-setup-script
./ubuntu24_setup.sh
```

Применение миграций базы данных:

```bash
make migrate
```
