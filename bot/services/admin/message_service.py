from typing import List, Dict
from sqlalchemy import select, update
from bot.db.engine import db
from bot.db.tables import messages_texts
from bot.db.messages_text import messages_text

async def get_all_messages() -> List[Dict[str, str]]:
    """Возвращает все записи из messages_texts (ключ + текст)."""
    async with db.session_factory() as session:
        result = await session.execute(
            select(messages_texts.c.message_key, messages_texts.c.text)
            .order_by(messages_texts.c.message_key)
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]

async def update_message_text(key: str, new_text: str) -> bool:
    """Обновляет текст сообщения в БД и в кэше."""
    async with db.session_factory() as session:
        async with session.begin():
            result = await session.execute(
                update(messages_texts)
                .where(messages_texts.c.message_key == key)
                .values(text=new_text)
            )
            if result.rowcount == 0:
                return False
    # Обновляем кэш в памяти
    messages_text.update_message(key, new_text)
    return True