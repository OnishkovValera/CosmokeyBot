from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.helpers import admin_button_messages


def back_button_for_post():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=admin_button_messages["special_post"]["special_post_cancel"], callback_data="special_post_cancel")]
    ])