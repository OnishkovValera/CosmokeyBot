import asyncio

from aiogram import Bot, Dispatcher
from loguru import logger
from bot.config import settings
from bot.db.messages_text import messages_text
from bot.fsm.storage import storage
from bot.middlewares.album import AlbumMiddleware
from bot.routers.admin.admin_router import admin_router
from bot.routers.customer.customer_router import customer_router


async def on_startup():
    logger.log("INFO", "Starting bot...")
    await messages_text.load_messages_texts()


async def main():
    await on_startup()
    bot = Bot(settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    dp.message.middleware(AlbumMiddleware())
    dp.include_routers(customer_router, admin_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())