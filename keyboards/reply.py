from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def personal_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="/start"), KeyboardButton(text="/help")],
        [KeyboardButton(text="/info"), KeyboardButton(text="/create_plan")],
        [KeyboardButton(text="/view_plans")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, is_persistent=True
    )


def group_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="/new_day"), KeyboardButton(text="/static")],
        [KeyboardButton(text="/help")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, is_persistent=True
    )
