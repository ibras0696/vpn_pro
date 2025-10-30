"""Конфигурация приложения и загрузка переменных окружения."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из .env или переменных окружения.

    Атрибуты:
        database_url (str): Строка подключения к базе данных PostgreSQL.
        bot_token (str): Токен Telegram-бота.
        admin_id (int): Идентификатор администратора для проверки доступа.
        xray_config_path (str): Путь к конфигурации XRay.
        xray_host (str): Домен для генерации vless-ссылки.
        xray_port (int): Порт сервиса XRay.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/postgres"
    bot_token: str = ""
    admin_id: int = 0
    xray_config_path: str = "./docker/xray/config.json"
    xray_host: str = "vpn.example.com"
    xray_port: int = 443


@lru_cache
def get_settings() -> Settings:
    """Получить singleton с настройками приложения.

    Возвращает:
        Settings: Экземпляр с загруженными переменными окружения.
    """

    return Settings()


def reset_settings_cache() -> None:
    """Очистить кэш настроек для повторной загрузки переменных окружения."""

    get_settings.cache_clear()
