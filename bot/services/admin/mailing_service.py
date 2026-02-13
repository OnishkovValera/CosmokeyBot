from typing import List, Tuple
import asyncio
from aiogram import Bot
from sqlalchemy import select

from bot.db.engine import db
from bot.db.tables import users

async def get_all_user_chat_ids() -> List[int]:
    async with db.session_factory() as session:
        result = await session.execute(
            select(users.c.chat_id).where(users.c.chat_id != None)
        )
        rows = result.all()
        return [row[0] for row in rows]

async def send_mailing(
    bot: Bot,
    chat_ids: List[int],
    text: str,
    parse_mode: str = "HTML"
) -> Tuple[int, int]:
    success = 0
    failed = 0
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text, parse_mode=parse_mode)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.035)
    return success, failed