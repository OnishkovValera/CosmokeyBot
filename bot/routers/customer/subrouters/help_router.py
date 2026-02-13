from typing import List

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.config import settings
from bot.db.messages_text import messages_text
from bot.fsm.states.customer import FeedbackStates
from bot.keyboards.customer.help_kb import get_help_starter_keyboard
from bot.keyboards.customer.main_menu_kb import main_menu
from bot.services.customer.assistance_service import create_assistance_request, save_media_messages
from bot.utils.helpers import button_messages

help_router = Router()


@help_router.message(F.text == button_messages["support"])
async def start_support_message(message: Message, state: FSMContext):
    await state.set_state(FeedbackStates.CHOOSING_CATEGORY)
    await message.answer(
        messages_text["feedback_welcome_message"],
        reply_markup=get_help_starter_keyboard()
    )


@help_router.message(FeedbackStates.CHOOSING_CATEGORY, F.text.in_(button_messages["help"].values()))
async def set_category(message: Message, state: FSMContext):
    global request_type, answer
    if message.text == button_messages["help"]["defect"]:
        request_type = "defect"
        answer = messages_text["assistance_request_received"]
    elif message.text == button_messages["help"]["complaint"]:
        request_type = "complaint"
        answer = messages_text["complaint_received"]
    elif message.text == button_messages["help"]["feedback"]:
        request_type = "feedback"
        answer = messages_text["feedback_request"]
    elif message.text == button_messages["help"]["back"]:
        await message.answer(
            messages_text["welcome_message"],
            reply_markup=main_menu()
        )
        await state.clear()
        return
    try:
        request_id = await create_assistance_request(
            telegram_id=message.from_user.id,
            request_type=request_type
        )
    except Exception as e:
        logger.error(f"Failed to create assistance request for {message.from_user.id}: {e}")
        await message.answer("❌ Ошибка при создании обращения. Попробуйте позже.")
        await state.clear()
        return

        # Сохраняем ID заявки в состояние и переходим к ожиданию медиа
    await state.update_data(
        assistance_request_id=request_id,
        request_type=request_type
    )
    await state.set_state(FeedbackStates.WAITING_FOR_MEDIA)
    await message.answer(answer)


@help_router.message(FeedbackStates.WAITING_FOR_MEDIA, ~F.media_group_id)
async def handle_single_message(message: Message, state: FSMContext, bot: Bot):
    logger.info(f"MESSSSSSSSSSSSAGE{message} 1")
    data = await state.get_data()
    request_id = data.get("assistance_request_id")
    if not request_id:
        await message.answer("❌ Заявка не найдена. Пожалуйста, начните заново.")
        await state.clear()
        return

    await save_media_messages(request_id, [message])

    try:
        await bot.forward_message(
            chat_id=settings.ADMIN_ACCOUNT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.error(f"Failed to forward message to admin: {e}")

    await message.answer(
        messages_text["feedback_received"],
        reply_markup=main_menu()
    )
    await state.clear()

@help_router.message(FeedbackStates.WAITING_FOR_MEDIA, F.media_group_id)
async def handle_album(message: Message, state: FSMContext, album: List[Message], bot: Bot):
    logger.info(f"MESSSSSSSSSSSSAGE{message} 2")
    data = await state.get_data()
    request_id = data.get("assistance_request_id")
    if not request_id:
        await message.answer("❌ Заявка не найдена. Пожалуйста, начните заново.")
        await state.clear()
        return

    await save_media_messages(request_id, album)

    try:
        await bot.forward_messages(
            chat_id=settings.ADMIN_ACCOUNT_ID,
            from_chat_id=message.chat.id,
            message_ids=[msg.message_id for msg in album]
        )
    except Exception as e:
        logger.error(f"Failed to forward album to admin: {e}")

    await message.answer(
        messages_text["feedback_received"],
        reply_markup=main_menu()
    )
    await state.clear()