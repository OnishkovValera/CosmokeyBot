from sqlalchemy import select, func, and_
from bot.db.engine import db
from bot.db.tables import users, assistance_requests, rewards


async def get_users_count() -> int:
    async with db.session_factory() as session:
        result = await session.execute(select(func.count(users.c.id)))
        return result.scalar_one()  # ✅ внутри сессии


async def get_gifts_count() -> int:
    async with db.session_factory() as session:
        result = await session.execute(
            select(func.count(users.c.id))
            .where(users.c.is_got_reward_for_subscription == True)
        )
        return result.scalar_one()


async def get_assistance_stats() -> dict:
    async with db.session_factory() as session:
        # По типам
        type_counts = {}
        for req_type in ['defect', 'complaint', 'feedback']:
            result = await session.execute(
                select(func.count(assistance_requests.c.id))
                .where(assistance_requests.c.request_type == req_type)
            )
            type_counts[req_type] = result.scalar_one()

        # По статусам
        status_counts = {}
        for status in ['new', 'in_progress', 'completed', 'rejected']:
            result = await session.execute(
                select(func.count(assistance_requests.c.id))
                .where(assistance_requests.c.status == status)
            )
            status_counts[status] = result.scalar_one()

        return {
            'by_type': type_counts,
            'by_status': status_counts
        }


async def get_rewards_stats() -> dict:
    async with db.session_factory() as session:
        total = await session.execute(select(func.count(rewards.c.id)))
        total_count = total.scalar_one()  # ✅ внутри сессии

        paid = await session.execute(
            select(func.count(rewards.c.id))
            .where(rewards.c.is_paid == True)
        )
        paid_count = paid.scalar_one()  # ✅ внутри сессии

        return {
            'total': total_count,
            'paid': paid_count,
            'pending': total_count - paid_count
        }