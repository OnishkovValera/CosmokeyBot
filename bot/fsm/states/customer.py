from aiogram.fsm.state import StatesGroup, State


class GiftStates(StatesGroup):
    waiting_subscription_check = State()


class ReviewStates(StatesGroup):
    WAITING_FOR_READY = State()
    WAITING_FOR_PHOTO = State()
    WAITING_FOR_LINK = State()


class FeedbackStates(StatesGroup):
    WAITING_FOR_MEDIA = State()
    CHOOSING_CATEGORY = State()
    WAITING_FOR_TEXT = State()
