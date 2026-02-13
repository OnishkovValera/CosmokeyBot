from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_admin_main_keyboard,
    BTN_ADMIN_STATS,
    BTN_BACK,
    get_back_keyboard
)
from bot.services.admin import stats_service

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_STATS
)
async def show_stats(message: Message, state: FSMContext):
    await state.set_state(AdminStates.viewing_stats)

    # Собираем статистику
    users_count = await stats_service.get_users_count()
    gifts_count = await stats_service.get_gifts_count()
    assistance_stats = await stats_service.get_assistance_stats()
    rewards_stats = await stats_service.get_rewards_stats()

    # Формируем текст
    text = (
        "📊 **Общая статистика бота**\n\n"
        f"👥 **Пользователи:** {users_count}\n"
        f"🎁 **Выдано подарков:** {gifts_count}\n\n"

        "📩 **Обращения по типам:**\n"
        f"  🔧 Дефект: {assistance_stats['by_type'].get('defect', 0)}\n"
        f"  ⚠️ Жалоба: {assistance_stats['by_type'].get('complaint', 0)}\n"
        f"  📝 Отзыв:  {assistance_stats['by_type'].get('feedback', 0)}\n\n"

        "🔄 **Обращения по статусам:**\n"
        f"  🟢 Новые:       {assistance_stats['by_status'].get('new', 0)}\n"
        f"  🟡 В работе:    {assistance_stats['by_status'].get('in_progress', 0)}\n"
        f"  ✅ Завершено:   {assistance_stats['by_status'].get('completed', 0)}\n"
        f"  ❌ Отклонено:   {assistance_stats['by_status'].get('rejected', 0)}\n\n"

        "💰 **Выплаты за отзывы:**\n"
        f"  Всего заявок: {rewards_stats['total']}\n"
        f"  Выплачено:    {rewards_stats['paid']}\n"
        f"  Ожидает:      {rewards_stats['pending']}\n"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()  # кнопка «Назад» в главное меню
    )


@router.message(
    AdminStates.viewing_stats,
    F.text == BTN_BACK
)
async def back_to_menu(message: Message, state: FSMContext):
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_main_keyboard()
    )