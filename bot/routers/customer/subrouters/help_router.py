from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from typing import List, Optional

from bot.db.engine import db
from bot.db.tables import assistance_requests, media_messages, users
from bot.db.messages_text import messages_text
from bot.fsm.states.customer import FeedbackStates
from bot.keyboards.customer.help_kb import get_help_starter_keyboard
from bot.keyboards.customer.main_menu_kb import main_menu
from bot.utils.helpers import button_messages
from sqlalchemy import insert, select

assistance_router = Router()


@assistance_router.message(F.text == button_messages["support"])
async def start_support_message(message: Message, state: FSMContext):
    await state.set_state(FeedbackStates.CHOOSING_CATEGORY)
    await message.answer(
        messages_text["feedback_welcome_message"],
        reply_markup=get_help_starter_keyboard()
    )


@assistance_router.message(
    FeedbackStates.CHOOSING_CATEGORY,
    F.text.in_(button_messages["help"].values())
)
async def set_category(message: Message, state: FSMContext):
    # Определяем тип обращения
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
        await message.answer(messages_text["welcome_message"], reply_markup=main_menu())
        await state.clear()
        return
    else:
        return

    # Получаем внутренний ID пользователя
    async with db.session_factory() as session:
        user_res = await session.execute(
            select(users.c.id).where(users.c.telegram_id == message.from_user.id)
        )
        user_db_id = user_res.scalar_one_or_none()
        if not user_db_id:
            await message.answer("❌ Ошибка: пользователь не найден. Напишите /start")
            await state.clear()
            return

        # Создаём заявку (текст будет заполнен позже)
        result = await session.execute(
            insert(assistance_requests)
            .values(
                user_id=user_db_id,
                request_type=request_type,
                text=None
            )
            .returning(assistance_requests.c.id)
        )
        request_id = result.scalar_one()
        await session.commit()

    await state.update_data(assistance_request_id=request_id, request_type=request_type)
    await state.set_state(FeedbackStates.WAITING_FOR_MEDIA)
    await message.answer(answer)


# Обработка текстовых сообщений (без медиа)
@assistance_router.message(FeedbackStates.WAITING_FOR_MEDIA, F.text, ~F.media_group_id)
async def handle_text_message(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_id = data.get("assistance_request_id")
    if not request_id:
        await message.answer("❌ Ошибка сессии. Начните заново.")
        await state.clear()
        return

    # Сохраняем текст в заявку
    async with db.session_factory() as session:
        await session.execute(
            assistance_requests.update()
            .where(assistance_requests.c.id == request_id)
            .values(text=message.text)
        )
        await session.commit()

    await message.answer(messages_text["feedback_received"], reply_markup=main_menu())
    await state.clear()


# Обработка сообщений с одним медиа (фото, видео, документ)
@assistance_router.message(FeedbackStates.WAITING_FOR_MEDIA, F.photo | F.document | F.video | F.audio | F.voice,
                           ~F.media_group_id)
async def handle_single_media(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_id = data.get("assistance_request_id")
    if not request_id:
        await message.answer("❌ Ошибка сессии. Начните заново.")
        await state.clear()
        return

    # Сохраняем подпись в текст заявки (если есть)
    async with db.session_factory() as session:
        # Если есть caption, сохраняем его как текст заявки
        if message.caption:
            await session.execute(
                assistance_requests.update()
                .where(assistance_requests.c.id == request_id)
                .values(text=message.caption)
            )

        # Сохраняем медиа в media_messages
        await session.execute(
            insert(media_messages).values(
                assistance_request_id=request_id,
                chat_id=message.chat.id,
                message_id=message.message_id,
                media_group_id=None
            )
        )
        await session.commit()

    await message.answer(messages_text["feedback_received"], reply_markup=main_menu())
    await state.clear()


# Обработка альбома (несколько медиа)
@assistance_router.message(FeedbackStates.WAITING_FOR_MEDIA, F.media_group_id)
async def handle_album(message: Message, state: FSMContext, bot: Bot, album: List[Message]):
    data = await state.get_data()
    request_id = data.get("assistance_request_id")
    if not request_id:
        await message.answer("❌ Ошибка сессии. Начните заново.")
        await state.clear()
        return

    async with db.session_factory() as session:
        # Сохраняем подпись первого сообщения как текст заявки
        if album[0].caption:
            await session.execute(
                assistance_requests.update()
                .where(assistance_requests.c.id == request_id)
                .values(text=album[0].caption)
            )

        # Сохраняем все медиа альбома
        for msg in album:
            await session.execute(
                insert(media_messages).values(
                    assistance_request_id=request_id,
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    media_group_id=msg.media_group_id
                )
            )
        await session.commit()

    await message.answer(messages_text["feedback_received"], reply_markup=main_menu())
    await state.clear()