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
    BTN_ADMIN_EDIT_TEXTS,
    BTN_ADMIN_BACK,
    BTN_ADMIN_CANCEL,
    get_admin_back_keyboard,
    get_admin_cancel_keyboard
)
from bot.services.admin import admin_service

texts_editor_router = Router()


# ------------------------------------------------------------
# 1. Вход в режим редактирования – из главного меню админа
# ------------------------------------------------------------
@texts_editor_router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_EDIT_TEXTS
)
async def start_edit_texts(message: Message, state: FSMContext):
    await state.set_state(AdminStates.editing_texts_list)
    await show_texts_list(message, state, message.bot)


async def show_texts_list(message: Message, state: FSMContext, bot: Bot):
    """Показывает все тексты с inline-кнопками «Изменить»."""
    # 1. Удаляем предыдущее сообщение-приглашение, если было (необязательно)
    data = await state.get_data()
    if "list_message_ids" in data:
        for msg_id in data["list_message_ids"]:
            try:
                await bot.delete_message(message.chat.id, msg_id)
            except:
                pass

    all_msgs = await admin_service.get_all_messages()
    if not all_msgs:
        await message.answer(
            "❌ В базе нет ни одного сообщения.",
            reply_markup=get_admin_mode_keyboard()
        )
        await state.set_state(AdminStates.choosing_mode)
        return

    # 2. Отправляем инструкцию с reply-кнопкой «Назад»
    instr = await message.answer(
        "📋 Список текущих сообщений:\n"
        "Нажмите «✏️ Изменить» под нужным сообщением, чтобы заменить текст.",
        reply_markup=get_admin_back_keyboard()
    )
    list_msg_ids = [instr.message_id]

    # 3. Для каждого текста отправляем отдельное сообщение с кнопкой
    for msg in all_msgs:
        key = msg["message_key"]
        text = msg["text"]
        # Обрезаем слишком длинные сообщения для предпросмотра
        display_text = text[:300] + "..." if len(text) > 300 else text
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit:{key}")]
            ]
        )
        sent = await message.answer(display_text, reply_markup=kb)
        list_msg_ids.append(sent.message_id)

    # 4. Сохраняем ID всех отправленных сообщений в state
    await state.update_data(
        list_message_ids=list_msg_ids,
        messages_data={msg["message_key"]: msg["text"] for msg in all_msgs}
    )


# ------------------------------------------------------------
# 2. Нажатие «Назад» – удаляем список, возвращаемся в главное меню
# ------------------------------------------------------------
@texts_editor_router.message(
    AdminStates.editing_texts_list,
    F.text == BTN_ADMIN_BACK
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
        "🛠 Панель администратора\nВыберите режим работы:",
        reply_markup=get_admin_mode_keyboard()
    )


# ------------------------------------------------------------
# 3. Нажатие «Изменить» – запрашиваем новый текст
# ------------------------------------------------------------
@texts_editor_router.callback_query(
    StateFilter(AdminStates.editing_texts_list),
    F.data.startswith("edit:")
)
async def process_edit_callback(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    # Сохраняем, какой ключ редактируем, и ID сообщения, которое нужно будет обновить
    await state.update_data(
        editing_key=key,
        editing_message_id=callback.message.message_id
    )
    await state.set_state(AdminStates.waiting_new_text)

    # Отправляем сообщение с запросом и reply-кнопкой «Отмена»
    await callback.message.answer(
        f"✏️ Введите **новый текст** для этого сообщения.\n"
        f"Текущий текст (первые 100 символов):\n{callback.message.text[:100]}...",
        reply_markup=get_admin_cancel_keyboard()
    )
    await callback.answer()


# ------------------------------------------------------------
# 4. Нажатие «Отмена» – удаляем запрос, возвращаемся к списку
# ------------------------------------------------------------
@texts_editor_router.message(
    AdminStates.waiting_new_text,
    F.text == BTN_ADMIN_CANCEL
)
async def cancel_edit(message: Message, state: FSMContext, bot: Bot):
    # 1. Удаляем сообщение с запросом (то, которое отправил админ)
    await message.delete()

    # 2. Возвращаем состояние списка
    await state.set_state(AdminStates.editing_texts_list)

    # 3. Отправляем сообщение с подтверждением отмены (самоудаляющееся)
    confirm = await message.answer("❌ Редактирование отменено.")
    import asyncio
    await asyncio.sleep(2)
    await confirm.delete()

    # 4. Возвращаем reply-клавиатуру «Назад»
    await message.answer(
        "📋 Выберите сообщение для редактирования или нажмите «Назад».",
        reply_markup=get_admin_back_keyboard()
    )
# ------------------------------------------------------------
# 5. Получение нового текста
# ------------------------------------------------------------
@texts_editor_router.message(AdminStates.waiting_new_text)
async def receive_new_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    key = data.get("editing_key")
    old_msg_id = data.get("editing_message_id")
    new_text = message.text

    if not new_text:
        await message.answer("❌ Текст не может быть пустым. Попробуйте снова.")
        return

    # Обновляем БД и кэш
    success = await admin_service.update_message_text(key, new_text)
    if not success:
        await message.answer("❌ Ошибка обновления. Попробуйте позже.")
        return

    # 1. Удаляем сообщение с запросом (то, которое отправил админ)
    await message.delete()

    # 2. Обновляем сообщение со старым текстом – вставляем новый
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

    # 3. Отправляем самоудаляющееся подтверждение
    confirm = await message.answer(f"✅ Текст для ключа `{key}` обновлён!")
    import asyncio
    await asyncio.sleep(2)
    await confirm.delete()

    # 4. Возвращаем состояние списка И отправляем новую инструкцию с кнопкой «Назад»
    await state.set_state(AdminStates.editing_texts_list)

    # Отправляем сообщение, которое вернёт reply-клавиатуру «Назад»
    await message.answer(
        "📋 Вы можете выбрать другое сообщение для редактирования или нажать «Назад» для выхода.",
        reply_markup=get_admin_back_keyboard()
    )

# ------------------------------------------------------------
# 6. Команда /cancel – аварийный выход (на случай, если reply не сработал)
# ------------------------------------------------------------
@texts_editor_router.message(Command("cancel"), StateFilter(AdminStates.waiting_new_text))
async def command_cancel(message: Message, state: FSMContext, bot: Bot):
    await state.set_state(AdminStates.editing_texts_list)
    await message.delete()
    confirm = await message.answer("❌ Редактирование отменено.", reply_markup=ReplyKeyboardRemove())
    import asyncio
    await asyncio.sleep(2)
    await confirm.delete()
    # Возвращаем список сообщений (заново показываем)
    await show_texts_list(message, state, bot)