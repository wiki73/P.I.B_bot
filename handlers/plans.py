from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from database import save_user_plan
from keyboards.inline import plan_confirmation_keyboard, plan_management_keyboard, task_marking_keyboard
from states.plans import PlanCreation, PlanManagement
from states.user import UserState
from utils import send_message_with_keyboard, logger, show_management_menu

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

@router.callback_query(F.data.startswith("add_at_"))
async def select_task_position(callback: CallbackQuery, state: FSMContext):
    position = int(callback.data.split('_')[-1])
    await state.update_data(new_task_position=position)
    await callback.message.edit_text("Введите текст нового пункта:")
    await state.set_state(UserState.adding_new_task)
    await callback.answer()

@router.callback_query(F.data == "finish_plan")
async def finish_plan_editing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(task for task in tasks)
    await callback.message.edit_text(
        plan_text + "\n\nХотите опубликовать этот план в группу?",
        reply_markup=plan_confirmation_keyboard()
    )
    await state.set_state(UserState.publishing_plan)
    await callback.answer()


@router.callback_query(UserState.publishing_plan, F.data == "publish_plan")
async def publish_plan(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    group_id = data.get('group_id')
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(task for task in tasks)
    
    await bot.send_message(
        chat_id=group_id,
        text=f"🌅 {callback.from_user.mention_html()} опубликовал свой план на сегодня:\n\n{plan_text}",
        parse_mode="HTML",
        reply_markup=plan_management_keyboard(callback.from_user.id)
    )
    
    await callback.message.edit_text("✅ План успешно опубликован в группу!")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("manage_plan:"))
async def manage_plan_handler(callback: CallbackQuery, state: FSMContext):
    try:
        plan_text = callback.message.text
        lines = plan_text.split('\n')
        
        header = "\n".join(lines[:2])
        tasks = [line.strip() for line in lines[2:] if line.strip()]
        
        await state.update_data({
            'is_new_task': False,
            'header': header,
            'tasks': tasks,
            'message_id': callback.message.message_id,
            'chat_id': callback.message.chat.id
        })
        
        await show_management_menu(callback.message)
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в manage_plan_handler: {e}")
        await callback.answer("Ошибка при обработке плана", show_alert=True)
    finally:
        await callback.answer()

@router.callback_query(PlanManagement.marking_tasks, F.data.startswith("toggle_"))
async def toggle_task_mark(callback: CallbackQuery, state: FSMContext):
    try:
        task_index = int(callback.data.split('_')[1])
        data = await state.get_data()
        tasks = data['tasks']
        
        if task_index >= len(tasks):
            await callback.answer("Неверный номер пункта", show_alert=True)
            return
        
        original_task = tasks[task_index]

        if '✅' in original_task:
            new_task = original_task.replace('✅', '').strip()
        else:
            new_task = f"✅ {original_task.replace('✅', '').strip()}"
        
        if new_task == original_task:
            await callback.answer()
            return
            
        tasks[task_index] = new_task
        await state.update_data({'tasks': tasks})

        try:
            await callback.message.edit_reply_markup(reply_markup=task_marking_keyboard(tasks))
            await callback.answer(f"Пункт {task_index+1} обновлен")
        except:
            await callback.answer()
            
    except Exception as e:
        logger.error(f"Ошибка в toggle_task_mark: {e}")
        await callback.answer("Ошибка при обновлении", show_alert=True)