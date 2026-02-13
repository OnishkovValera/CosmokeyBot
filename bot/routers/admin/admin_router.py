from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.db.queries import create_user
from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    BTN_ADMIN_ASSISTANCE,
    BTN_ADMIN_REWARDS, get_admin_main_keyboard,
)
from bot.routers.admin.subrouters.admin_assistance import admin_assistance_router, enter_assistance_section
from bot.routers.admin.subrouters.mailing import mailing_router
from bot.routers.admin.subrouters.rewards import rewards_router, start_rewards_review
from bot.routers.admin.subrouters.text_editor import texts_editor_router
from bot.routers.admin.subrouters.admin_stats import router as stats_router
from bot.routers.admin.subrouters.admin_info_post import router as info_post_router
from bot.routers.admin.subrouters.admin_users import router as users_info_router

admin_router = Router()

admin_router.include_routers(
    admin_assistance_router,
    rewards_router,
    mailing_router,
    texts_editor_router,
    stats_router,
    info_post_router,
    users_info_router
)

admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


@admin_router.message(Command("start"))
async def admin_panel(message: Message, state: FSMContext):
    # ✅ Регистрируем администратора (если уже есть – обновит данные)
    await create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        chat_id=message.chat.id,
        phone_number=None
    )
    await state.clear()
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "🛠 Панель администратора\nВыберите режим работы:",
        reply_markup=get_admin_main_keyboard()
    )


@admin_router.message(AdminStates.choosing_mode, F.text == BTN_ADMIN_ASSISTANCE)
async def process_mode_assistance(message: Message, state: FSMContext):
    await state.set_state(AdminStates.choosing_assistance_type)
    await enter_assistance_section(message, state)


@admin_router.message(AdminStates.choosing_mode, F.text == BTN_ADMIN_REWARDS)
async def process_mode_rewards(message: Message, state: FSMContext):
    await state.set_state(AdminStates.viewing_rewards)
    await start_rewards_review(message, state, message.bot)


@admin_router.message(Command("add_test_users"))
async def add_test_users(message: Message):
    for i in range(60):
        await create_user(
            telegram_id=1000 + i,
            username=f"testuser{i}",
            chat_id=1000 + i,
            phone_number=None
        )
    await message.answer("✅ Добавлено 5 тестовых пользователей")