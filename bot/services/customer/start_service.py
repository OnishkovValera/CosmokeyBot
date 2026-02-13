from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.db.messages_text import messages_text
from bot.keyboards.customer.main_menu_kb import main_menu


async def welcome_message(message: Message, state: FSMContext):
    await message.answer(messages_text["welcome_message"], reply_markup=main_menu())


