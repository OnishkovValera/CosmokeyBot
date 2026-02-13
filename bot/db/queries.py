from sqlalchemy.dialects.postgresql import insert as pg_insert
from bot.db.engine import db
from bot.db.tables import users


async def create_user(
        telegram_id: int,
        username: str | None,
        chat_id: int,
        phone_number: str | None = None
):
    username = username or "no_username"

    async with db.session_factory() as session:
        async with session.begin():
            stmt = pg_insert(users).values(
                telegram_id=telegram_id,
                username=username,
                chat_id=chat_id,
                phone_number=phone_number
            ).on_conflict_do_update(
                index_elements=['telegram_id'],
                set_={
                    'username': username,
                    'chat_id': chat_id,
                    'phone_number': phone_number  # обновляем, если передан
                }
            )
            await session.execute(stmt)
