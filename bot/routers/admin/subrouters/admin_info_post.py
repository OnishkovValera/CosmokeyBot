from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_admin_main_keyboard,
    get_cancel_keyboard,
    BTN_ADMIN_SET_INFO_POST,
    BTN_CANCEL,
)
from bot.services.admin import settings_service  # 👈 новый сервис

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

@router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_SET_INFO_POST
)
async def start_set_info_post(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_info_post)
    await message.answer(
        "📦 **Настройка информационного поста**\n\n"
        "Перешлите **любое сообщение** (текст, фото, видео, альбом) из канала, группы или личного чата.\n"
        "Именно это сообщение будет отправляться пользователям по кнопке «Узнать полезную информацию».\n\n"
        "❌ Нажмите «Отмена», чтобы выйти без сохранения.",
        reply_markup=get_cancel_keyboard()
    )

@router.message(
    AdminStates.waiting_info_post,
    F.text == BTN_CANCEL
)
async def cancel_set_info_post(message: Message, state: FSMContext):
    await state.set_state(AdminStates.choosing_mode)
    await message.delete()
    await message.answer(
        "❌ Установка инфо-поста отменена.",
        reply_markup=get_admin_main_keyboard()
    )

@router.message(
    AdminStates.waiting_info_post,
    F.forward_from_chat | F.forward_from | F.forward_sender_name
)
async def receive_forwarded_message(message: Message, state: FSMContext):
    # Определяем исходный чат и ID сообщения
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
        msg_id = message.forward_from_message_id
    elif message.forward_from:
        chat_id = message.forward_from.id
        msg_id = message.forward_from_message_id
    else:
        await message.answer(
            "❌ Не удалось определить источник сообщения. Пожалуйста, перешлите сообщение через кнопку «Переслать»."
        )
        return

    if not chat_id or not msg_id:
        await message.answer("❌ Ошибка: не удалось получить ID чата или сообщения.")
        return

    # Сохраняем в БД
    await settings_service.set_info_post(chat_id, msg_id)

    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "✅ **Информационный пост успешно сохранён!**\n\n"
        f"`chat_id: {chat_id}`\n"
        f"`message_id: {msg_id}`\n\n"
        "Теперь пользователи будут получать это сообщение по кнопке «Узнать полезную информацию».",
        reply_markup=get_admin_main_keyboard()
    )

@router.message(AdminStates.waiting_info_post)
async def receive_any_message(message: Message, state: FSMContext):
    await message.answer(
        "⚠️ Пожалуйста, **перешлите** сообщение, используя кнопку «Переслать» в Telegram.\n"
        "Просто отправить текст или файл недостаточно – бот должен видеть исходные `chat_id` и `message_id`."
    )