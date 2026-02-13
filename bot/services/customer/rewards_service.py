from typing import List
from sqlalchemy import insert, select, update
from aiogram.types import Message

from bot.db.engine import db
from bot.db.tables import users, rewards, media_messages
from bot.utils.media_helper import extract_media_info  # опишем ниже


async def get_user_db_id(telegram_id: int) -> int | None:
    async with db.session_factory() as session:
        result = await session.execute(
            select(users.c.id).where(users.c.telegram_id == telegram_id)
        )
        row = result.first()
        return row[0] if row else None


async def create_reward(telegram_id: int) -> int:
    user_db_id = await get_user_db_id(telegram_id)
    if not user_db_id:
        raise ValueError(f"User with telegram_id {telegram_id} not found")

    async with db.session_factory() as session:
        async with session.begin():
            stmt = (
                insert(rewards)
                .values(
                    user_id=user_db_id,
                    link=None  # временно NULL
                )
                .returning(rewards.c.id)
            )
            result = await session.execute(stmt)
            reward_id = result.scalar_one()
    return reward_id


async def update_reward_link(reward_id: int, link: str):
    async with db.session_factory() as session:
        async with session.begin():
            await session.execute(
                update(rewards)
                .where(rewards.c.id == reward_id)
                .values(link=link)
            )


async def save_reward_media(reward_id: int, messages: List[Message]):
    values_list = []
    for msg in messages:
        media_info = extract_media_info(msg)
        values_list.append({
            "reward_id": reward_id,
            "assistance_request_id": None,
            **media_info
        })

    if not values_list:
        return

    async with db.session_factory() as session:
        async with session.begin():
            await session.execute(insert(media_messages), values_list)