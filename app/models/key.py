"""Модель ключей доступа для XRay."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Key(Base):
    """Хранит данные VLESS-ключей.

    Атрибуты:
        id (int): Первичный ключ таблицы.
        uuid (str): Уникальный идентификатор клиента в XRay.
        email (str): Контакт пользователя или комментарий.
        created_at (datetime): Время создания ключа.
        expires_at (datetime | None): Срок действия ключа.
        device_limit (int | None): Максимальное количество устройств.
    """

    __tablename__ = "keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    device_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
