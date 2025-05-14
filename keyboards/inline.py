from typing import Dict, List, Literal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def back_button(callback_data = "back_to_main"):
    return InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)

def cancel_plan_creation_keyboard()->InlineKeyboardMarkup: 
    return InlineKeyboardMarkup(inline_keyboard=[[back_button()]])

def main_menu_keyboard() ->InlineKeyboardMarkup: 
    buttons = [
        [InlineKeyboardButton(text="Мои планы", callback_data="view_user_plans")],
        [InlineKeyboardButton(text="Базовые планы", callback_data="view_base_plans")],
        [InlineKeyboardButton(text="Создать план", callback_data="create_plan")],
        [InlineKeyboardButton(text="Текущий план", callback_data="current_plan")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def help_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Посмотреть текущий план", callback_data="current_plan")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plans_keyboard(plans: List[Dict], type: Literal["base", "user"]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:{type}:{plan['id']}")]
        for plan in plans 
    ] + [[back_button()]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_plan_keyboard() -> InlineKeyboardMarkup:
    buttons = [[back_button()]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def new_day_keyboard(bot_username, chat_id) -> InlineKeyboardMarkup:
    deep_link = f"https://t.me/{bot_username}?start=newday_{chat_id}"

    buttons = [
        [InlineKeyboardButton(text="✨ Создать мой план", url=deep_link)],
        [InlineKeyboardButton( text="❌ Отмена",callback_data="cancel_new_day")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_keyboard() -> InlineKeyboardMarkup:
    buttons = [[back_button()]]

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
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_actions_keyboard(plan_name: str, plan_type: Literal["base", "user"], plan_id: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📌 Сделать текущим", callback_data=f"set_current_plan:{plan_name}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_plan_types")]
    ]

    if plan_type == 'user':
        buttons.insert(1, [InlineKeyboardButton(text="🗑 Удалить план", callback_data=f"confirm_delete_plan:{plan_type}:{plan_id}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_edit_keyboard(tasks: List[Dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"✏️ Изменить задачу {i+1}", callback_data=f"edit_task_{i}")]
        for i in range(len(tasks))
    ] + [
        [InlineKeyboardButton(text="➕ Добавить пункт", callback_data="add_new_task")],
        [back_button()]
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

def task_marking_keyboard(tasks: List[Dict]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for i, task in enumerate(tasks):
        clean_task = task.replace('✅', '').strip()
        prefix = "✓ " if '✅' in task else f"{i+1}."
        keyboard.add(InlineKeyboardButton(
            text=f"{prefix} {clean_task}",
            callback_data=f"toggle_{i}"
        ))
    
    keyboard.adjust(1)
    keyboard.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_manage"
    ))
    
    return keyboard.as_markup()

def task_comments_keyboard(tasks: List[Dict]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for i, task in enumerate(tasks):
        clean_task = task.replace('✅', '').strip()
        keyboard.add(InlineKeyboardButton(
            text=f"{i+1}. {clean_task[:20]}...",
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
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_current_plan")]
        [back_button()]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_editor_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_current_plan")]
        [back_button()]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_confirmation_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]  
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)