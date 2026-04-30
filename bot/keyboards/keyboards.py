from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Generates the main navigation keyboard"""
    kb = [
        [
            KeyboardButton(text="📅 Today"),
            KeyboardButton(text="📅 Tomorrow")
        ],
        [
            KeyboardButton(text="🗓️ Week Browser"),
            KeyboardButton(text="📤 Upload Schedule")
        ],
        [
            KeyboardButton(text="⚙️ Settings")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholders="Select an option"
    )

def get_browser_keyboard():
    """Inline keyboard for browsing schedule day by day"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data="browser_prev"),
            InlineKeyboardButton(text="❌", callback_data="browser_exit"),
            InlineKeyboardButton(text="➡️", callback_data="browser_next")
        ]
    ])