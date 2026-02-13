from sqlalchemy import select, update
from bot.db.engine import db
from bot.db.tables import users

async def get_user_reward_status(telegram_id: int) -> bool:
    async with db.session_factory() as session:
        result = await session.execute(
            select(users.c.is_got_reward_for_subscription)
            .where(users.c.telegram_id == telegram_id)
        )
        row = result.first()
        return row[0] if row else False

async def set_user_reward_status(telegram_id: int, value: bool = True):
    async with db.session_factory() as session:
        async with session.begin():
            await session.execute(
                update(users)
                .where(users.c.telegram_id == telegram_id)
                .values(is_got_reward_for_subscription=value)
            )