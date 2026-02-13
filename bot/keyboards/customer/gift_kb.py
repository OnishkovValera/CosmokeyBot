from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_subscribe_for_gift_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я подписан", callback_data="subscribed")],
        [InlineKeyboardButton(text="Я не подписан", callback_data="not_subscribed")]
    ])

def check_subscription_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить подписку", callback_data="gift_check_subscription")]
    ])