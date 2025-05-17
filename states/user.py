from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_plan_title = State()
    waiting_for_plan_tasks = State()
    waiting_for_base_plan_choice = State()
    waiting_for_confirm = State()
    editing_plan = State()
    choosing_plan_type = State()
    selecting_existing_plan = State()
    creating_new_plan = State()
    publishing_plan = State()
    adding_new_task = State()
