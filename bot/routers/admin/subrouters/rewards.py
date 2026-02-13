from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_admin_mode_keyboard,
    get_admin_done_keyboard,
    BTN_ADMIN_DONE,
    BTN_BACK,
)
from bot.services.admin import requests_service

rewards_router = Router()

# ------------------------------------------------------------
# 1. Вход в раздел выплат
# ------------------------------------------------------------
@rewards_router.message(
    AdminStates.choosing_mode,
    F.text == "💰 Выплатить за отзывы"
)
async def start_rewards_review(message: Message, state: FSMContext, bot: Bot):  # ← добавили bot
    await state.set_state(AdminStates.viewing_rewards_list)
    await show_rewards_list(message, state, bot)
async def show_rewards_list(message: Message, state: FSMContext, bot: Bot):
    """Показывает до 20 необработанных заявок на выплату."""
    requests = await requests_service.get_requests_by_filters(
        request_type="reward",
        status="new",
        limit=20,
        offset=0
    )

    logger.info(f"Получено заявок: {len(requests)}")
    if requests:
        logger.info(f"Первый элемент: {requests[0]}")

    if not requests:
        await state.set_state(AdminStates.choosing_mode)
        await message.answer(
            "✅ Нет новых заявок на выплату.\n"
            "Выберите режим работы:",
            reply_markup=get_admin_mode_keyboard()
        )
        return

    data = await state.get_data()
    old_ids = data.get("list_message_ids", [])
    for msg_id in old_ids:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass

    await message.answer(
        f"💰 Найдено {len(requests)} новых заявок. Отправляю...",
        reply_markup=get_admin_done_keyboard()
    )

    list_message_ids = []
    for req in requests:
        if req is None:
            logger.warning("Пропущен None в списке заявок")
            continue

        # Безопасное извлечение данных
        user_username = req.get('user_username')
        user_telegram_id = req.get('user_telegram_id', '?')
        user_link = f"@{user_username}" if user_username else f"ID {user_telegram_id}"

        created_date = req['created_at'].strftime('%d.%m.%Y %H:%M') if req.get('created_at') else 'неизвестно'

        # ✅ Защита от None при взятии среза
        link = req.get('link')
        link_display = (link[:50] + '...') if link else 'нет ссылки'
        if len(link_display) > 53:
            link_display = link_display[:50] + '...'

        text = req.get('text')
        text_display = (text[:100] + '...') if text else 'нет текста'
        if len(text_display) > 103:
            text_display = text_display[:100] + '...'

        text_message = (
            f"🆔 #{req['id']} | {user_link}\n"
            f"📅 {created_date}\n"
            f"🔗 Ссылка: {link_display}\n"
            f"📝 {text_display}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Обработать",
                callback_data=f"process_reward:{req['id']}"
            )]
        ])
        sent = await message.answer(text_message, reply_markup=kb)
        list_message_ids.append(sent.message_id)

    await state.update_data(list_message_ids=list_message_ids)
# ------------------------------------------------------------
# 2. Обработка нажатия «Обработать» -> детальный просмотр
# ------------------------------------------------------------
@rewards_router.callback_query(
    StateFilter(AdminStates.viewing_rewards_list),
    F.data.startswith("process_reward:")
)
async def process_reward(callback: CallbackQuery, state: FSMContext, bot: Bot):
    _, req_id_str = callback.data.split(":")
    req_id = int(req_id_str)

    # Удаляем все сообщения списка
    data = await state.get_data()
    for msg_id in data.get("list_message_ids", []):
        try:
            await bot.delete_message(callback.message.chat.id, msg_id)
        except:
            pass

    await state.set_state(AdminStates.viewing_rewards_detail)
    await show_reward_detail(callback, state, req_id)
