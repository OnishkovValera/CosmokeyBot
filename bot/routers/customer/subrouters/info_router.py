from aiogram import Router, F, Bot
from aiogram.types import Message

from bot.utils.helpers import button_messages

info_router = Router()

@info_router.message(F.text == button_messages["info"])
async def get_info(message: Message, bot: Bot):
    await bot.forward_message(
        chat_id=message.chat.id,
        from_chat_id=-1003637901510,
        message_id=2
    )