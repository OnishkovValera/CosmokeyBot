from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.utils.helpers import button_messages


def get_help_starter_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=button_messages["help"]["defect"])],
        [KeyboardButton(text=button_messages["help"]["complaint"])],
        [KeyboardButton(text=button_messages["help"]["feedback"])],
        [KeyboardButton(text="Назад")]
    ], resize_keyboard=True)
