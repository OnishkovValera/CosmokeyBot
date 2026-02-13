from aiogram import Bot

from bot.config import settings


async def check_subscription(bot: Bot, user_id):
    member = await bot.get_chat_member(settings.ADMIN_GROUP_ID, user_id)
    return member.status in ["member", "administrator", "creator"]
