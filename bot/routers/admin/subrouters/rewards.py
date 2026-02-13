from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_admin_done_keyboard,
    BTN_ADMIN_DONE, get_admin_mode_keyboard,
)
from bot.keyboards.admin.callback_data import ProcessRequestCD
from bot.keyboards.customer.main_menu_kb import main_menu
from bot.services.admin import admin_service

rewards_router = Router()
rewards_router.message.filter(IsAdmin())
rewards_router.callback_query.filter(IsAdmin())


# ------------------------------------------------------------------
# Старт просмотра заявок на выплату
# ------------------------------------------------------------------
async def start_rewards_review(message: Message, state: FSMContext, bot):
    await state.set_state(AdminStates.viewing_rewards)
    await show_reward_requests(message, state, bot)


async def show_reward_requests(message: Message, state: FSMContext, bot):
    requests = await admin_service.get_pending_rewards(limit=10)

    if not requests:
        # ✅ Возвращаем в главное меню админки
        await state.set_state(AdminStates.choosing_mode)
        await message.answer(
            "✅ Нет необработанных заявок на выплату.\n"
            "Выберите режим работы:",
            reply_markup=get_admin_mode_keyboard()  # админ-клавиатура
        )
        return

    await message.answer(
        f"💰 Найдено {len(requests)} заявок. Отправляю...",
        reply_markup=get_admin_done_keyboard()
    )

    for req in requests:
        media = await admin_service.get_media_for_request("reward", req["id"])
        await admin_service.send_request_to_admin(
            bot,
            message.chat.id,
            "reward",
            req,
            media,
            state
        )
    await message.answer("⚠️ Все заявки показаны. Нажмите «Закончить» для выхода.")


# ------------------------------------------------------------------
# Обработка инлайн‑кнопки «Обработано»
# ------------------------------------------------------------------
@rewards_router.callback_query(
    StateFilter(AdminStates.viewing_rewards),
    ProcessRequestCD.filter(F.request_type == "reward")
)
async def process_reward_done(
        callback: CallbackQuery,
        callback_data: ProcessRequestCD,
        state: FSMContext
):
    await callback.answer("Выплата помечена как выполненная.")
    await admin_service.mark_request_processed("reward", callback_data.request_id)

    msg_ids = list(map(int, callback_data.msg_ids.split(",")))
    await admin_service.delete_admin_messages(callback.bot, callback.message.chat.id, msg_ids)

    data = await state.get_data()
    sent_map = data.get("sent_messages", {})
    sent_map.pop(str(callback_data.request_id), None)
    await state.update_data(sent_messages=sent_map)


# ------------------------------------------------------------------
# Завершение сессии выплат
# ------------------------------------------------------------------
@rewards_router.message(AdminStates.viewing_rewards, F.text == BTN_ADMIN_DONE)
async def finish_rewards_session(message: Message, state: FSMContext):
    data = await state.get_data()
    sent_map = data.get("sent_messages", {})
    for msg_ids in sent_map.values():
        await admin_service.delete_admin_messages(message.bot, message.chat.id, msg_ids)

    # 2. Сбрасываем состояние
    await state.clear()

    # 3. Возвращаем главную админ-клавиатуру
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "✅ Сессия выплат завершена.\n"
        "Выберите новый режим работы:",
        reply_markup=get_admin_mode_keyboard()
    )
