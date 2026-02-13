from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from loguru import logger


async def send_media_to_admin(bot: Bot, media: dict, chat_id: int):
    content_type = media.get('content_type')
    file_id = media.get('file_id')
    caption = media.get('caption', '')

    try:
        if content_type == 'photo' and file_id:
            await bot.send_photo(chat_id, file_id, caption=caption)
        elif content_type == 'video' and file_id:
            await bot.send_video(chat_id, file_id, caption=caption)
        elif content_type == 'document' and file_id:
            await bot.send_document(chat_id, file_id, caption=caption)
        elif content_type == 'audio' and file_id:
            await bot.send_audio(chat_id, file_id, caption=caption)
        elif content_type == 'voice' and file_id:
            await bot.send_voice(chat_id, file_id, caption=caption)
        else:
            await bot.send_message(chat_id, f"⚠️ Медиа неизвестного типа: {content_type}")
    except Exception as e:
        logger.error(f"Ошибка отправки медиа админу: {e}")