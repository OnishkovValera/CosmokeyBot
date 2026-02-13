from aiogram import Router, F, Bot
from aiogram.types import Message
from loguru import logger

from bot.utils.helpers import button_messages
from bot.services.admin import settings_service

info_router = Router()

@info_router.message(F.text == button_messages["info"])
async def send_info_post(message: Message, bot: Bot):
    chat_id, message_id = await settings_service.get_info_post()

    if chat_id == 0 or message_id == 0:
        await message.answer("📚 Информационный пост ещё не настроен. Попробуйте позже.")
        return

    try:
        await bot.forward_message(
            chat_id=message.chat.id,
            from_chat_id=chat_id,
            message_id=message_id
        )
    except Exception as e:
        await message.answer("❌ Не удалось загрузить пост. Возможно, он был удалён или бот не имеет доступа.")
        logger.error(f"Info post error: {e}")