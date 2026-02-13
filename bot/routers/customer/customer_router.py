from aiogram import Router

from bot.filters.is_customer import IsCustomer
from bot.routers.customer.subrouters.gift_router import gift_router
from bot.routers.customer.subrouters.help_router import assistance_router
from bot.routers.customer.subrouters.info_router import info_router
from bot.routers.customer.subrouters.review_router import review_router
from bot.routers.customer.subrouters.start_router import start_router

customer_router = Router()
customer_router.message.filter(IsCustomer())
customer_router.callback_query.filter(IsCustomer())
customer_router.include_routers(start_router, gift_router, review_router, info_router, assistance_router)