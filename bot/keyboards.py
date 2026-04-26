from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Generates the main navigation keyboard"""
    kb = [
        [
            KeyboardButton(text="📅 Today"),
            KeyboardButton(text="📅 Tomorrow")
        ],
        [
            KeyboardButton(text="⚙️ Settings")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True, # Makes the buttons smaller
        input_field_placeholders="Select an option"
    )