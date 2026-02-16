from sqlalchemy import select, func, and_
from bot.db.engine import db
from bot.db.tables import users, assistance_requests, rewards


async def get_users_count() -> int:
    """Общее количество пользователей."""
    async with db.session_factory() as session:
        result = await session.execute(select(func.count(users.c.id)))
        return result.scalar_one()


async def get_subscribed_users_count() -> int:
    """Количество пользователей, подписанных на канал."""
    async with db.session_factory() as session:
        result = await session.execute(
            select(func.count(users.c.id)).where(users.c.is_subscribed == True)
        )
        return result.scalar_one()


async def get_gifts_count() -> int:
    """Количество пользователей, получивших подарок за подписку."""
    async with db.session_factory() as session:
        result = await session.execute(
            select(func.count(users.c.id))
            .where(users.c.is_got_reward_for_subscription == True)
        )
        return result.scalar_one()


async def get_assistance_stats() -> dict:
    """Статистика по обращениям (defect, complaint, feedback)."""
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
    """Статистика по выплатам за отзывы."""
    async with db.session_factory() as session:
        total = await session.execute(select(func.count(rewards.c.id)))
        total_count = total.scalar_one()

        paid = await session.execute(
            select(func.count(rewards.c.id)).where(rewards.c.is_paid == True)
        )
        paid_count = paid.scalar_one()

        # По статусам
        status_counts = {}
        for status in ['new', 'in_progress', 'completed', 'rejected']:
            result = await session.execute(
                select(func.count(rewards.c.id)).where(rewards.c.status == status)
            )
            status_counts[status] = result.scalar_one()

        return {
            'total': total_count,
            'paid': paid_count,
            'pending': total_count - paid_count,
            'by_status': status_counts
        }


async def get_total_requests() -> int:
    """Общее количество всех заявок (обращения + выплаты)."""
    async with db.session_factory() as session:
        assist = await session.execute(select(func.count(assistance_requests.c.id)))
        rew = await session.execute(select(func.count(rewards.c.id)))
        return assist.scalar_one() + rew.scalar_one()