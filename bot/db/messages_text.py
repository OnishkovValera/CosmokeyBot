from sqlalchemy import text

from bot.db.engine import Database, db


class MessageText:
    def __init__(self, database: Database):
        self._db = database
        self._messages_texts = {}

    def __getitem__(self, message_key: str) -> str:
        return self._messages_texts[message_key]

    def update_message(self, key: str, new_text: str):
        self._messages_texts[key] = new_text

    async def load_messages_texts(self):
        self._messages_texts = await get_messages_text(self._db)

async def get_messages_text(database: Database) -> dict[str, str]:
    async with database.session_factory() as session:
        async with session.begin():
            result = await session.execute(text("""SELECT * FROM messages_texts"""))
            messages_texts = {}
            for row in result.mappings():
                messages_texts[row["message_key"]] = row["text"]
            return messages_texts


messages_text = MessageText(db)
