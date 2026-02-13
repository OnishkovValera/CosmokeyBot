from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from bot.filters.is_admin import IsAdmin
from bot.fsm.states.admin import AdminStates
from bot.keyboards.admin.admin_menu import (
    get_assistance_type_keyboard,
    BTN_ASSISTANCE_DEFECT,
    BTN_ASSISTANCE_COMPLAINT,
    BTN_ASSISTANCE_FEEDBACK,
    get_admin_done_keyboard,
    BTN_ADMIN_DONE, get_admin_mode_keyboard,
)
from bot.keyboards.admin.callback_data import ProcessRequestCD
from bot.services.admin import admin_service

assistance_router = Router()
assistance_router.message.filter(IsAdmin())
assistance_router.callback_query.filter(IsAdmin())


# ------------------------------------------------------------------
# Шаг 1: показать reply‑клавиатуру с типами обращений
# ------------------------------------------------------------------
async def start_assistance(message: Message, state: FSMContext):
    await message.answer(
        "Выберите тип обращения:",
        reply_markup=get_assistance_type_keyboard()
    )


# ------------------------------------------------------------------
# Шаг 2: выбран тип – запоминаем, переходим к просмотру заявок
# ------------------------------------------------------------------
@assistance_router.message(
    AdminStates.choosing_assistance_type,
    F.text.in_([BTN_ASSISTANCE_DEFECT, BTN_ASSISTANCE_COMPLAINT, BTN_ASSISTANCE_FEEDBACK])
)
async def select_assistance_type(message: Message, state: FSMContext):
    # Определяем тип обращения (соответствует значениям в БД)
    if message.text == BTN_ASSISTANCE_DEFECT:
        req_type = "defect"
    elif message.text == BTN_ASSISTANCE_COMPLAINT:
        req_type = "complaint"
    else:
        req_type = "feedback"

    await state.update_data(assistance_type=req_type)
    await state.set_state(AdminStates.viewing_assistance)
    await show_assistance_requests(message, state, message.bot)

async def show_assistance_requests(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    req_type = data["assistance_type"]
    requests = await admin_service.get_pending_assistance_requests(req_type, limit=10)

    if not requests:
        # ✅ Возвращаем в выбор типа или в главное меню?
        # Лучше сразу в главное меню админки
        await state.set_state(AdminStates.choosing_mode)
        await message.answer(
            "✅ Нет необработанных обращений данного типа.\n"
            "Выберите режим работы:",
            reply_markup=get_admin_mode_keyboard()
        )
        return

    await message.answer(
        f"📨 Найдено {len(requests)} обращений. Отправляю...",
        reply_markup=get_admin_done_keyboard()
    )

    for req in requests:
        media = await admin_service.get_media_for_request("assistance", req["id"])
        await admin_service.send_request_to_admin(
            bot,
            message.chat.id,
            "assistance",
            req,
            media,
            state
        )
    await message.answer("⚠️ Все заявки показаны. Нажмите «Закончить» для выхода.")


# ------------------------------------------------------------------
# Обработка инлайн‑кнопки «Обработано» (callback_data)
# ------------------------------------------------------------------
@assistance_router.callback_query(
    StateFilter(AdminStates.viewing_assistance),
    ProcessRequestCD.filter(F.request_type == "assistance")
)
async def process_assistance_done(
        callback: CallbackQuery,
        callback_data: ProcessRequestCD,
        state: FSMContext
):
    await callback.answer("Обращение помечено как обработанное.")
    await admin_service.mark_request_processed("assistance", callback_data.request_id)

    # Удаляем сообщения, относящиеся к этой заявке
    msg_ids = list(map(int, callback_data.msg_ids.split(",")))
    await admin_service.delete_admin_messages(callback.bot, callback.message.chat.id, msg_ids)

    # Убираем ID заявки из сохранённых в state
    data = await state.get_data()
    sent_map = data.get("sent_messages", {})
    sent_map.pop(str(callback_data.request_id), None)
    await state.update_data(sent_messages=sent_map)


# ------------------------------------------------------------------
# Завершение сессии – кнопка «🚫 Закончить» (reply)
# ------------------------------------------------------------------
@assistance_router.message(AdminStates.viewing_assistance, F.text == BTN_ADMIN_DONE)
async def finish_assistance_session(message: Message, state: FSMContext):
    # 1. Удаляем все сообщения, отправленные в рамках этой сессии
    data = await state.get_data()
    sent_map = data.get("sent_messages", {})
    for msg_ids in sent_map.values():
        await admin_service.delete_admin_messages(message.bot, message.chat.id, msg_ids)

    # 2. Полностью сбрасываем состояние
    await state.clear()

    # 3. Устанавливаем состояние выбора режима и показываем главную админ-клавиатуру
    await state.set_state(AdminStates.choosing_mode)
    await message.answer(
        "✅ Сессия обращений завершена.\n"
        "Выберите новый режим работы:",
        reply_markup=get_admin_mode_keyboard()
    )