from aiogram.fsm.state import StatesGroup, State


class SpecialPostState(StatesGroup):
    WAITING_FOR_POST = State()


class AdminStates(StatesGroup):
    choosing_mode = State()
    choosing_assistance_type = State()
    viewing_assistance = State()
    viewing_rewards = State()
    editing_texts_list = State()
    waiting_new_text = State()
