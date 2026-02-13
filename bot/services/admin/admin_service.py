from typing import List

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from sqlalchemy import select, and_, update, func

from bot.db.engine import db
from bot.db.messages_text import messages_text
from bot.db.tables import (
    assistance_requests,
    rewards,
    media_messages,
    users, messages_texts
)
from bot.keyboards.admin.callback_data import ProcessRequestCD


async def get_pending_assistance_requests(request_type: str, limit: int = 10) -> List[dict]:
    async with db.session_factory() as session:
        result = await session.execute(
            select(assistance_requests)
            .where(
                and_(
                    assistance_requests.c.request_type == request_type,
                    assistance_requests.c.is_processed == False
                )
            )
            .order_by(assistance_requests.c.created_at.asc())
            .limit(limit)
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]


async def get_pending_rewards(limit: int = 10) -> List[dict]:
    async with db.session_factory() as session:
        result = await session.execute(
            select(rewards)
            .where(
                and_(
                    rewards.c.is_paid == False,
                    rewards.c.link != None
                )
            )
            .order_by(rewards.c.created_at.asc())
            .limit(limit)
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]


async def get_media_for_request(request_type: str, request_id: int) -> List[dict]:
    async with db.session_factory() as session:
        if request_type == "assistance":
            condition = media_messages.c.assistance_request_id == request_id
        else:
            condition = media_messages.c.reward_id == request_id

        result = await session.execute(
            select(media_messages)
            .where(condition)
            .order_by(media_messages.c.id.asc())
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]


async def send_request_to_admin(
        bot: Bot,
        admin_chat_id: int,
        request_type: str,
        request: dict,
        media_list: List[dict],
        state: FSMContext
):
    """
    Отправляет администратору заявку со всеми связанными медиа.
    Использует только forward_message / forward_messages.
    Сохраняет в state список message_id отправленных сообщений.
    """
    sent_message_ids = []

    # ----- 1. Формируем текст-шапку заявки -----
    if request_type == "assistance":
        async with db.session_factory() as session:
            user_res = await session.execute(
                select(users.c.username, users.c.telegram_id)
                .where(users.c.id == request["user_id"])
            )
            user_row = user_res.first()
            username = user_row[0] if user_row else "no_username"
            telegram_id = user_row[1] if user_row else "?"
        header = (
            f"📩 Обращение #{request['id']} ({request['request_type']})\n"
            f"От: @{username} (ID: {telegram_id})\n"
            f"Дата: {request['created_at']}\n\n"
        )
    else:  # rewards
        async with db.session_factory() as session:
            user_res = await session.execute(
                select(users.c.username, users.c.telegram_id)
                .where(users.c.id == request["user_id"])
            )
            user_row = user_res.first()
            username = user_row[0] if user_row else "no_username"
            telegram_id = user_row[1] if user_row else "?"
        header = (
            f"💰 Заявка на выплату #{request['id']}\n"
            f"От: @{username} (ID: {telegram_id})\n"
            f"Ссылка: {request['link']}\n"
            f"Дата: {request['created_at']}\n\n"
        )

    # ----- 2. Кнопка «Обработано» (inline) -----
    # Мы не знаем message_id до отправки, поэтому сначала отправляем медиа,
    # потом кнопку прикрепляем к последнему сообщению.
    # Сделаем callback_data с плейсхолдером, а после отправки заменим.
    placeholder_callback = ProcessRequestCD(
        request_type=request_type,
        request_id=request["id"],
        msg_ids="PLACEHOLDER"
    ).pack()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Обработано", callback_data=placeholder_callback)]
        ]
    )

    # ----- 3. Если нет медиа — просто текст с кнопкой -----
    if not media_list:
        msg = await bot.send_message(admin_chat_id, header, reply_markup=keyboard)
        sent_message_ids.append(msg.message_id)
    else:
        # Сначала отправляем текст-шапку (без кнопки)
        header_msg = await bot.send_message(admin_chat_id, header)
        sent_message_ids.append(header_msg.message_id)

        # Группируем медиа по media_group_id
        albums = {}
        singles = []
        for media in media_list:
            if media["media_group_id"]:
                albums.setdefault(media["media_group_id"], []).append(media)
            else:
                singles.append(media)

        # Пересылаем одиночные сообщения
        for media in singles:
            try:
                fwd = await bot.forward_message(
                    chat_id=admin_chat_id,
                    from_chat_id=media["chat_id"],
                    message_id=media["message_id"]
                )
                sent_message_ids.append(fwd.message_id)
            except Exception as e:
                logger.error(f"Не удалось переслать сообщение {media['message_id']}: {e}")

        # Пересылаем альбомы (группы)
        for group_id, group_media in albums.items():
            group_media.sort(key=lambda x: x["id"])
            msg_ids = [m["message_id"] for m in group_media]
            try:
                fwd_messages = await bot.forward_messages(
                    chat_id=admin_chat_id,
                    from_chat_id=group_media[0]["chat_id"],
                    message_ids=msg_ids
                )
                for msg in fwd_messages:
                    sent_message_ids.append(msg.message_id)
            except Exception as e:
                logger.error(f"Не удалось переслать альбом {group_id}: {e}")

        # После всех медиа отправляем кнопку «Обработано»
        button_msg = await bot.send_message(admin_chat_id, "⬆️ Заявка выше", reply_markup=keyboard)
        sent_message_ids.append(button_msg.message_id)

        # ----- 4. Обновляем callback_data с реальными message_id -----
        real_callback = ProcessRequestCD(
            request_type=request_type,
            request_id=request["id"],
            msg_ids=",".join(map(str, sent_message_ids))
        ).pack()
        new_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Обработано", callback_data=real_callback)]
            ]
        )
        await bot.edit_message_reply_markup(
            chat_id=admin_chat_id,
            message_id=button_msg.message_id,
            reply_markup=new_keyboard
        )

    # ----- 5. Сохраняем в state список сообщений этой заявки -----
    data = await state.get_data()
    sent_map = data.get("sent_messages", {})
    sent_map[str(request["id"])] = sent_message_ids
    await state.update_data(sent_messages=sent_map)


async def delete_admin_messages(bot: Bot, chat_id: int, message_ids: List[int]):
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")


async def mark_request_processed(request_type: str, request_id: int):
    async with db.session_factory() as session:
        async with session.begin():
            if request_type == "assistance":
                await session.execute(
                    update(assistance_requests)
                    .where(assistance_requests.c.id == request_id)
                    .values(is_processed=True, processed_at=func.now())
                )
            else:  # reward
                await session.execute(
                    update(rewards)
                    .where(rewards.c.id == request_id)
                    .values(is_paid=True, processed_at=func.now())
                )

async def get_all_messages() -> List[dict]:
    async with db.session_factory() as session:
        result = await session.execute(
            select(messages_texts.c.message_key, messages_texts.c.text)
            .order_by(messages_texts.c.message_key)
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]

async def update_message_text(message_key: str, new_text: str) -> bool:
    async with db.session_factory() as session:
        async with session.begin():
            result = await session.execute(
                update(messages_texts)
                .where(messages_texts.c.message_key == message_key)
                .values(text=new_text)
            )
            if result.rowcount == 0:
                return False
    messages_text.update_message(message_key, new_text)
    return True