async def show_reward_detail(target: CallbackQuery | Message, state: FSMContext, request_id: int, bot: Bot = None):
    """Отображает детальную информацию по заявке на выплату и сохраняет ID сообщений для последующего удаления."""
    if isinstance(target, CallbackQuery):
        message = target.message
        bot = target.bot
    else:
        message = target
        bot = bot

    detail = await requests_service.get_request_detail("reward", request_id)
    if not detail:
        await message.answer("❌ Заявка не найдена.")
        return

    detail_message_ids = []  # ← список для удаления при возврате

    # --- Текст заявки ---
    user_link = f"@{detail['username']}" if detail['username'] else f"ID {detail['telegram_id']}"
    created_date = detail['created_at'].strftime('%d.%m.%Y %H:%M') if detail.get('created_at') else 'неизвестно'
    text = (
        f"🆔 Заявка #{detail['id']}\n"
        f"👤 Пользователь: {user_link}\n"
        f"📱 Телефон: {detail.get('phone_number', 'не указан')}\n"
        f"📅 Создано: {created_date}\n"
        f"🔄 Статус: **{detail['status']}**\n\n"
        f"🔗 Ссылка на отзыв: {detail.get('link', 'нет ссылки')}\n"
    )
    if detail.get('text'):
        text += f"📝 Текст отзыва:\n{detail['text']}\n"
    if detail.get('comments'):
        text += "\n📋 **Комментарии:**\n"
        for c in detail['comments']:
            admin_name = f"@{c['admin_username']}" if c['admin_username'] else "Админ"
            time_str = c['created_at'].strftime('%d.%m %H:%M') if c.get('created_at') else ''
            text += f"• {time_str} {admin_name}: {c['comment']}\n"

    msg_text = await message.answer(text)
    detail_message_ids.append(msg_text.message_id)

    # --- Медиа (группировка альбомов) ---
    media_list = detail.get('media', [])
    albums = {}
    singles = []
    for media in media_list:
        if media.get('media_group_id'):
            albums.setdefault(media['media_group_id'], []).append(media)
        else:
            singles.append(media)

    # Одиночные медиа
    for media in singles:
        try:
            fwd = await bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id=media['chat_id'],
                message_id=media['message_id']
            )
            detail_message_ids.append(fwd.message_id)
        except Exception as e:
            logger.error(f"Не удалось переслать сообщение {media['message_id']}: {e}")

    # Альбомы
    for group_id, group_media in albums.items():
        group_media.sort(key=lambda x: x['id'])
        msg_ids = [m['message_id'] for m in group_media]
        try:
            fwd_messages = await bot.forward_messages(
                chat_id=message.chat.id,
                from_chat_id=group_media[0]['chat_id'],
                message_ids=msg_ids
            )
            for fwd_msg in fwd_messages:
                detail_message_ids.append(fwd_msg.message_id)
        except Exception as e:
            logger.error(f"Не удалось переслать альбом {group_id}: {e}")

    # --- Кнопки действий ---
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Отметить выплаченным",
                callback_data=f"mark_paid:{detail['id']}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад к списку",
                callback_data="back_to_rewards_list"
            )
        ]
    ])
    msg_actions = await message.answer("Действия:", reply_markup=kb)
    detail_message_ids.append(msg_actions.message_id)

    # --- Сохраняем ID сообщений и ID заявки в state ---
    await state.update_data(
        detail_message_ids=detail_message_ids,
        current_reward_id=detail['id']
    )
# ------------------------------------------------------------
# 3. Отметить выплату выполненной
# ------------------------------------------------------------
@rewards_router.callback_query(F.data.startswith("mark_paid:"))
async def mark_paid_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    _, req_id_str = callback.data.split(":")
    req_id = int(req_id_str)

    await requests_service.update_request_status("reward", req_id, "completed")
    await callback.answer("✅ Выплата отмечена как выполненная.")
    await show_reward_detail(callback, state, req_id)

# ------------------------------------------------------------
# 4. Кнопка «Назад» в списке -> возврат в главное меню
# ------------------------------------------------------------
@rewards_router.message(
    StateFilter(AdminStates.viewing_rewards_list),
    F.text == BTN_BACK
)
async def back_from_list(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    for msg_id in data.get("list_message_ids", []):
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_mode_keyboard()
    )

# ------------------------------------------------------------
# 5. Кнопка «Назад» в деталях -> возврат к списку
# ------------------------------------------------------------
@rewards_router.callback_query(F.data == "back_to_rewards_list")
async def back_to_list_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    for msg_id in data.get("detail_message_ids", []):
        try:
            await bot.delete_message(callback.message.chat.id, msg_id)
        except:
            pass
    await state.set_state(AdminStates.viewing_rewards_list)
    try:  # ✅ Оборачиваем
        await callback.message.delete()
    except:
        pass
    await show_rewards_list(callback.message, state, bot)

@rewards_router.message(StateFilter(AdminStates.viewing_rewards_list), F.text == BTN_ADMIN_DONE)
async def finish_rewards_session(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    # удаляем список
    for msg_id in data.get("list_message_ids", []):
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    # удаляем возможные детальные
    for msg_id in data.get("detail_message_ids", []):
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    await state.set_state(AdminStates.choosing_mode)
    await message.answer("✅ Сессия выплат завершена.", reply_markup=get_admin_mode_keyboard())

@rewards_router.message(
    StateFilter(AdminStates.viewing_rewards_detail),
    F.text == BTN_BACK
)
async def back_from_reward_detail(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    for msg_id in data.get("detail_message_ids", []):
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    await state.set_state(AdminStates.viewing_rewards_list)
    try:  # ✅ Оборачиваем
        await message.delete()
    except:
        pass
    await show_rewards_list(message, state, bot)