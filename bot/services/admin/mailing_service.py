# bot/services/admin/mailing_service.py
from typing import List, Tuple
import asyncio
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from sqlalchemy import select
from bot.db.engine import db
from bot.db.tables import users
from loguru import logger

async def get_all_user_chat_ids() -> List[int]:
    async with db.session_factory() as session:
        result = await session.execute(
            select(users.c.chat_id).where(users.c.chat_id != None)
        )
        rows = result.all()
        return [row[0] for row in rows]

async def send_mailing_content(
    bot: Bot,
    chat_ids: List[int],
    content: dict,
    parse_mode: str = "HTML"
) -> Tuple[int, int]:
    """Универсальная отправка контента (словарь из extract_*) всем пользователям."""
    success = 0
    failed = 0
    for chat_id in chat_ids:
        try:
            await _send_to_user(bot, chat_id, content, parse_mode)
            success += 1
        except Exception as e:
            logger.warning(f"Ошибка отправки пользователю {chat_id}: {e}")
            failed += 1
        await asyncio.sleep(0.035)  # ограничение 30 сообщений/сек
    return success, failed

async def _send_to_user(bot: Bot, chat_id: int, content: dict, parse_mode: str):
    ctype = content['type']
    if ctype == 'text':
        await bot.send_message(chat_id, content['text'], parse_mode=parse_mode)
    elif ctype in ('photo', 'video', 'document', 'audio', 'voice'):
        await _send_media(bot, chat_id, content)
    elif ctype == 'album':
        media_group = []
        for item in content['media']:
            if item['type'] == 'photo':
                media_group.append(InputMediaPhoto(media=item['media'], caption=item.get('caption')))
            elif item['type'] == 'video':
                media_group.append(InputMediaVideo(media=item['media'], caption=item.get('caption')))
            elif item['type'] == 'document':
                media_group.append(InputMediaDocument(media=item['media'], caption=item.get('caption')))
        await bot.send_media_group(chat_id, media_group)
    else:
        raise ValueError(f"Неизвестный тип контента: {ctype}")

async def _send_media(bot: Bot, chat_id: int, content: dict):
    caption = content.get('caption', '')
    file_id = content['file_id']
    if content['type'] == 'photo':
        await bot.send_photo(chat_id, file_id, caption=caption)
    elif content['type'] == 'video':
        await bot.send_video(chat_id, file_id, caption=caption)
    elif content['type'] == 'document':
        await bot.send_document(chat_id, file_id, caption=caption)
    elif content['type'] == 'audio':
        await bot.send_audio(chat_id, file_id, caption=caption)
    elif content['type'] == 'voice':
        await bot.send_voice(chat_id, file_id)