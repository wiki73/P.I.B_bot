from aiogram.types import  Message, InlineKeyboardMarkup
from keyboards import group_keyboard, personal_keyboard
import logging

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