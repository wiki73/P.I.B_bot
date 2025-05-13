from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database import save_user_plan
from states.plans import PlanCreation
from utils import send_message_with_keyboard, logger

router = Router()

@router.message(Command('create_plan'))
async def create_plan_command(message: types.Message, state: FSMContext):
    logger.info(f"Create plan command received, current state: {await state.get_state()}")

    if message.chat.type == "private":
        await send_message_with_keyboard(
            message,
            "📝 Давайте создадим новый план.\n"
            "Введите название для вашего плана:"
        )
        await state.set_state(PlanCreation.waiting_for_title)
        logger.info(f"New state set: {await state.get_state()}")
    else:
        await send_message_with_keyboard(
            message,
            "Эта команда доступна только в личном чате с ботом."
        )

@router.message(PlanCreation.waiting_for_title)
async def process_plan_title(message: types.Message, state: FSMContext):
    logger.info('Title processing triggered')
    await state.update_data(title=message.text)
    await message.answer(
        "✏️ Теперь введите задачи для плана (каждая задача с новой строки):\n\n"
        "Пример:\n"
        "1. Зарядка\n"
        "2. Завтрак\n"
        "3. Работа над проектом"
    )
    await state.set_state(PlanCreation.waiting_for_tasks)

@router.message(PlanCreation.waiting_for_tasks)
async def process_plan_tasks(message: types.Message, state: FSMContext):
    tasks = message.text.split('\n')
    data = await state.get_data()
    
    formatted_tasks = "\n".join(task.strip() for task in tasks if task.strip())
    
    await state.update_data(tasks=formatted_tasks)
    
    preview = (
        f"📋 <b>{data['title']}</b>\n\n"
        f"{formatted_tasks}\n\n"
        "Всё верно? (да/нет)"
    )
    
    await send_message_with_keyboard(message, preview, parse_mode='HTML')
    await state.set_state(PlanCreation.waiting_for_confirmation)

@router.message(PlanCreation.waiting_for_confirmation, F.text.lower().in_(['да', 'нет']))
async def confirm_plan(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        data = await state.get_data()
        user_id = message.from_user.id
        
        save_user_plan(
            user_id=user_id,
            name=data['title'],
            text=data['tasks']
        )
        
        await send_message_with_keyboard(
            message,
            f"✅ План <b>{data['title']}</b> успешно сохранён!\n"
            "Теперь вы можете использовать его в своём расписании.",
            parse_mode='HTML'
        )
    else:
        await send_message_with_keyboard(
            message,
            "Создание плана отменено.\n"
            "Если хотите начать заново, введите /create_plan"
        )
    
    await state.clear()

@router.message(PlanCreation.waiting_for_confirmation)
async def wrong_confirmation(message: Message):
    await send_message_with_keyboard(message, "Пожалуйста, ответьте 'да' или 'нет'")