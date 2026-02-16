from typing import List
import re
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from loguru import logger

from bot.db.messages_text import messages_text
from bot.fsm.states.customer import ReviewStates
from bot.keyboards.customer.main_menu_kb import main_menu
from bot.keyboards.customer.review_kb import get_review_kb, get_back_keyboard
from bot.utils.helpers import button_messages
from bot.services.customer.rewards_service import (
    create_reward,
    save_reward_media,
    update_reward_link
)

review_router = Router()


def is_valid_review_link(link: str) -> bool:
    """Проверяет, что ссылка ведёт на Ozon или Wildberries."""
    ozon_pattern = r'(https?://)?(www\.)?ozon\.ru/(product|context/detail)/'
    wb_pattern = r'(https?://)?(www\.)?wildberries\.ru/catalog/\d+/detail\.aspx'
    return re.search(ozon_pattern, link) is not None or re.search(wb_pattern, link) is not None


# ------------------------------------------------------------
# 1. Начало процесса
# ------------------------------------------------------------
@review_router.message(F.text == button_messages["review"])
async def start_review(message: Message, state: FSMContext):
    await state.set_state(ReviewStates.WAITING_FOR_READY)
    hide_msg = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await hide_msg.delete()

    msg1 = await message.answer(
        messages_text["reward_request"],
        reply_markup=get_review_kb()
    )
    msg2 = await message.answer(
        "🔙 Нажмите «Назад» для возврата.",
        reply_markup=get_back_keyboard()
    )
    await state.update_data(message_ids=[msg1.message_id, msg2.message_id])


# ------------------------------------------------------------
# 2. Обработка кнопки "Назад" на этапе WAITING_FOR_READY
# ------------------------------------------------------------
@review_router.message(ReviewStates.WAITING_FOR_READY, F.text == "🔙 Назад")
async def back_from_ready(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    # Удаляем сообщения текущего шага
    for msg_id in data.get("message_ids", []):
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    await state.clear()
    await message.delete()
    await message.answer(
        messages_text["welcome_message"],
        reply_markup=main_menu()
    )


# ------------------------------------------------------------
# 3. Обработка нажатия "Готов" – запрос фото
# ------------------------------------------------------------
@review_router.callback_query(ReviewStates.WAITING_FOR_READY, F.data == "ready_for_review")
async def get_review(callback: CallbackQuery, state: FSMContext):
    try:
        reward_id = await create_reward(callback.from_user.id)
    except Exception as e:
        logger.error(f"Failed to create reward for {callback.from_user.id}: {e}")
        await callback.message.answer("❌ Ошибка, попробуйте позже.")
        await state.clear()
        await callback.answer()
        return

    # Удаляем сообщения предыдущего шага (приглашение нажать "Готов")
    data = await state.get_data()
    for msg_id in data.get("message_ids", []):
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except:
            pass

    await state.update_data(reward_id=reward_id)
    await state.set_state(ReviewStates.WAITING_FOR_PHOTO)

    msg = await callback.message.answer(
        messages_text["get_photo_for_reward"],
        reply_markup=get_back_keyboard()
    )
    # Сохраняем только ID нового сообщения
    await state.update_data(message_ids=[msg.message_id])
    await callback.answer()


# ------------------------------------------------------------
# 4. Получение одиночного фото
# ------------------------------------------------------------
@review_router.message(ReviewStates.WAITING_FOR_PHOTO, ~F.media_group_id)
async def handle_single_media(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    reward_id = data.get("reward_id")
    if not reward_id:
        await message.answer("❌ Сессия устарела. Начните заново.")
        await state.clear()
        return

    # Обработка кнопки "Назад"
    if message.text == "🔙 Назад":
        # Удаляем сообщения текущего шага (приглашение отправить фото)
        for msg_id in data.get("message_ids", []):
            try:
                await bot.delete_message(message.chat.id, msg_id)
            except:
                pass
        await state.set_state(ReviewStates.WAITING_FOR_READY)
        msg1 = await message.answer(
            messages_text["reward_request"],
            reply_markup=get_review_kb()
        )
        msg2 = await message.answer(
            "🔙 Нажмите «Назад» для возврата.",
            reply_markup=get_back_keyboard()
        )
        await state.update_data(message_ids=[msg1.message_id, msg2.message_id])
        await message.delete()
        return

    # Проверка, что прислано именно фото
    if not message.photo:
        await message.answer(
            "❌ Пожалуйста, отправьте фотографии (можно несколько в одном альбоме). Другие типы файлов не принимаются.")
        return

    # Сохраняем в БД
    await save_reward_media(reward_id, [message])

    # ❌ НЕ УДАЛЯЕМ старые сообщения – они остаются в чате
    # Просто отправляем новое приглашение и переходим на следующий шаг
    msg = await message.answer(
        messages_text["get_link_for_reward"],
        reply_markup=get_back_keyboard()
    )
    # Перезаписываем message_ids новым ID (старые ID больше не хранятся)
    await state.update_data(message_ids=[msg.message_id])
    await state.set_state(ReviewStates.WAITING_FOR_LINK)


# ------------------------------------------------------------
# 5. Получение альбома (несколько фото)
# ------------------------------------------------------------
@review_router.message(ReviewStates.WAITING_FOR_PHOTO, F.media_group_id)
async def handle_album(message: Message, state: FSMContext, album: List[Message], bot: Bot):
    data = await state.get_data()
    reward_id = data.get("reward_id")
    if not reward_id:
        await message.answer("❌ Сессия устарела. Начните заново.")
        await state.clear()
        return

    # Проверяем, что все сообщения альбома – фото
    for msg in album:
        if not msg.photo:
            await message.answer("❌ Альбом должен содержать только фотографии. Видео и другие файлы не принимаются.")
            return

    await save_reward_media(reward_id, album)

    # ❌ НЕ УДАЛЯЕМ старые сообщения
    msg = await message.answer(
        messages_text["get_link_for_reward"],
        reply_markup=get_back_keyboard()
    )
    await state.update_data(message_ids=[msg.message_id])
    await state.set_state(ReviewStates.WAITING_FOR_LINK)


# ------------------------------------------------------------
# 6. Получение ссылки на отзыв
# ------------------------------------------------------------
@review_router.message(ReviewStates.WAITING_FOR_LINK)
async def handle_review_link(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    reward_id = data.get("reward_id")
    if not reward_id:
        await message.answer("❌ Сессия устарела. Начните заново.")
        await state.clear()
        return

    # Обработка кнопки "Назад"
    if message.text == "🔙 Назад":
        # Удаляем сообщения текущего шага (приглашение отправить ссылку)
        for msg_id in data.get("message_ids", []):
            try:
                await bot.delete_message(message.chat.id, msg_id)
            except:
                pass
        await state.set_state(ReviewStates.WAITING_FOR_PHOTO)
        msg = await message.answer(
            messages_text["get_photo_for_reward"],
            reply_markup=get_back_keyboard()
        )
        await state.update_data(message_ids=[msg.message_id])
        await message.delete()
        return

    link = message.text.strip()

    if not is_valid_review_link(link):
        await message.answer("❌ Пожалуйста, отправьте ссылку на отзыв с Ozon или Wildberries.")
        return

    await update_reward_link(reward_id, link)

    # ❌ НЕ УДАЛЯЕМ старые сообщения
    await message.answer(
        messages_text["reward_submission_received"],
        reply_markup=main_menu()
    )
    await state.clear()
