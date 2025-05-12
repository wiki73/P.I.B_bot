from aiogram.types import  InlineKeyboardButton

def add_back_button(keyboard_list: list, callback_data: str = "back_to_main") -> list:
    keyboard_list.append([InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)])
    return keyboard_list