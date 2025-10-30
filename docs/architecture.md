# Архитектура

## Слои приложения

- **Bot Layer** — Aiogram 3, маршруты `/start`, inline-хендлеры создания и удаления ключей.
- **Services Layer** — утилиты работы с XRay (`xray.py`), планировщик (`scheduler.py`) и ограничитель подключений (`limiter.py`).
- **Data Layer** — SQLAlchemy AsyncEngine (`db.py`), модели `User` и `Key`, репликация изменений в XRay.
- **Infra** — Docker Compose, PostgreSQL, Makefile, Poetry.

## Поток создания ключа
1. Администратор нажимает кнопку «Создать ключ» в inline-меню.
2. Хендлер `handle_create_key` генерирует UUID, вызывает `services.xray.create_client` и сохраняет запись в БД.
3. XRay конфиг обновляется и перезапускается командой `systemctl reload xray` (в тестах мокируется).
4. Бот отправляет администратору vless-ссылку и QR-код.

## Планировщик
- `scheduler.remove_expired_keys` — выборка ключей со сроком `expires_at` ≤ now, удаление из БД.
- `scheduler.scheduler_loop` — таймер на `interval_seconds`, который вызывает очистку до срабатывания `stop_event`.

## Ограничение подключений
- `limiter.parse_active_ips` анализирует `access.log` и собирает IP по UUID.
- `limiter.detect_overuse` возвращает нарушителей при превышении лимита активных IP.
- `limiter.handle_overuse` вызывает `tc` для снижения скорости (в продакшене — real command, в тестах — mock).
