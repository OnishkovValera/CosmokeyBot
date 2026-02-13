from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

button_messages = {
    "get_gift": "🎁 Получить подарок",
    "support": "💬 Нужна помощь",
    "review": "💸 Деньги за отзыв",
    "info": "ℹ Узнать информацию",
    "help": {
        "defect": "Брак/Дефект",
        "complaint": "Претензия/Жалоба",
        "feedback": "Обратная связь",
        "back" : "Назад"
    },
    "review_messages": {
        "ready": "Да, готов",
        "set_photo": "Прикрепите фото-результаты(до/после).",
        "set_link": "Отправьте ссылку на ваш опубликованный отзыв",
        "review_back": "Назад"
    }
}

admin_button_messages = {
    "special_post": {
        "special_post_cancel": "Отмена"
    }
}


def add_back_button(keyboard: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return keyboard
