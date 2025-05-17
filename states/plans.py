from aiogram.fsm.state import State, StatesGroup


class PlanCreation(StatesGroup):
    waiting_for_title = State()
    waiting_for_tasks = State()
    waiting_for_confirmation = State()


class PlanManagement(StatesGroup):
    managing_plan = State()
    marking_tasks = State()
    adding_comment = State()
    editing_task = State()
    adding_task = State()
    waiting_for_study_time = State()


class PlanView(StatesGroup):
    viewing_plans = State()
