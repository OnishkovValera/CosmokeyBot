from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger
from sqlalchemy.sql.expression import update

from bot.db.engine import db
from bot.db.queries import create_user
from bot.db.tables import users
from bot.keyboards.customer.main_menu_kb import get_phone_keyboard
from bot.services.customer import start_service

start_router = Router()



@start_router.message(Command("start"))
async def start_message(message: Message, state: FSMContext):
    user = message.from_user
    await create_user(
        telegram_id=user.id,
        username=user.username,
        chat_id=message.chat.id,
        phone_number=None
    )

    if not user.username:
        await message.answer(
            "📞 У вас не указан username в Telegram.\n"
            "Поделитесь номером телефона, чтобы мы могли связаться с вами быстрее.",
            reply_markup=get_phone_keyboard()
        )
        await state.set_state("waiting_contact")
    else:
        await start_service.welcome_message(message, state)


@start_router.message(F.contact, StateFilter("waiting_contact"))
async def receive_contact(message: Message, state: FSMContext):
    contact = message.contact
    phone = contact.phone_number
    user_id = message.from_user.id

    async with db.session_factory() as session:
        async with session.begin():
            stmt = (
                update(users)
                .where(users.c.telegram_id == user_id)
                .values(phone_number=phone)
            )
            await session.execute(stmt)

    await message.answer("✅ Спасибо! Номер сохранён.", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    await start_service.welcome_message(message, state)  # приветствие