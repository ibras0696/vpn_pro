# Тестирование и проверка качества

## Набор тестов
- `tests/test_db_connection.py` — проверка базового подключения SQLAlchemy.
- `tests/test_admin_access.py` — middleware и ограничения доступа администратора.
- `tests/test_key_handlers.py` — inline-хендлеры создания/удаления ключей.
- `tests/test_create_key.py`, `tests/test_remove_key.py` — операции с конфигом XRay и QR-коды.
- `tests/test_expiration.py` — планировщик истёкших ключей.
- `tests/test_limiter.py` — анализ access.log и применение `tc`.
- `tests/test_full_flow.py` — сквозной сценарий create → expire → delete.

## Команды
```bash
pytest -q --disable-warnings
python3 -m coverage run -m pytest
python3 -m coverage report
```

## Минимальные критерии
- Покрытие по пакету `app/` не ниже 80% (текущие показатели — ~89%).
- Тесты должны выполняться в чистом окружении без реального XRay (используются mock-файлы).
- Для проверки линтеров рекомендуется `ruff check .`.
