from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ==================== REPLY-КЛАВИАТУРЫ ====================

# ----- Главное меню администратора -----
BTN_ADMIN_ASSISTANCE = "📩 Обращения"
BTN_ADMIN_REWARDS = "💰 Выплатить за отзывы"
BTN_ADMIN_EDIT_TEXTS = "✏️ Поменять текст сообщений"
BTN_ADMIN_SEARCH_REQUEST = "🔍 Поиск заявки по ID"
BTN_ADMIN_MAILING = "📢 Сделать рассылку"
BTN_ADMIN_DONE = "🚫 Закончить"
BTN_ADMIN_STATS = "📊 Статистика"
BTN_ADMIN_SET_INFO_POST = "📦 Установить инфо-пост"
BTN_ADMIN_USERS = "👥 Список пользователей"

def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADMIN_ASSISTANCE)],
            [KeyboardButton(text=BTN_ADMIN_REWARDS)],
            [KeyboardButton(text=BTN_ADMIN_EDIT_TEXTS)],
            [KeyboardButton(text=BTN_ADMIN_SEARCH_REQUEST)],
            [KeyboardButton(text=BTN_ADMIN_STATS)],
            [KeyboardButton(text=BTN_ADMIN_SET_INFO_POST)],
            [KeyboardButton(text=BTN_ADMIN_USERS)],
            [KeyboardButton(text=BTN_ADMIN_MAILING)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_admin_mode_keyboard() -> ReplyKeyboardMarkup:
    """Синоним для главной клавиатуры (для обратной совместимости)."""
    return get_admin_main_keyboard()

def get_admin_done_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с одной кнопкой «Закончить»."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_ADMIN_DONE)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# ----- Кнопки навигации -----
BTN_BACK = "🔙 Назад"
BTN_CANCEL = "❌ Отмена"

def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ----- Выбор типа обращения -----
BTN_ASSISTANCE_DEFECT = "🔧 Дефект"
BTN_ASSISTANCE_COMPLAINT = "⚠️ Жалоба"
BTN_ASSISTANCE_FEEDBACK = "📝 Отзыв"

def get_assistance_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ASSISTANCE_DEFECT)],
            [KeyboardButton(text=BTN_ASSISTANCE_COMPLAINT)],
            [KeyboardButton(text=BTN_ASSISTANCE_FEEDBACK)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# ----- Выбор статуса заявок -----
BTN_STATUS_NEW = "🟢 Новые"
BTN_STATUS_IN_PROGRESS = "🟡 В работе"
BTN_STATUS_COMPLETED = "🔴 Закрытые"

def get_status_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STATUS_NEW)],
            [KeyboardButton(text=BTN_STATUS_IN_PROGRESS)],
            [KeyboardButton(text=BTN_STATUS_COMPLETED)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# ==================== INLINE-КЛАВИАТУРЫ ====================

def get_request_actions_keyboard(request_type: str, request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔄 Изменить статус",
                callback_data=f"change_status:{request_type}:{request_id}"
            ),
            InlineKeyboardButton(
                text="💬 Добавить комментарий",
                callback_data=f"add_comment:{request_type}:{request_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад к списку",
                callback_data=f"back_to_list:{request_type}"
            )
        ]
    ])

def get_status_choice_inline(request_type: str, request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🆕 Новое", callback_data=f"set_status:{request_type}:{request_id}:new"),
            InlineKeyboardButton(text="⚙️ В работе", callback_data=f"set_status:{request_type}:{request_id}:in_progress")
        ],
        [
            InlineKeyboardButton(text="✅ Завершено", callback_data=f"set_status:{request_type}:{request_id}:completed"),
            InlineKeyboardButton(text="❌ Отклонено", callback_data=f"set_status:{request_type}:{request_id}:rejected")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_detail:{request_type}:{request_id}")]
    ])

def get_mailing_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, отправить", callback_data="mailing:confirm"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data="mailing:cancel")
        ]
    ])