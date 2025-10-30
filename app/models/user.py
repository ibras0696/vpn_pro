"""Модель пользователя Telegram."""

from sqlalchemy import Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    """Пользователь бота для управления правами доступа.

    Атрибуты:
        id (int): Уникальный идентификатор записи.
        tg_id (int): Telegram ID пользователя.
        is_admin (bool): Флаг административного доступа.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
