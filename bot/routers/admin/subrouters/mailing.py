from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    BTN_ADMIN_MAILING,
    BTN_CANCEL,
    get_cancel_keyboard,
    get_mailing_confirm_keyboard,
    get_admin_main_keyboard
)
from bot.services.admin import mailing_service

mailing_router = Router()
mailing_router.message.filter(IsAdmin())
mailing_router.callback_query.filter(IsAdmin())


@mailing_router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_MAILING
)
async def start_mailing(message: Message, state: FSMContext):
    await state.set_state(AdminStates.mailing_text)
    await message.answer(
        "📢 Введите текст для рассылки всем пользователям:\n",
        reply_markup=get_cancel_keyboard()
    )


@mailing_router.message(AdminStates.mailing_text)
async def receive_mailing_text(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await state.set_state(AdminStates.choosing_mode)
        await message.delete()
        await message.answer(
            "❌ Рассылка отменена.",
            reply_markup=get_admin_main_keyboard()
        )
        return

    text = message.html_text
    await state.update_data(mailing_text=text)
    await state.set_state(AdminStates.mailing_confirm)

    chat_ids = await mailing_service.get_all_user_chat_ids()
    await message.answer(
        f"📋 **Предпросмотр текста:**\n\n{text}\n\n"
        f"👥 Будет отправлено **{len(chat_ids)}** пользователям.\n"
        f"Подтверждаете рассылку?",
        reply_markup=get_mailing_confirm_keyboard()
    )


@mailing_router.callback_query(AdminStates.mailing_confirm, F.data == "mailing:confirm")
async def confirm_mailing(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer("⏳ Рассылка началась...")
    data = await state.get_data()
    text = data['mailing_text']

    chat_ids = await mailing_service.get_all_user_chat_ids()
    success, failed = await mailing_service.send_mailing(bot, chat_ids, text)

    await callback.message.edit_text(
        f"✅ Рассылка завершена!\n"
        f"📨 Успешно: {success}\n"
        f"❌ Ошибок: {failed}"
    )
    await state.set_state(AdminStates.choosing_mode)
    await callback.message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_main_keyboard()
    )


@mailing_router.callback_query(AdminStates.mailing_confirm, F.data == "mailing:cancel")
async def cancel_mailing(callback: CallbackQuery, state: FSMContext):
    await callback.answer("❌ Отменено")
    await state.set_state(AdminStates.choosing_mode)
    await callback.message.edit_text("Рассылка отменена.")
    await callback.message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_main_keyboard()
    )