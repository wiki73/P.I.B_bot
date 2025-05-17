from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database.user import get_user_by_telegram_id, save_user
from keyboards.inline import kb_plans
from utils import logger, send_welcome_message
from states import UserState
from utils import show_plan_creation_options, send_message_with_keyboard, show_main_menu

router = Router()

@router.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    args = message.text.split()[1:]
    logger.info('/start args: ' + str(args))
    if len(args) > 0:
        group_id = int(args[0].split('_')[1])
        logger.info(f'Setting group_id: {group_id}')
        await state.update_data(group_id=group_id)
        await state.set_state(UserState.choosing_plan_type)
        await show_plan_creation_options(message, state)
    else:
        user_id = message.from_user.id
        logger.info(f'Processing start command for user {user_id}')
        user = get_user_by_telegram_id(user_id)
        logger.info(f'Found user: {user}')
        
        if user is None:
            logger.info('User not found, creating user')
        user = save_user(user_id, message.from_user.full_name)
        logger.info(f'User exists: {user.name}')
        await send_welcome_message(message, message.from_user.full_name)

@router.message(Command('help'))
async def help_command(message: types.Message):
    if message.chat.type == "private":
        help_text = (
            "Личные команды:\n"
            "/start - Начало работы\n"
            "/help - Показать это сообщение\n"
            "/info - О планировании\n"
            "/create_plan - Создать новый план\n"
            "/view_plans - Посмотреть планы"
        )

        await send_message_with_keyboard(message, help_text, reply_markup=kb_plans())
    else:
        await send_message_with_keyboard(
            message,
            "Групповые команды:\n"
            "/new_day - Начать день\n"
            "/static - Статистика"
        )

@router.message(Command('info'))
async def info_command(message: Message):
    info_text = (
        "Планирование помогает:\n\n"
        "1. Избежать суеты в течение дня\n"
        "2. Освободить время для отдыха\n"
        "3. Развивать дисциплину\n\n"
        "Попробуйте создать свой первый план!"
    )
    await send_message_with_keyboard(message, info_text)

@router.message()
async def handle_any_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f'Received message: "{message.text}" in state: {current_state}')
    
    if current_state is None:
        await send_message_with_keyboard(
            message,
            "Используйте кнопки меню или команды:"
        )
