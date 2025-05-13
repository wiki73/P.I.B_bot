from aiogram.types import  Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from database import get_current_plan
from keyboards import group_keyboard, personal_keyboard, plan_creation_options_keyboard
import logging

from keyboards.inline import main_menu_keyboard
from states.user import UserState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_message_with_keyboard(message: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None, parse_mode=None):
    base_keyboard = group_keyboard() if message.chat.type in ["group", "supergroup"] else personal_keyboard()
    
    try:
        if isinstance(reply_markup, InlineKeyboardMarkup):
            await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await message.answer(text, reply_markup=base_keyboard, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        await message.answer(text, reply_markup=base_keyboard)

async def show_plan_creation_options(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_plan_name: str | None = get_current_plan(user_id)
    
    await send_message_with_keyboard(
        message,
        "Выберите действие:",
        reply_markup=plan_creation_options_keyboard(current_plan_name)
    )
    await state.set_state(UserState.choosing_plan_type)

async def show_main_menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())