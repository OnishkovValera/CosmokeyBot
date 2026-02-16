from typing import List

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaDocument, InputMediaPhoto, InputMediaVideo

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    BTN_ADMIN_MAILING,
    BTN_CANCEL,
    get_cancel_keyboard,
    get_mailing_confirm_keyboard,
    get_admin_main_keyboard,
)
from bot.services.admin import mailing_service

mailing_router = Router()
mailing_router.message.filter(IsAdmin())
mailing_router.callback_query.filter(IsAdmin())

# ------------------------------------------------------------
# 1. Вход в раздел рассылки
# ------------------------------------------------------------
@mailing_router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_MAILING
)
async def start_mailing(message: Message, state: FSMContext):
    await state.set_state(AdminStates.mailing_content)
    await message.answer(
        "📢 Отправьте **одно сообщение** или **альбом** (несколько фото/видео), которые будут разосланы всем пользователям.\n"
        "Для отмены нажмите «Отмена».",
        reply_markup=get_cancel_keyboard()
    )

# ------------------------------------------------------------
# 2. Обработка одиночного сообщения (текст или одно медиа)
# ------------------------------------------------------------
@mailing_router.message(
    AdminStates.mailing_content,
    ~F.media_group_id
)
async def receive_single_content(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await state.set_state(AdminStates.choosing_mode)
        await message.delete()
        await message.answer("❌ Рассылка отменена.", reply_markup=get_admin_main_keyboard())
        return

    content = await extract_single_content(message)
    if not content:
        await message.answer("❌ Неподдерживаемый тип сообщения. Отправьте текст, фото, видео, документ, аудио или голосовое.")
        return

    await state.update_data(mailing_content=content)
    await state.set_state(AdminStates.mailing_confirm)

    # Отправляем предпросмотр
    await send_single_preview(message, content, message.bot)
    chat_ids = await mailing_service.get_all_user_chat_ids()
    await message.answer(
        f"👥 Будет отправлено **{len(chat_ids)}** пользователям.\nПодтверждаете рассылку?",
        reply_markup=get_mailing_confirm_keyboard()
    )

# ------------------------------------------------------------
# 3. Обработка альбома (несколько медиа)
# ------------------------------------------------------------
@mailing_router.message(
    AdminStates.mailing_content,
    F.media_group_id
)
async def receive_album(message: Message, state: FSMContext, album: List[Message]):
    if message.text == BTN_CANCEL:
        await state.set_state(AdminStates.choosing_mode)
        await message.delete()
        await message.answer("❌ Рассылка отменена.", reply_markup=get_admin_main_keyboard())
        return

    content = await extract_album_content(album)
    if not content:
        await message.answer("❌ Альбом пуст или содержит неподдерживаемые типы.")
        return

    await state.update_data(mailing_content=content)
    await state.set_state(AdminStates.mailing_confirm)

    # Отправляем предпросмотр альбома
    await send_album_preview(message, content, message.bot)
    chat_ids = await mailing_service.get_all_user_chat_ids()
    await message.answer(
        f"👥 Будет отправлено **{len(chat_ids)}** пользователям.\nПодтверждаете рассылку?",
        reply_markup=get_mailing_confirm_keyboard()
    )

# ------------------------------------------------------------
# Вспомогательные функции извлечения контента
# ------------------------------------------------------------
async def extract_single_content(message: Message) -> dict | None:
    """Извлекает информацию из одиночного сообщения (сериализуемые данные)."""
    if message.photo:
        return {
            'type': 'photo',
            'file_id': message.photo[-1].file_id,
            'caption': message.caption,
        }
    elif message.video:
        return {
            'type': 'video',
            'file_id': message.video.file_id,
            'caption': message.caption,
        }
    elif message.document:
        return {
            'type': 'document',
            'file_id': message.document.file_id,
            'caption': message.caption,
        }
    elif message.audio:
        return {
            'type': 'audio',
            'file_id': message.audio.file_id,
            'caption': message.caption,
        }
    elif message.voice:
        return {
            'type': 'voice',
            'file_id': message.voice.file_id,
            'caption': None,
        }
    elif message.text:
        return {
            'type': 'text',
            'text': message.html_text,
        }
    else:
        return None

async def extract_album_content(album: List[Message]) -> dict | None:
    """Преобразует список сообщений альбома в список словарей (сериализуемых)."""
    if not album:
        return None
    media_list = []
    for msg in album:
        if msg.photo:
            media_list.append({
                'type': 'photo',
                'media': msg.photo[-1].file_id,
                'caption': msg.caption,
            })
        elif msg.video:
            media_list.append({
                'type': 'video',
                'media': msg.video.file_id,
                'caption': msg.caption,
            })
        elif msg.document:
            media_list.append({
                'type': 'document',
                'media': msg.document.file_id,
                'caption': msg.caption,
            })
        else:
            continue
    if not media_list:
        return None
    return {
        'type': 'album',
        'media': media_list,
    }

# ------------------------------------------------------------
# Функции предпросмотра
# ------------------------------------------------------------
async def send_single_preview(original_message: Message, content: dict, bot: Bot):
    """Отправляет копию одиночного сообщения как предпросмотр."""
    chat_id = original_message.chat.id
    if content['type'] == 'text':
        await original_message.answer(
            f"📋 **Предпросмотр текста:**\n\n{content['text']}",
            parse_mode='HTML'
        )
    elif content['type'] == 'photo':
        await bot.send_photo(chat_id, content['file_id'], caption=content.get('caption', ''))
    elif content['type'] == 'video':
        await bot.send_video(chat_id, content['file_id'], caption=content.get('caption', ''))
    elif content['type'] == 'document':
        await bot.send_document(chat_id, content['file_id'], caption=content.get('caption', ''))
    elif content['type'] == 'audio':
        await bot.send_audio(chat_id, content['file_id'], caption=content.get('caption', ''))
    elif content['type'] == 'voice':
        await bot.send_voice(chat_id, content['file_id'])

async def send_album_preview(original_message: Message, content: dict, bot: Bot):
    """Отправляет предпросмотр альбома на основе списка словарей."""
    media_group = []
    for item in content['media']:
        if item['type'] == 'photo':
            media_group.append(InputMediaPhoto(media=item['media'], caption=item.get('caption')))
        elif item['type'] == 'video':
            media_group.append(InputMediaVideo(media=item['media'], caption=item.get('caption')))
        elif item['type'] == 'document':
            media_group.append(InputMediaDocument(media=item['media'], caption=item.get('caption')))
    await bot.send_media_group(original_message.chat.id, media_group)
    await original_message.answer("📸 **Предпросмотр альбома** (показан выше)")

# ------------------------------------------------------------
# 4. Подтверждение рассылки
# ------------------------------------------------------------
@mailing_router.callback_query(AdminStates.mailing_confirm, F.data == "mailing:confirm")
async def confirm_mailing(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer("⏳ Рассылка началась...")
    data = await state.get_data()
    content = data['mailing_content']

    chat_ids = await mailing_service.get_all_user_chat_ids()
    success, failed = await mailing_service.send_mailing_content(bot, chat_ids, content)

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