from typing import List, Optional

from sqlalchemy import select, update, and_, desc, insert

from bot.db.engine import db
from bot.db.tables import (
    assistance_requests, rewards, users,
    media_messages, request_comments
)


# ------------------- ПОЛУЧЕНИЕ СПИСКА ЗАЯВОК -------------------
async def get_requests_by_filters(
        request_type: str,  # 'assistance' или 'reward'
        subtype: Optional[str] = None,  # для assistance: defect/complaint/feedback
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
) -> List[dict]:
    """Возвращает заявки с информацией о пользователе и текстом."""
    async with db.session_factory() as session:
        if request_type == 'assistance':
            table = assistance_requests
            type_filter = assistance_requests.c.request_type == subtype if subtype else True
        else:
            table = rewards
            type_filter = True

        query = (
            select(
                table,
                users.c.username.label('user_username'),
                users.c.telegram_id.label('user_telegram_id'),
                users.c.chat_id.label('user_chat_id')
            )
            .join(users, table.c.user_id == users.c.id)
            .where(
                and_(
                    type_filter,
                    table.c.status == status if status else True
                )
            )
            .order_by(desc(table.c.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        rows = result.mappings().all()
        return [dict(row) for row in rows]


# ------------------- ПОИСК ПО ID -------------------
async def get_request_by_id(request_id: int) -> Optional[dict]:
    """Ищет заявку по ID в обеих таблицах."""
    async with db.session_factory() as session:
        # assistance
        res = await session.execute(
            select(assistance_requests, users.c.username, users.c.telegram_id, users.c.chat_id)
            .join(users, assistance_requests.c.user_id == users.c.id)
            .where(assistance_requests.c.id == request_id)
        )
        row = res.mappings().first()
        if row:
            data = dict(row)
            data['request_type'] = 'assistance'
            return data

        # rewards
        res = await session.execute(
            select(rewards, users.c.username, users.c.telegram_id, users.c.chat_id)
            .join(users, rewards.c.user_id == users.c.id)
            .where(rewards.c.id == request_id)
        )
        row = res.mappings().first()
        if row:
            data = dict(row)
            data['request_type'] = 'reward'
            return data

        return None


# ------------------- ДЕТАЛЬНАЯ ИНФОРМАЦИЯ -------------------
async def get_request_detail(request_type: str, request_id: int) -> Optional[dict]:
    """Полная информация: заявка + пользователь + медиа + все комментарии."""
    async with db.session_factory() as session:
        if request_type == 'assistance':
            table = assistance_requests
            media_condition = media_messages.c.assistance_request_id == request_id
        else:
            table = rewards
            media_condition = media_messages.c.reward_id == request_id

        # Основная запись
        query = (
            select(table, users.c.username, users.c.telegram_id, users.c.chat_id, users.c.phone_number)
            .join(users, table.c.user_id == users.c.id)
            .where(table.c.id == request_id)
        )
        result = await session.execute(query)
        main = result.mappings().first()
        if not main:
            return None

        # Медиа (список словарей с chat_id, message_id, media_group_id)
        media_res = await session.execute(
            select(media_messages)
            .where(media_condition)
            .order_by(media_messages.c.created_at.asc())
        )
        media = [dict(row) for row in media_res.mappings().all()]

        # ВСЕ КОММЕНТАРИИ
        comments_res = await session.execute(
            select(request_comments, users.c.username.label('admin_username'))
            .join(users, request_comments.c.admin_id == users.c.id, isouter=True)
            .where(
                request_comments.c.request_type == request_type,
                request_comments.c.request_id == request_id
            )
            .order_by(request_comments.c.created_at.asc())
        )
        comments = [dict(row) for row in comments_res.mappings().all()]

        result_dict = dict(main)
        result_dict['media'] = media
        result_dict['comments'] = comments
        return result_dict


# ------------------- ИЗМЕНЕНИЕ СТАТУСА -------------------
async def update_request_status(request_type: str, request_id: int, new_status: str):
    """Обновляет статус и синхронизирует булевы поля."""
    async with db.session_factory() as session:
        async with session.begin():
            if request_type == 'assistance':
                table = assistance_requests
                is_processed = (new_status == 'completed')
                await session.execute(
                    update(table)
                    .where(table.c.id == request_id)
                    .values(status=new_status, is_processed=is_processed)
                )
            else:
                table = rewards
                is_paid = (new_status == 'completed')
                await session.execute(
                    update(table)
                    .where(table.c.id == request_id)
                    .values(status=new_status, is_paid=is_paid)
                )


# ------------------- ДОБАВЛЕНИЕ КОММЕНТАРИЯ -------------------
async def add_comment(request_type: str, request_id: int, admin_id: int, comment: str):
    """Добавляет новый комментарий к обращению."""
    async with db.session_factory() as session:
        async with session.begin():
            await session.execute(
                insert(request_comments).values(
                    request_type=request_type,
                    request_id=request_id,
                    admin_id=admin_id,
                    comment=comment
                )
            )