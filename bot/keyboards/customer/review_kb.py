from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.helpers import button_messages


def get_review_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_messages["review_messages"]["ready"], callback_data="ready_for_review")],
        [InlineKeyboardButton(text=button_messages["review_messages"]["review_back"], callback_data="review_back")]
    ])
