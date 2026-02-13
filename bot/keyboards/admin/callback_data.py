from aiogram.filters.callback_data import CallbackData

class AdminModeCD(CallbackData, prefix="admin_mode"):
    mode: str

class AssistanceTypeCD(CallbackData, prefix="assist_type"):
    type: str

class ProcessRequestCD(CallbackData, prefix="process"):
    request_type: str
    request_id: int
    msg_ids: str