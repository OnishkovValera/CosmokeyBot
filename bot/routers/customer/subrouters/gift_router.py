from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from loguru import logger

from bot.db.messages_text import messages_text
from bot.keyboards.customer.gift_kb import get_subscribe_for_gift_kb, check_subscription_kb
from bot.keyboards.customer.main_menu_kb import main_menu
from bot.services.customer.gift_service import check_subscription
from bot.services.customer.user_service import get_user_reward_status, set_user_reward_status
from bot.utils.helpers import button_messages, add_back_button
from bot.utils.navigation import pop_state, push_state, GiftSteps, clear_stack, get_current_step

gift_router = Router()


@gift_router.message(F.text == button_messages['get_gift'])
async def gift_callback(message: Message, state: FSMContext):
    already_got = await get_user_reward_status(message.from_user.id)
    if already_got:
        await message.answer("🎁 Вы уже получили подарок за подписку!")
        return

    await state.set_state("gift_flow")
    await state.clear()
    await push_state(state, GiftSteps.GET_GIFT)
    hide_msg = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await hide_msg.delete()
    await message.answer(
        messages_text["subscription_check"],
        reply_markup=add_back_button(get_subscribe_for_gift_kb())
    )


@gift_router.callback_query(F.data == "subscribed")
async def subscribed_callback(callback: CallbackQuery, state: FSMContext):
    await push_state(state, GiftSteps.CHECK_SUBSCRIPTION)
    is_subscribed = await check_subscription(callback.bot, callback.from_user.id)
    if is_subscribed:
        await set_user_reward_status(callback.from_user.id, True)

        await callback.message.edit_text(messages_text["reward_received"])
        await callback.message.answer(
            messages_text["welcome_message"],
            reply_markup=main_menu()
        )
        await clear_stack(state)
    else:
        await callback.message.edit_text(
            messages_text["subscription_check_failed"],
            reply_markup=add_back_button(check_subscription_kb())
        )

@gift_router.callback_query(F.data == "not_subscribed")
async def not_subscribed_callback(callback: CallbackQuery, state: FSMContext):
    await push_state(state, GiftSteps.CHANNEL_LINK)
    await callback.message.edit_text("t.me/your_channel_link", reply_markup=add_back_button(check_subscription_kb()))


@gift_router.callback_query(F.data == "gift_check_subscription")
async def get_gift(callback: CallbackQuery, state: FSMContext):
    current_state = await get_current_step(state)
    if current_state != GiftSteps.NOT_SUBSCRIBED:
        await push_state(state, GiftSteps.NOT_SUBSCRIBED)
    is_subscribed = await check_subscription(callback.bot, callback.from_user.id)
    if is_subscribed:
        await set_user_reward_status(callback.from_user.id, True)
        await callback.message.edit_text(messages_text["reward_received"])
        await callback.message.answer(messages_text["welcome_message"], reply_markup=main_menu())
        await clear_stack(state)
    else:
        await callback.message.edit_text("Проверка...", reply_markup=None)
        await callback.message.edit_text(messages_text["subscription_check_failed"],
                                         reply_markup=add_back_button(check_subscription_kb()))


@gift_router.callback_query(F.data == "back")
async def universal_back(callback: CallbackQuery, state: FSMContext):
    previous_step = await pop_state(state)
    logger.log("INFO", f"User state {previous_step} ")
    logger.log("INFO", f"User {callback.from_user.first_name} pressed back button, previous step is {previous_step}")
    if previous_step is None or previous_step == GiftSteps.GET_GIFT:
        await callback.message.delete()
        await callback.message.answer(
            "Главное меню:",
            reply_markup=main_menu()
        )
        await callback.answer()
        return

    if previous_step == GiftSteps.CHECK_SUBSCRIPTION or previous_step == GiftSteps.CHANNEL_LINK:
        await callback.message.edit_text(
            messages_text["subscription_check"],
            reply_markup=add_back_button(get_subscribe_for_gift_kb())
        )

    if previous_step == GiftSteps.NOT_SUBSCRIBED:
        previous_step = await pop_state(state)
        if previous_step == GiftSteps.CHANNEL_LINK:
            await push_state(state, GiftSteps.CHANNEL_LINK)
            await callback.message.edit_text("t.me/your_channel_link", reply_markup=add_back_button(check_subscription_kb()))
        elif previous_step == GiftSteps.CHECK_SUBSCRIPTION:
            await callback.message.edit_text(messages_text["subscription_check"], reply_markup=add_back_button(get_subscribe_for_gift_kb()))
        else:
            logger.log("WARNING", f"User {callback.from_user.first_name} push back button but previous step is {previous_step}, expected {GiftSteps.CHANNEL_LINK} or {GiftSteps.CHECK_SUBSCRIPTION}")
            logger.log("INFO", f" previous state {previous_step}")
    await callback.answer()
