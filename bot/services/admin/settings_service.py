from sqlalchemy import select, update
from bot.db.engine import db
from bot.db.tables import settings

async def get_setting(key: str) -> str:
    """Возвращает значение настройки по ключу."""
    async with db.session_factory() as session:
        result = await session.execute(
            select(settings.c.value).where(settings.c.key == key)
        )
        row = result.scalar_one_or_none()
        return row if row is not None else "0"

async def get_info_post() -> tuple[int, int]:
    """Возвращает (chat_id, message_id) инфо-поста."""
    chat_id = int(await get_setting('info_chat_id'))
    message_id = int(await get_setting('info_message_id'))
    return chat_id, message_id

async def set_info_post(chat_id: int, message_id: int):
    """Сохраняет chat_id и message_id инфо-поста."""
    async with db.session_factory() as session:
        async with session.begin():
            for key, value in [
                ('info_chat_id', str(chat_id)),
                ('info_message_id', str(message_id))
            ]:
                await session.execute(
                    update(settings)
                    .where(settings.c.key == key)
                    .values(value=value)
                )