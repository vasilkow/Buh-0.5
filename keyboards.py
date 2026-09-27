from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import WEBAPP_URL

def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Казна"), KeyboardButton(text="📊 Моя статистика")],
            [KeyboardButton(text="📜 История"), KeyboardButton(text="👥 Все участники")],
            [KeyboardButton(text="💳 Долги"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🌐 Мини-приложение", web_app=WebAppInfo(url=WEBAPP_URL))],
        ],
        resize_keyboard=True
    )
    return kb

def treasury_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Пополнить", callback_data="treasury_deposit")],
            [InlineKeyboardButton(text="➖ Снять", callback_data="treasury_withdraw")],
            [InlineKeyboardButton(text="🏢 С бизнеса (5%)", callback_data="treasury_business")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
        ]
    )
    return kb

def debts_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Мне должны", callback_data="debts_owed_to_me")],
            [InlineKeyboardButton(text="➕ Добавить долг", callback_data="debts_add")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
        ]
    )
    return kb

def settings_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Уведомления: ВКЛ", callback_data="toggle_notifications")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
        ]
    )
    return kb

def back_to_main():
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Назад")]],
        resize_keyboard=True
    )
    return kb
