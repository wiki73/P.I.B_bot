from asyncio.log import logger
from typing import Dict, List, Literal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.callback_data import PlanAction, PlansView
from database.models import Plan, Task

def btn_back(callback_data = "back_to_main"):
    return InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)

def kb_cancel_plan_creation() -> InlineKeyboardMarkup: 
    return InlineKeyboardMarkup(inline_keyboard=[[btn_back()]])

def kb_main_menu() ->InlineKeyboardMarkup: 
    buttons = [
        [InlineKeyboardButton(text="Мои планы", callback_data=PlansView(plan_type='user').pack())],
        [InlineKeyboardButton(text="Базовые планы", callback_data=PlansView(plan_type='base').pack())],
        [InlineKeyboardButton(text="Создать план", callback_data=PlanAction(action='create').pack())],
        [InlineKeyboardButton(text="Текущий план", callback_data=PlanAction(action='current').pack())]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def kb_plans() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Посмотреть текущий план", callback_data="current_plan")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plans_keyboard(plans: List[Plan], type: Literal["base", "user"]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=plan.name, callback_data=f"plan_action:{type}:{plan.id}")]
        for plan in plans 
    ] + [[btn_back()]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_plan_keyboard() -> InlineKeyboardMarkup:
    buttons = [[btn_back()]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def new_day_keyboard(bot_username, chat_id) -> InlineKeyboardMarkup:
    deep_link = f"https://t.me/{bot_username}?start=newday_{chat_id}"

    buttons = [
        [InlineKeyboardButton(text="✨ Создать мой план", url=deep_link)],
        [InlineKeyboardButton( text="❌ Отмена",callback_data="cancel_new_day")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_keyboard() -> InlineKeyboardMarkup:
    buttons = [[btn_back()]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def management_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Отметить пункты", callback_data="mark_tasks"),
        InlineKeyboardButton(text="💬 Комментарии", callback_data="task_comments")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_plan")],
        [InlineKeyboardButton(text="🌙 Завершить день", callback_data="finish_day")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_management")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_creation_options_keyboard(plan_name: str | None = None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📋 Использовать существующий план", callback_data="use_existing_plan")],
        [InlineKeyboardButton(text="✨ Создать новый план", callback_data="create_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ]

    if plan_name:
        buttons.insert(0, [InlineKeyboardButton(text="📌 Использовать текущий план", callback_data="use_current_plan")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_edit_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data=f"finish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_actions_keyboard(plan_name: str, plan_type: Literal["base", "user"], plan_id: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📌 Сделать текущим", callback_data=f"use_plan:{plan_type}:{plan_id}")],
        [btn_back('view_base_plans')]
    ]

    if plan_type == 'user':
        buttons.insert(1, [InlineKeyboardButton(text="🗑 Удалить план", callback_data=f"delete_plan:{plan_type}:{plan_id}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_edit_keyboard(tasks: List[Dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"✏️ Изменить задачу {i+1}", callback_data=f"edit_task_{i}")]
        for i in range(len(tasks))
    ] + [
        [InlineKeyboardButton(text="➕ Добавить пункт", callback_data="add_new_task")],
        [btn_back()]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_position_keyboard(tasks: List[Dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"Добавить после пункта {i+1}", callback_data=f"add_at_{i+1}")]
        for i in range(len(tasks))
    ] + [
        [InlineKeyboardButton(text="Добавить в начало", callback_data="add_at_0")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="edit_tasks")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_marking_keyboard(tasks: List[Task]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for i, task in enumerate(tasks):
        prefix = "✅" if task.checked else f"🟩"
        keyboard.add(InlineKeyboardButton(
            text=f"{prefix} {task.body}",
            callback_data=f"task_action:{i}"
        ))
    
    keyboard.adjust(1)
    keyboard.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_manage"
    ))
    
    return keyboard.as_markup()

def task_comments_keyboard(tasks: List[Task]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for i, task in enumerate(tasks):
        keyboard.add(InlineKeyboardButton(
            text=f"{i+1}. {task.body[:20]}...",
            callback_data=f"comment_task_{i}"
        ))
    
    keyboard.adjust(1)
    keyboard.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_manage"
    ))
    
    return keyboard.as_markup()

def current_plan_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_tasks")],
        [btn_back()]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_editor_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_current_plan")],
        [btn_back()]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_confirmation_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]  
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def existing_plans_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Базовые планы", callback_data="view_base_plans")],
        [InlineKeyboardButton(text="Мои планы", callback_data="view_user_plans")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
         [InlineKeyboardButton(
            text="⚙️ Управление планом",
            callback_data=f"manage_plan:{str(user_id)}"
        )]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def plan_tasks_edit_keyboard (tasks: List[Task]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for i, task in enumerate(tasks):
        builder.row(InlineKeyboardButton(
            text=f'{i+1}. {task.body}',
            callback_data=f"edit_task_{i}"
        ))
    builder.row(InlineKeyboardButton(
            text="➕ Добавить пункт",
            callback_data="add_new_task"
        ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_manage"
    ))

    return builder.as_markup()

def base_plans_keyboard(plans: List[Plan]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for plan in plans:
        builder.add(
            InlineKeyboardButton(
                text=plan.name,
                callback_data=f"select_base_{plan.id}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="← Назад",
            callback_data="back_to_plan_types"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()

def user_plans_keyboard(plans: List[Plan]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for plan in plans:
        builder.add(
            InlineKeyboardButton(
                text=plan.name,
                callback_data=f"plan_action:user:{plan.id}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="← Назад",
            callback_data="back_to_plan_types"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()

def select_plan_keyboard(plan_type: str, plan_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Выбрать этот план",
            callback_data=f"use_plan:{plan_type}:{plan_id}"
        ),
        InlineKeyboardButton(
            text="← Назад",
            callback_data=f"view_{plan_type}_plans"
        )
    )
    builder.adjust(1)
    return builder.as_markup()

