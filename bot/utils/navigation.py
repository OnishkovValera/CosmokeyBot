from aiogram.fsm.context import FSMContext
from loguru import logger

STACK_KEY = "navigation_stack"


class GiftSteps:
    GET_GIFT = "get_gift"
    CHECK_SUBSCRIPTION = "check_subscription"
    CHANNEL_LINK = "channel_link"
    NOT_SUBSCRIBED = "not_subscribed"


async def push_state(state: FSMContext, step: str):
    logger.log("INFO", f"User {await state.get_data()} pushed state {step}")
    data = await state.get_data()
    stack = data.get(STACK_KEY, [])
    stack.append(step)
    logger.log("INFO", f"Current stack: {stack}")
    await state.update_data(**{STACK_KEY: stack})


async def pop_state(state: FSMContext) -> str | None:
    data = await state.get_data()
    logger.log("INFO", f"User {await state.get_data()} popped state, current stack before pop: {data.get(STACK_KEY, [])}")
    stack = data.get(STACK_KEY, [])

    if not stack:
        return None

    element = stack.pop()

    if not stack:
        await state.update_data(**{STACK_KEY: []})
        return None

    await state.update_data(**{STACK_KEY: stack})
    return element


async def get_current_step(state: FSMContext) -> str | None:
    data = await state.get_data()
    stack = data.get(STACK_KEY, [])
    return stack.pop() if stack else None

async def clear_stack(state: FSMContext):
    await state.update_data(**{STACK_KEY: []})