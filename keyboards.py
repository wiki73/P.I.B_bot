from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from database import get_base_plan
from utils import add_back_button

cancel_plan_creation_keyboard = InlineKeyboardMarkup(inline_keyboard=add_back_button([], "back_to_main"))

personal_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start"), KeyboardButton(text="/help")],
        [KeyboardButton(text="/info"), KeyboardButton(text="/create_plan")],
        [KeyboardButton(text="/view_plans")]
    ],
    resize_keyboard=True,
    is_persistent=True
)

group_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/new_day"), KeyboardButton(text="/static")],
        [KeyboardButton(text="/help")]
    ],
    resize_keyboard=True,
    is_persistent=True
)

main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои планы", callback_data="view_user_plans")],
        [InlineKeyboardButton(text="Базовые планы", callback_data="view_base_plans")],
        [InlineKeyboardButton(text="Создать план", callback_data="create_plan")],
        [InlineKeyboardButton(text="Текущий план", callback_data="current_plan")]
    ])

help_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть текущий план", callback_data="current_plan")]
    ])

def get_view_base_plans_keyboard(plans):
    if not plans:
        return InlineKeyboardMarkup(inline_keyboard=add_back_button([], "back_to_main"))

    return InlineKeyboardMarkup(inline_keyboard=add_back_button([
        [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:base:{plan['id']}")]
        for plan in plans
    ], "back_to_main"))

def get_new_day_keyboard(bot_username, chat_id): 
    deep_link = f"https://t.me/{bot_username}?start=newday_{chat_id}"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✨ Создать мой план",
            url=deep_link
        )],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_new_day"
        )]
    ])