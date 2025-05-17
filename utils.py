from datetime import datetime
from typing import List, Literal
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.plan import get_base_plans, get_current_plan, get_user_plans
from keyboards import group_keyboard, personal_keyboard, plan_creation_options_keyboard
import logging

from keyboards.inline import (
    existing_plans_keyboard,
    kb_main_menu,
    kb_plans,
    management_keyboard,
)
from database.models import Comment, Plan
from states.user import UserState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_message_with_keyboard(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode=None,
):
    base_keyboard = (
        group_keyboard()
        if message.chat.type in ["group", "supergroup"]
        else personal_keyboard()
    )

    try:
        if isinstance(reply_markup, InlineKeyboardMarkup):
            await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await message.answer(
                text, reply_markup=base_keyboard, parse_mode=parse_mode
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        await message.answer(text, reply_markup=base_keyboard)


async def show_plan_creation_options(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_plan_name: str | None = get_current_plan(user_id)

    await send_message_with_keyboard(
        message,
        "Выберите действие:",
        reply_markup=plan_creation_options_keyboard(current_plan_name),
    )
    await state.set_state(UserState.choosing_plan_type)


async def show_main_menu(message: Message):
    await send_message_with_keyboard(
        message, "Выберите действие:", reply_markup=kb_main_menu()
    )


async def show_existing_plans(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите тип существующего плана:", reply_markup=existing_plans_keyboard()
    )
    await callback.answer()


async def show_management_menu(message: Message):
    await message.edit_reply_markup(reply_markup=management_keyboard())


def get_plan_comments(comments: List[Comment]) -> str:
    return "\n    💬 ".join(comment.body for comment in comments)


def get_plan_body(plan: Plan) -> str:
    tasks = "\n".join(
        ("✅" if task.checked else " ") + task.body + get_plan_comments(task.comments)
        for task in plan.tasks
    )
    return f"{tasks}"


def get_full_plan(plan: Plan) -> str:
    current_date = datetime.now().strftime("%d.%m.%Y")

    return f"""<b>📅{current_date}
<i>📝{plan.name}</i></b>

{get_plan_body(plan)}
"""


def get_full_current_plan(plan: Plan) -> str:
    return f"<b>Текущий план</b>\n\n{get_full_plan(plan)}"


def get_plan_published_message(plan: Plan, user_name: str) -> str:

    return f"<b><u>{user_name}</u></b> опубликовал(а) свой план на сегодня! 🥳\n\n{get_full_plan(plan)}"


def get_plan_by_type_user_id_plan_id(
    plan_type: Literal["base", "user"], user_id: str | None, plan_id: str
) -> Plan | None:

    if plan_type == "base":
        plans = get_base_plans()
    else:
        plans = get_user_plans(user_id)

    return next((p for p in plans if str(p.id) == plan_id), None)


async def send_welcome_message(message: Message, user_name: str):
    text = (
        f"👋 Привет, {user_name}!\n\n"
        "Я — твой помощник по планированию задач и организации дня.\n"
        "Со мной ты сможешь:\n"
        "- Составлять планы на день\n"
        "- Отслеживать свои задачи\n"
        "- Использовать бот как в личных чатах, так и в группах для совместного планирования\n\n"
        "📋 Доступные команды:\n"
        "/create_plan — Создать новый план\n"
        "/view_plans — Посмотреть свои планы\n"
        "/info — Зачем нужно планирование\n"
        "/help — Показать список всех команд\n\n"
        "В группах доступны:\n"
        "/new_day — Начать новый день\n"
        "/static — Посмотреть статистику группы\n\n"
        "Попробуй создать свой первый план или выбери нужную команду из меню."
    )
    await send_message_with_keyboard(message, text, reply_markup=kb_plans())
