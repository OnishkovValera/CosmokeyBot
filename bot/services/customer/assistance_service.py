from typing import List
from sqlalchemy import insert, select
from bot.db.engine import db
from bot.db.tables import users, assistance_requests, media_messages
from aiogram.types import Message


async def get_user_db_id(telegram_id: int) -> int | None:
    async with db.session_factory() as session:
        result = await session.execute(
            select(users.c.id).where(users.c.telegram_id == telegram_id)
        )
        row = result.first()
        return row[0] if row else None


async def create_assistance_request(telegram_id: int, request_type: str) -> int:
    user_db_id = await get_user_db_id(telegram_id)
    if not user_db_id:
        raise ValueError(f"User with telegram_id {telegram_id} not found in database")

    async with db.session_factory() as session:
        async with session.begin():
            stmt = (
                insert(assistance_requests)
                .values(
                    user_id=user_db_id,
                    request_type=request_type,
                    is_processed=False,
                    processed_at=None
                )
                .returning(assistance_requests.c.id)
            )
            result = await session.execute(stmt)
            request_id = result.scalar_one()
    return request_id


async def save_media_messages(assistance_request_id: int, messages: List[Message]):
    values_list = [
        {
            "assistance_request_id": assistance_request_id,
            "reward_id": None,
            "chat_id": msg.chat.id,
            "message_id": msg.message_id,
            "media_group_id": msg.media_group_id
        }
        for msg in messages
    ]
    if not values_list:
        return

    async with db.session_factory() as session:
        async with session.begin():
            await session.execute(insert(media_messages), values_list)