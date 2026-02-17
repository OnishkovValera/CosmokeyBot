
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_admin_main_keyboard,
    get_back_keyboard,
    BTN_ADMIN_USERS,
    BTN_BACK
)
from bot.services.customer import user_service

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# ------------------------------------------------------------
# 1. Вход в раздел "Список пользователей"
# ------------------------------------------------------------
@router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_USERS
)
async def start_users_list(message: Message, state: FSMContext):
    await state.set_state(AdminStates.viewing_users_list)
    await state.update_data(users_offset=0)
    await show_users_page(message, state, message.bot)
    # Отправляем reply-клавиатуру «Назад» (только один раз)
    await message.answer("🔽 Используйте кнопку «Назад» для выхода", reply_markup=get_back_keyboard())

async def show_users_page(message: Message, state: FSMContext, bot: Bot):
    """Отображает текущую страницу списка пользователей (только inline-пагинация)."""
    data = await state.get_data()
    offset = data.get("users_offset", 0)
    limit = 20

    users = await user_service.get_users_page(limit=limit, offset=offset)
    total = await user_service.get_users_count()

    if not users:
        # Если пользователей нет – выходим в главное меню
        await state.set_state(AdminStates.choosing_mode)
        await message.answer(
            "❌ Пользователи не найдены.",
            reply_markup=get_admin_main_keyboard()
        )
        return

    # Удаляем предыдущее сообщение со списком (если есть)
    old_msg_id = data.get("users_list_message_id")
    if old_msg_id:
        try:
            await bot.delete_message(message.chat.id, old_msg_id)
        except:
            pass

    # Формируем текст
    text = f"👥 **Список пользователей** (всего: {total})\n\n"
    for idx, user in enumerate(users, start=offset + 1):
        username = f"@{user['username']}" if user['username'] != 'no_username' else "—"
        subscribed = "✅" if user['is_subscribed'] else "❌"
        rewarded = "🎁" if user['is_got_reward_for_subscription'] else "—"
        created = user['created_at'].strftime('%d.%m.%Y') if user.get('created_at') else '?'
        text += (
            f"{idx}. ID: `{user['id']}` | TG: `{user['telegram_id']}`\n"
            f"   👤 {username} | 📱 {user.get('phone_number', '—')}\n"
            f"   📅 {created} | Канал: {subscribed} | Подарок: {rewarded}\n\n"
        )

    # Клавиатура пагинации (inline)
    kb = []
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data="users_prev"))
    if offset + limit < total:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data="users_next"))
    if nav_buttons:
        kb.append(nav_buttons)

    sent = await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb) if kb else None
    )

    await state.update_data(users_list_message_id=sent.message_id)

# ------------------------------------------------------------
# 2. Пагинация: вперёд / назад (inline)
# ------------------------------------------------------------
@router.callback_query(
    StateFilter(AdminStates.viewing_users_list),
    F.data.in_(["users_next", "users_prev"])
)
async def paginate_users(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    offset = data.get("users_offset", 0)
    limit = 20

    if callback.data == "users_next":
        offset += limit
    elif callback.data == "users_prev":
        offset = max(0, offset - limit)

    await state.update_data(users_offset=offset)
    await callback.answer()
    await show_users_page(callback.message, state, bot)

# ------------------------------------------------------------
# 3. Возврат в главное меню (inline-кнопка)
# ------------------------------------------------------------
@router.callback_query(
    StateFilter(AdminStates.viewing_users_list),
    F.data == "users_to_menu"
)
async def back_to_menu_inline(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdminStates.choosing_mode)
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()

# ------------------------------------------------------------
# 4. Возврат через reply-кнопку «Назад»
# ------------------------------------------------------------
@router.message(
    StateFilter(AdminStates.viewing_users_list),
    F.text == BTN_BACK
)
async def back_from_users(message: Message, state: FSMContext, bot: Bot):
    await state.set_state(AdminStates.choosing_mode)
    # Убираем reply-клавиатуру «Назад» и показываем главную
    await message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_main_keyboard()
    )
    # Удаляем сообщение со списком, если оно ещё висит
    data = await state.get_data()
    list_msg_id = data.get("users_list_message_id")
    if list_msg_id:
        try:
            await bot.delete_message(message.chat.id, list_msg_id)
        except:
            pass
    await message.delete()  # удаляем команду «Назад»