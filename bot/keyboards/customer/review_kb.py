from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_review_kb() -> InlineKeyboardMarkup:
    """Inline-клавиатура с одной кнопкой «Готов»."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готов", callback_data="ready_for_review")]
    ])

def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура с одной кнопкой «🔙 Назад»."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )