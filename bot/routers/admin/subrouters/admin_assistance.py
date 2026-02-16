from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from sqlalchemy import select

from bot.db.engine import db
from bot.db.tables import users
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_assistance_type_keyboard,
    get_status_choice_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
    get_request_actions_keyboard,
    get_status_choice_inline,
    get_admin_main_keyboard,
    BTN_BACK,
    BTN_CANCEL,
    BTN_ADMIN_ASSISTANCE,
    BTN_ADMIN_SEARCH_REQUEST,
    BTN_ASSISTANCE_DEFECT,
    BTN_ASSISTANCE_COMPLAINT,
    BTN_ASSISTANCE_FEEDBACK,
    BTN_ASSISTANCE_REWARDS,
    BTN_STATUS_NEW,
    BTN_STATUS_IN_PROGRESS,
    BTN_STATUS_COMPLETED,
    BTN_STATUS_REJECTED, BTN_ADMIN_SEARCH_REWARD,  # новая кнопка
)
from bot.services.admin import requests_service

admin_assistance_router = Router()

PAGE_SIZE = 10


# ------------------------------------------------------------
# 1. Вход в раздел "Обращения"
# ------------------------------------------------------------
@admin_assistance_router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_ASSISTANCE
)
async def enter_assistance_section(message: Message, state: FSMContext):
    await state.set_state(AdminStates.choosing_assistance_type)
    await message.answer(
        "Выберите тип обращения:",
        reply_markup=get_assistance_type_keyboard()
    )


# ------------------------------------------------------------
# 2. Выбор типа обращения
# ------------------------------------------------------------
@admin_assistance_router.message(
    AdminStates.choosing_assistance_type,
    F.text.in_([BTN_ASSISTANCE_DEFECT, BTN_ASSISTANCE_COMPLAINT,
                BTN_ASSISTANCE_FEEDBACK, BTN_ASSISTANCE_REWARDS])
)
async def choose_assistance_type(message: Message, state: FSMContext):
    type_map = {
        BTN_ASSISTANCE_DEFECT: "defect",
        BTN_ASSISTANCE_COMPLAINT: "complaint",
        BTN_ASSISTANCE_FEEDBACK: "feedback",
        BTN_ASSISTANCE_REWARDS: "reward"
    }
    subtype = type_map[message.text]
    await state.update_data(assistance_subtype=subtype)
    await state.set_state(AdminStates.choosing_assistance_status)
    await message.answer(
        "Выберите статус заявок для просмотра:",
        reply_markup=get_status_choice_keyboard()
    )


@admin_assistance_router.message(
    AdminStates.choosing_assistance_type,
    F.text == BTN_BACK
)
async def back_to_admin_menu(message: Message, state: FSMContext):
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "Главное меню администратора:",
        reply_markup=get_admin_main_keyboard()
    )


@admin_assistance_router.message(
    AdminStates.choosing_assistance_status,
    F.text.in_([BTN_STATUS_NEW, BTN_STATUS_IN_PROGRESS, BTN_STATUS_COMPLETED, BTN_STATUS_REJECTED])
)
async def choose_status(message: Message, state: FSMContext, bot: Bot):
    status_map = {
        BTN_STATUS_NEW: "new",
        BTN_STATUS_IN_PROGRESS: "in_progress",
        BTN_STATUS_COMPLETED: "completed",
        BTN_STATUS_REJECTED: "rejected",
    }
    status = status_map[message.text]
    await state.update_data(assistance_status=status)
    await state.set_state(AdminStates.viewing_assistance_list)
    await state.update_data(assistance_offset=0)  # сбрасываем offset
    await show_requests_list(message, state, bot)


@admin_assistance_router.message(
    AdminStates.choosing_assistance_status,
    F.text == BTN_BACK
)
async def back_to_type_choice(message: Message, state: FSMContext):
    await state.set_state(AdminStates.choosing_assistance_type)
    await message.answer(
        "Выберите тип обращения:",
        reply_markup=get_assistance_type_keyboard()
    )


async def show_requests_list(message: Message, state: FSMContext, bot: Bot):
    """Отображает страницу заявок с пагинацией (20 шт)."""
    data = await state.get_data()
    subtype = data.get("assistance_subtype")
    status = data.get("assistance_status")
    offset = data.get("assistance_offset", 0)
    limit = PAGE_SIZE

    if subtype == "reward":
        request_type = "reward"
        subtype_filter = None
    else:
        request_type = "assistance"
        subtype_filter = subtype

    # Получаем заявки
    requests = await requests_service.get_requests_by_filters(
        request_type=request_type,
        subtype=subtype_filter,
        status=status,
        limit=limit,
        offset=offset
    )

    # Получаем общее количество (для пагинации)
    total = await requests_service.get_total_requests_count(
        request_type=request_type,
        subtype=subtype_filter,
        status=status
    )

    if not requests:
        await message.answer(
            "✅ Нет заявок с такими параметрами.",
            reply_markup=get_status_choice_keyboard()
        )
        await state.set_state(AdminStates.choosing_assistance_status)
        return

    # Удаляем предыдущие сообщения списка
    old_ids = data.get("list_message_ids", [])
    for msg_id in old_ids:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass

    list_message_ids = []
    for req in requests:
        created_date = req['created_at'].strftime('%d.%m.%Y %H:%M') if req.get('created_at') else 'неизвестно'

        if request_type == "reward":
            link = req.get('link')
            if link:
                link_display = link[:50] + ('...' if len(link) > 50 else '')
            else:
                link_display = 'нет ссылки'

            text_preview = (req.get('text') or 'нет текста')[:100]
            if len(text_preview) == 100:
                text_preview += '...'

            text_line = f"🔗 {link_display}\n📝 {text_preview}"
        else:
            text_preview = (req.get('text') or 'нет текста')[:100]
            if len(text_preview) == 100:
                text_preview += '...'
            text_line = f"📝 {text_preview}"

        text = (
            f"🆔 #{req['id']} | @{req['user_username']}\n"
            f"📅 {created_date}\n"
            f"📌 {req['request_type'] if request_type == 'assistance' else '💰 Выплата'}\n"
            f"{text_line}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Обработать",
                callback_data=f"process_request:{request_type}:{req['id']}"
            )]
        ])
        sent = await message.answer(text, reply_markup=kb)
        list_message_ids.append(sent.message_id)

    # Клавиатура пагинации (inline)
    pagination_kb = []
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data="assistance_prev"))
    if offset + limit < total:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data="assistance_next"))
    if nav_buttons:
        pagination_kb.append(nav_buttons)

    # Если есть пагинация – показываем inline-клавиатуру, иначе – обычную кнопку "Назад"
    if pagination_kb:
        pagination_msg = await message.answer(
            "⬆️ Список заявок",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=pagination_kb)
        )
        list_message_ids.append(pagination_msg.message_id)
    else:
        back_msg = await message.answer(
            "⬆️ Список заявок",
            reply_markup=get_back_keyboard()
        )
        list_message_ids.append(back_msg.message_id)

    await state.update_data(
        list_message_ids=list_message_ids,
        assistance_offset=offset,
        assistance_total=total
    )


# ------------------------------------------------------------
# 4. Пагинация: вперёд / назад
# ------------------------------------------------------------
@admin_assistance_router.callback_query(
    StateFilter(AdminStates.viewing_assistance_list),
    F.data.in_(["assistance_next", "assistance_prev"])
)
async def paginate_assistance(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    offset = data.get("assistance_offset", 0)
    limit = PAGE_SIZE

    if callback.data == "assistance_next":
        offset += limit
    elif callback.data == "assistance_prev":
        offset = max(0, offset - limit)

    await state.update_data(assistance_offset=offset)
    await callback.answer()
    await show_requests_list(callback.message, state, bot)


# ------------------------------------------------------------
# 5. Кнопка «Назад» в списке -> возврат к выбору статуса
# ------------------------------------------------------------
@admin_assistance_router.message(
    StateFilter(AdminStates.viewing_assistance_list),
    F.text == BTN_BACK
)
async def back_from_list(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    for msg_id in data.get("list_message_ids", []):
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    await state.set_state(AdminStates.choosing_assistance_status)
    await message.answer(
        "Выберите статус заявок:",
        reply_markup=get_status_choice_keyboard()
    )


# ------------------------------------------------------------
# 6. Нажатие «Обработать» -> удаляем список, показываем детали
# ------------------------------------------------------------
@admin_assistance_router.callback_query(
    StateFilter(AdminStates.viewing_assistance_list),
    F.data.startswith("process_request:")
)
async def process_request(callback: CallbackQuery, state: FSMContext, bot: Bot):
    _, req_type, req_id_str = callback.data.split(":")
    req_id = int(req_id_str)

    # Удаляем все сообщения списка
    data = await state.get_data()
    for msg_id in data.get("list_message_ids", []):
        try:
            await bot.delete_message(callback.message.chat.id, msg_id)
        except:
            pass

    await state.set_state(AdminStates.viewing_assistance_detail)
    await show_request_detail(callback, state, req_type, req_id)


async def show_request_detail(
        target: CallbackQuery | Message,
        state: FSMContext,
        request_type: str,
        request_id: int,
        bot: Bot = None
):
    """Отображает детальную информацию по заявке + пересылает медиа."""
    if isinstance(target, CallbackQuery):
        message = target.message
        bot = target.bot
    else:
        message = target
        bot = bot

    # ---------- Удаляем предыдущие детальные сообщения ----------
    data = await state.get_data()
    old_detail_ids = data.get("detail_message_ids", [])
    for msg_id in old_detail_ids:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить старое детальное сообщение {msg_id}: {e}")
    await state.update_data(detail_message_ids=[])
    # ------------------------------------------------------------

    detail = await requests_service.get_request_detail(request_type, request_id)
    if not detail:
        await message.answer("❌ Заявка не найдена.")
        return

    detail_message_ids = []

    user_link = f"@{detail['username']}" if detail['username'] else f"ID {detail['telegram_id']}"
    created_date = detail['created_at'].strftime('%d.%m.%Y %H:%M') if detail.get('created_at') else 'неизвестно'
    text = f"🆔 Заявка #{detail['id']}\n👤 Пользователь: {user_link}\n📱 Телефон: {detail.get('phone_number', 'не указан')}\n📅 Создано: {created_date}\n🔄 Статус: **{detail['status']}**\n\n"
    if request_type == 'assistance':
        text += f"📝 Текст обращения:\n{detail.get('text', 'нет текста')}\n"
    else:  # reward
        text += f"🔗 Ссылка на отзыв: {detail.get('link', 'нет ссылки')}\n"
        if detail.get('text'):
            text += f"📝 Текст отзыва:\n{detail['text']}\n"
    if detail.get('comments'):
        text += "\n📋 **История комментариев:**\n"
        for c in detail['comments']:
            admin_name = f"@{c['admin_username']}" if c['admin_username'] else "Админ"
            time_str = c['created_at'].strftime('%d.%m %H:%M') if c.get('created_at') else ''
            text += f"• {time_str} {admin_name}: {c['comment']}\n"

    msg_text = await message.answer(text)
    detail_message_ids.append(msg_text.message_id)

    # --- пересылка медиа ---
    media_list = detail.get('media', [])
    albums, singles = {}, []
    for media in media_list:
        if media.get('media_group_id'):
            albums.setdefault(media['media_group_id'], []).append(media)
        else:
            singles.append(media)

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

    # --- кнопки действий ---
    kb = get_request_actions_keyboard(request_type, request_id)
    msg_actions = await message.answer("Действия:", reply_markup=kb)
    detail_message_ids.append(msg_actions.message_id)

    # --- сохраняем ID и текущую заявку ---
    await state.update_data(
        detail_message_ids=detail_message_ids,
        current_request_type=request_type,
        current_request_id=request_id
    )


# ------------------------------------------------------------
# 6. Кнопка «Назад» в детальном просмотре -> возврат к списку
# ------------------------------------------------------------
@admin_assistance_router.message(
    StateFilter(AdminStates.viewing_assistance_detail),
    F.text == BTN_BACK
)
async def back_from_detail(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    detail_ids = data.get("detail_message_ids", [])

    for msg_id in detail_ids:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

    await state.update_data(detail_message_ids=[])
    await state.set_state(AdminStates.viewing_assistance_list)
    await show_requests_list(message, state, bot)

    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить reply-сообщение: {e}")


# ------------------------------------------------------------
# 7. Изменение статуса (inline)
# ------------------------------------------------------------
@admin_assistance_router.callback_query(F.data.startswith("change_status:"))
async def change_status_callback(callback: CallbackQuery, state: FSMContext):
    _, req_type, req_id_str = callback.data.split(":")
    req_id = int(req_id_str)
    kb = get_status_choice_inline(req_type, req_id)
    await callback.message.edit_text("Выберите новый статус:", reply_markup=kb)
    await callback.answer()


@admin_assistance_router.callback_query(F.data.startswith("set_status:"))
async def set_status_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    _, req_type, req_id_str, new_status = callback.data.split(":")
    req_id = int(req_id_str)
    await requests_service.update_request_status(req_type, req_id, new_status)
    await callback.answer(f"Статус изменён на {new_status}")
    await callback.message.delete()
    await show_request_detail(callback, state, req_type, req_id)


@admin_assistance_router.callback_query(F.data.startswith("back_to_detail:"))
async def back_to_detail_callback(callback: CallbackQuery, state: FSMContext):
    _, req_type, req_id_str = callback.data.split(":")
    req_id = int(req_id_str)
    await show_request_detail(callback, state, req_type, req_id)


# ------------------------------------------------------------
# 8. Добавление комментария
# ------------------------------------------------------------
@admin_assistance_router.callback_query(F.data.startswith("add_comment:"))
async def add_comment_callback(callback: CallbackQuery, state: FSMContext):
    _, req_type, req_id_str = callback.data.split(":")
    req_id = int(req_id_str)
    msg = await callback.message.answer(
        "✏️ Введите текст комментария (или нажмите «Отмена»):",
        reply_markup=get_cancel_keyboard()
    )
    await state.update_data(
        comment_request_type=req_type,
        comment_request_id=req_id,
        comment_request_message_id=msg.message_id
    )
    await state.set_state(AdminStates.adding_comment)
    await callback.answer()


@admin_assistance_router.message(AdminStates.adding_comment)
async def receive_comment(message: Message, state: FSMContext, bot: Bot):
    if not message.text or message.text.startswith('/'):
        await message.answer("❌ Пожалуйста, отправьте **текстовое** сообщение с комментарием.")
        return
    if message.text == BTN_CANCEL:
        data = await state.get_data()
        request_msg_id = data.get('comment_request_message_id')
        if request_msg_id:
            try:
                await bot.delete_message(message.chat.id, request_msg_id)
            except Exception as e:
                logger.warning(f"Не удалось удалить запрос: {e}")
        await state.set_state(AdminStates.viewing_assistance_detail)
        await message.answer("❌ Отменено.", reply_markup=get_back_keyboard())
        req_type = data.get('comment_request_type')
        req_id = data.get('comment_request_id')
        if req_type and req_id:
            await show_request_detail(message, state, req_type, req_id, bot)
        return

    async with db.session_factory() as session:
        result = await session.execute(
            select(users.c.id).where(users.c.telegram_id == message.from_user.id)
        )
        admin_db_id = result.scalar_one_or_none()
        if not admin_db_id:
            await message.answer("❌ Ошибка: администратор не найден в БД. Напишите /admin")
            return

    data = await state.get_data()
    req_type = data['comment_request_type']
    req_id = data['comment_request_id']
    request_msg_id = data.get('comment_request_message_id')

    if request_msg_id:
        try:
            await bot.delete_message(message.chat.id, request_msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение с запросом: {e}")

    await requests_service.add_comment(req_type, req_id, admin_db_id, message.text)
    await message.answer("✅ Комментарий добавлен.")
    await show_request_detail(message, state, req_type, req_id, bot)


# ------------------------------------------------------------
# 9. Поиск заявки по ID
# ------------------------------------------------------------
@admin_assistance_router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_SEARCH_REQUEST
)
async def start_search_request(message: Message, state: FSMContext):
    await state.set_state(AdminStates.searching_request)
    await message.answer(
        "🔍 Введите ID заявки (число):",
        reply_markup=get_cancel_keyboard()
    )


@admin_assistance_router.message(AdminStates.searching_request)
async def process_search_id(message: Message, state: FSMContext, bot: Bot):
    if message.text == BTN_CANCEL:
        await state.set_state(AdminStates.choosing_mode)
        await message.delete()
        await message.answer(
            "Главное меню администратора:",
            reply_markup=get_admin_main_keyboard()
        )
        return

    if not message.text.isdigit():
        await message.answer("❌ Введите целое число.")
        return

    request_id = int(message.text)
    request = await requests_service.get_request_by_id(request_id)
    if not request:
        await message.answer("❌ Заявка с таким ID не найдена.")
        return

    await state.set_state(AdminStates.viewing_assistance_detail)
    await show_request_detail(
        message,
        state,
        request['request_type'],
        request['id'],
        bot
    )


@admin_assistance_router.callback_query(F.data.startswith("back_to_list:"))
async def back_to_list_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    detail_ids = data.get("detail_message_ids", [])

    for msg_id in detail_ids:
        if msg_id == callback.message.message_id:
            continue
        try:
            await bot.delete_message(callback.message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

    await state.update_data(detail_message_ids=[])
    await state.set_state(AdminStates.viewing_assistance_list)
    await show_requests_list(callback.message, state, bot)

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение с кнопкой: {e}")

    await callback.answer()


@admin_assistance_router.message(
    AdminStates.choosing_mode,
    F.text == BTN_ADMIN_SEARCH_REWARD
)
async def start_search_reward(message: Message, state: FSMContext):
    await state.set_state(AdminStates.searching_reward)
    await message.answer(
        "💰 Введите ID выплаты (число):",
        reply_markup=get_cancel_keyboard()
    )


@admin_assistance_router.message(AdminStates.searching_reward)
async def process_search_reward_id(message: Message, state: FSMContext, bot: Bot):
    if message.text == BTN_CANCEL:
        await state.set_state(AdminStates.choosing_mode)
        await message.delete()
        await message.answer(
            "Главное меню администратора:",
            reply_markup=get_admin_main_keyboard()
        )
        return

    if not message.text.isdigit():
        await message.answer("❌ Введите целое число.")
        return

    reward_id = int(message.text)
    reward = await requests_service.get_reward_by_id(reward_id)
    if not reward:
        await message.answer("❌ Выплата с таким ID не найдена.")
        return

    await state.set_state(AdminStates.viewing_assistance_detail)
    await show_request_detail(
        message,
        state,
        reward['request_type'],  # 'reward'
        reward['id'],
        bot
    )
