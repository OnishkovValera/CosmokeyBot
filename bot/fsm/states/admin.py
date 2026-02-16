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
    waiting_info_post = State()
    editing_texts = State()
    viewing_rewards_list = State()
    viewing_rewards_detail = State()
    choosing_assistance_status = State()
    viewing_assistance_list = State()
    viewing_assistance_detail = State()
    adding_comment = State()
    searching_request = State()
    viewing_stats = State()
    mailing_text = State()
    mailing_confirm = State()
    viewing_users_list = State()
    choosing_rewards_status = State()
    mailing_content = State()
    searching_reward = State()
