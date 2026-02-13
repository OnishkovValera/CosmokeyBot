from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.fsm.states.admin import SpecialPostState
from bot.keyboards.admin.special_post_kb import back_button_for_post

special_post_router = Router()

@special_post_router.message(Command("set_post"))
async def set_special_post(message: Message, state: FSMContext):
    await state.set_state(SpecialPostState.WAITING_FOR_POST)
    await message.answer(f"Перешлите сюда пост из канала", reply_markup=back_button_for_post())

@special_post_router.message(SpecialPostState.WAITING_FOR_POST)
async def get_new_post(message: Message, state: FSMContext):
    await message.answer(f"Пост с id: {message.forward_from_message_id} и chatId: {message.forward_from_chat.id} установлен")
    await state.clear()

@special_post_router.callback_query(SpecialPostState.WAITING_FOR_POST, F.data == "special_post_cancel")
async def cancel_set_new_post(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()