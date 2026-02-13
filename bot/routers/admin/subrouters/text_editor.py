import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from loguru import logger

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_admin_mode_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
    BTN_BACK,
    BTN_CANCEL,
)
from bot.services.admin import message_service  # <-- ИСПРАВЛЕНО

texts_editor_router = Router()
texts_editor_router.message.filter(IsAdmin())
texts_editor_router.callback_query.filter(IsAdmin())

@texts_editor_router.message(
    AdminStates.choosing_mode,
    F.text == "✏️ Поменять текст сообщений"
)
async def start_edit_texts(message: Message, state: FSMContext):
    await state.set_state(AdminStates.editing_texts_list)
    await show_texts_list(message, state, message.bot)

async def show_texts_list(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    old_ids = data.get("list_message_ids", [])
    for msg_id in old_ids:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass

    all_msgs = await message_service.get_all_messages()  # <-- ИСПРАВЛЕНО
    if not all_msgs:
        await message.answer(
            "❌ В базе нет ни одного сообщения.",
            reply_markup=get_admin_mode_keyboard()
        )
        await state.set_state(AdminStates.choosing_mode)
        return

    instr = await message.answer(
        "📋 Список текущих сообщений:\n"
        "Нажмите «✏️ Изменить» под нужным сообщением, чтобы заменить текст.",
        reply_markup=get_back_keyboard()
    )
    list_msg_ids = [instr.message_id]

    for msg in all_msgs:
        key = msg["message_key"]
        text = msg["text"]
        display_text = text[:300] + "..." if len(text) > 300 else text
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit:{key}")]
            ]
        )
        sent = await message.answer(display_text, reply_markup=kb)
        list_msg_ids.append(sent.message_id)

    await state.update_data(
        list_message_ids=list_msg_ids,
        messages_data={msg["message_key"]: msg["text"] for msg in all_msgs}
    )

@texts_editor_router.message(
    AdminStates.editing_texts_list,
    F.text == BTN_BACK
)
async def back_from_list(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    for msg_id in data.get("list_message_ids", []):
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_mode_keyboard()
    )

@texts_editor_router.callback_query(
    StateFilter(AdminStates.editing_texts_list),
    F.data.startswith("edit:")
)
async def process_edit_callback(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    await state.update_data(
        editing_key=key,
        editing_message_id=callback.message.message_id
    )
    await state.set_state(AdminStates.waiting_new_text)

    await callback.message.answer(
        f"✏️ Введите **новый текст** для этого сообщения.\n"
        f"Текущий текст (первые 100 символов):\n{callback.message.text[:100]}...",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@texts_editor_router.message(
    AdminStates.waiting_new_text,
    F.text == BTN_CANCEL
)
async def cancel_edit(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    await state.set_state(AdminStates.editing_texts_list)
    confirm = await message.answer("❌ Редактирование отменено.")
    await asyncio.sleep(2)
    await confirm.delete()
    await message.answer(
        "📋 Выберите сообщение для редактирования или нажмите «Назад».",
        reply_markup=get_back_keyboard()
    )

@texts_editor_router.message(AdminStates.waiting_new_text)
async def receive_new_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    key = data.get("editing_key")
    old_msg_id = data.get("editing_message_id")
    new_text = message.text

    if not new_text:
        await message.answer("❌ Текст не может быть пустым. Попробуйте снова.")
        return

    success = await message_service.update_message_text(key, new_text)  # <-- ИСПРАВЛЕНО
    if not success:
        await message.answer("❌ Ошибка обновления. Попробуйте позже.")
        return

    await message.delete()
    try:
        display_text = new_text[:300] + "..." if len(new_text) > 300 else new_text
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=old_msg_id,
            text=display_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit:{key}")]
                ]
            )
        )
    except Exception as e:
        logger.error(f"Не удалось отредактировать сообщение: {e}")

    confirm = await message.answer(f"✅ Текст для ключа `{key}` обновлён!")
    await asyncio.sleep(2)
    await confirm.delete()

    await state.set_state(AdminStates.editing_texts_list)
    await message.answer(
        "📋 Вы можете выбрать другое сообщение для редактирования или нажать «Назад» для выхода.",
        reply_markup=get_back_keyboard()
    )

@texts_editor_router.message(Command("cancel"), StateFilter(AdminStates.waiting_new_text))
async def command_cancel(message: Message, state: FSMContext, bot: Bot):
    await state.set_state(AdminStates.editing_texts_list)
    await message.delete()
    confirm = await message.answer("❌ Редактирование отменено.", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(2)
    await confirm.delete()
    await show_texts_list(message, state, bot)