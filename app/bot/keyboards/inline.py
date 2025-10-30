"""Набор inline-кнопок для административного меню."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру с основными действиями администратора.

    Возвращает:
        InlineKeyboardMarkup: Разметка с кнопками управления ключами.
    """

    buttons = [
        [
            InlineKeyboardButton(text="🔑 Создать ключ", callback_data="create_key"),
            InlineKeyboardButton(text="📋 Список ключей", callback_data="list_keys"),
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить ключ", callback_data="delete_key"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
