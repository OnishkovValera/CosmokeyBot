from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BTN_ADMIN_ASSISTANCE = "📩 Ответить на обращения"
BTN_ADMIN_REWARDS = "💰 Выплатить за отзывы"
BTN_ASSISTANCE_DEFECT = "🔧 Дефект"
BTN_ASSISTANCE_COMPLAINT = "⚠️ Жалоба"
BTN_ASSISTANCE_FEEDBACK = "📝 Отзыв"
BTN_ADMIN_DONE = "🚫 Закончить"
BTN_ADMIN_EDIT_TEXTS = "✏️ Поменять текст сообщений"
BTN_ADMIN_BACK = "🔙 Назад"
BTN_ADMIN_CANCEL = "❌ Отмена"


def get_admin_mode_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADMIN_ASSISTANCE)],
            [KeyboardButton(text=BTN_ADMIN_REWARDS)],
            [KeyboardButton(text=BTN_ADMIN_EDIT_TEXTS)],  # ← новая кнопка
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_assistance_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ASSISTANCE_DEFECT)],
            [KeyboardButton(text=BTN_ASSISTANCE_COMPLAINT)],
            [KeyboardButton(text=BTN_ASSISTANCE_FEEDBACK)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_admin_done_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_ADMIN_DONE)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_admin_back_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура с одной кнопкой «Назад»."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_ADMIN_BACK)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_admin_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура с кнопкой «Отмена»."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_ADMIN_CANCEL)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
