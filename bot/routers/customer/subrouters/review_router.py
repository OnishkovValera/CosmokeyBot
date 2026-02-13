from typing import List
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from loguru import logger

from bot.config import settings
from bot.db.messages_text import messages_text
from bot.fsm.states.customer import ReviewStates
from bot.keyboards.customer.main_menu_kb import main_menu
from bot.keyboards.customer.review_kb import get_review_kb
from bot.utils.helpers import button_messages
from bot.services.customer.rewards_service import (
    create_reward,
    save_reward_media,
    update_reward_link
)

review_router = Router()

@review_router.message(F.text == button_messages["review"])
async def start_review(message: Message, state: FSMContext):
    await state.set_state(ReviewStates.WAITING_FOR_READY)
    hide_msg = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await hide_msg.delete()
    await message.answer(
        messages_text["reward_request"],
        reply_markup=get_review_kb()
    )

@review_router.callback_query(ReviewStates.WAITING_FOR_READY, F.data == "ready_for_review")
async def get_review(callback: CallbackQuery, state: FSMContext):
    try:
        reward_id = await create_reward(callback.from_user.id)
    except Exception as e:
        logger.error(f"Failed to create reward for {callback.from_user.id}: {e}")
        await callback.message.answer("❌ Ошибка, попробуйте позже.")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(reward_id=reward_id)
    await state.set_state(ReviewStates.WAITING_FOR_PHOTO)
    await callback.message.answer(messages_text["get_photo_for_reward"])
    await callback.answer()

@review_router.message(ReviewStates.WAITING_FOR_PHOTO, ~F.media_group_id)
async def handle_single_media(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    reward_id = data.get("reward_id")
    if not reward_id:
        await message.answer("❌ Сессия устарела. Начните заново.")
        await state.clear()
        return

    await save_reward_media(reward_id, [message])

    try:
        await bot.forward_message(
            chat_id=settings.ADMIN_ACCOUNT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.error(f"Failed to forward message to admin: {e}")

    await message.answer(messages_text["get_link_for_reward"])
    await state.set_state(ReviewStates.WAITING_FOR_LINK)

@review_router.message(ReviewStates.WAITING_FOR_PHOTO, F.media_group_id)
async def handle_album(message: Message, state: FSMContext, album: List[Message], bot: Bot):
    data = await state.get_data()
    reward_id = data.get("reward_id")
    if not reward_id:
        await message.answer("❌ Сессия устарела. Начните заново.")
        await state.clear()
        return

    await save_reward_media(reward_id, album)

    try:
        await bot.forward_messages(
            chat_id=settings.ADMIN_ACCOUNT_ID,
            from_chat_id=message.chat.id,
            message_ids=[msg.message_id for msg in album]
        )
    except Exception as e:
        logger.error(f"Failed to forward album to admin: {e}")

    await message.answer(messages_text["get_link_for_reward"])
    await state.set_state(ReviewStates.WAITING_FOR_LINK)

@review_router.message(ReviewStates.WAITING_FOR_LINK)
async def handle_review_link(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    reward_id = data.get("reward_id")
    if not reward_id:
        await message.answer("❌ Сессия устарела. Начните заново.")
        await state.clear()
        return

    link = message.text.strip()
    await update_reward_link(reward_id, link)

    try:
        await bot.send_message(
            settings.ADMIN_ACCOUNT_ID,
            f"🔗 Ссылка на отзыв (награда #{reward_id}):\n{link}"
        )
    except Exception as e:
        logger.error(f"Failed to send link to admin: {e}")

    await message.answer(
        messages_text["reward_submission_received"],
        reply_markup=main_menu()
    )
    await state.clear()