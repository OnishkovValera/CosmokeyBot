from typing import Any

from aiogram.fsm.context import FSMContext

STATE_STACK_KEY = "state_stack"

async def push_state(state: FSMContext):
    data: dict[str, Any] = await state.get_data()
    stack = data.get(STATE_STACK_KEY, [])
    current_state = await state.get_state()
