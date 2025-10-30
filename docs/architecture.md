# Архитектура

## Слои приложения

- **Bot Layer** — Aiogram 3, маршруты `/start`, `/help`, inline-хендлеры создания/управления ключами.
- **Services Layer** — утилиты работы с XRay (`xray.py`), планировщик (`scheduler.py`) и ограничитель подключений (`limiter.py`).
- **Data Layer** — SQLAlchemy AsyncEngine (`db.py`), модели `User` и `Key`, репликация изменений в XRay.
- **Infra** — Docker Compose, PostgreSQL, Makefile, Poetry.

## Поток создания ключа
1. Администратор нажимает кнопку «Создать ключ» в inline-меню.
2. Бот предлагает выбрать срок действия (1/7/30 дней или «без ограничения») и лимит устройств (1/3/5/без ограничений).
3. После выбора вызывается `services.xray.create_client`, формируется запись `Key` (`uuid`, `email`, `expires_at`, `device_limit`).
4. Конфиг XRay обновляется; при наличии `XRAY_RELOAD_COMMAND` запускается соответствующая команда (по умолчанию `systemctl reload xray`, если доступна).
5. Администратор получает vless-ссылку, сведения о сроке/лимите и QR-код.

## Планировщик
- `scheduler.remove_expired_keys` — выборка ключей со сроком `expires_at` ≤ now, удаление из БД.
- `scheduler.scheduler_loop` — таймер на `interval_seconds`, который вызывает очистку до срабатывания `stop_event`.

## Ограничение подключений
- `limiter.parse_active_ips` анализирует `access.log` и собирает IP по UUID.
- `limiter.detect_overuse` возвращает нарушителей при превышении лимита активных IP.
- `limiter.handle_overuse` вызывает `tc` для снижения скорости (в продакшене — real command, в тестах — mock).
