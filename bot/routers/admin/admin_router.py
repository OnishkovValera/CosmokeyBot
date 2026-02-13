from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_admin_mode_keyboard,
    BTN_ADMIN_ASSISTANCE,
    BTN_ADMIN_REWARDS,
)
from bot.routers.admin.subrouters.assistance import assistance_router, start_assistance
from bot.routers.admin.subrouters.rewards import rewards_router, start_rewards_review
from bot.routers.admin.subrouters.special_post_router import special_post_router
from bot.routers.admin.subrouters.text_editor import texts_editor_router

admin_router = Router()

admin_router.include_routers(
    special_post_router,
    assistance_router,
    rewards_router,
    texts_editor_router
)

admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


@admin_router.message(Command("start"))
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "🛠 Панель администратора\nВыберите режим работы:",
        reply_markup=get_admin_mode_keyboard()
    )


@admin_router.message(AdminStates.choosing_mode, F.text == BTN_ADMIN_ASSISTANCE)
async def process_mode_assistance(message: Message, state: FSMContext):
    await state.set_state(AdminStates.choosing_assistance_type)
    await start_assistance(message, state)

@admin_router.message(AdminStates.choosing_mode, F.text == BTN_ADMIN_REWARDS)
async def process_mode_rewards(message: Message, state: FSMContext):
    await state.set_state(AdminStates.viewing_rewards)
    await start_rewards_review(message, state, message.bot)