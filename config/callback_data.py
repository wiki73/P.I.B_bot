from aiogram.filters.callback_data import CallbackData
from typing import Literal

PlanType = Literal["base", "user", "current"]

class PlanAction(CallbackData, prefix="plan_action"):
    action: Literal["create", "current", "use", "view", "delete", "edit", "manage", "finish"]
    plan_type: PlanType | None = None
    plan_id: str | None = None

class PlansView(CallbackData, prefix="plans_view"):
    plan_type: PlanType

class TaskAction(CallbackData, prefix="task_action"):
    action: Literal["edit", "add", "toggle", "add_after"]
    task_index: int | None = None

class ManageAction(CallbackData, prefix="manage"):
    action: Literal["back", "close"]

class NewDayAction(CallbackData, prefix="newday"):
    action: Literal["cancel"]

class MainMenuAction(CallbackData, prefix="main"):
    action: Literal["back"]
