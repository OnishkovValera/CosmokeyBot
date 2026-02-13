from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.utils.helpers import button_messages


def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=button_messages['get_gift'])],
        [KeyboardButton(text=button_messages['support'])],
        [KeyboardButton(text=button_messages['review'])],
        [KeyboardButton(text=button_messages['info'])],
    ], resize_keyboard=True)


def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

