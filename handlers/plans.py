from datetime import datetime
from typing import List
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from database.plan import create_user_plan, get_base_plans, get_current_plan, get_user_plans, set_current_plan
from keyboards.inline import back_keyboard, current_plan_keyboard, existing_plans_keyboard, main_menu_keyboard, management_keyboard, new_day_keyboard, plan_actions_keyboard, plan_confirmation_keyboard, plan_edit_keyboard, plan_editor_keyboard, plan_management_keyboard, plan_tasks_edit_keyboard, plans_keyboard, task_comments_keyboard, task_edit_keyboard, task_marking_keyboard, base_plans_keyboard, task_position_keyboard, user_plans_keyboard, select_plan_keyboard
from models import Plan, Task
from states.plans import PlanCreation, PlanManagement, PlanView
from states.user import UserState
from utils import get_full_plan, get_plan_body, send_message_with_keyboard, logger, show_existing_plans, show_management_menu

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
async def confirm_plan(message: Message, state: FSMContext):
    if message.text.lower() == 'да':
        data = await state.get_data()
        user_id = message.from_user.id
        
        create_user_plan(
            user_id=user_id,
            name=data['title'],
            tasks_text=data['tasks']
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
    plan = data.get('plan')

    await callback.message.edit_text(
        get_full_plan(plan) + "\n\nХотите опубликовать этот план в группу?",
        reply_markup=plan_confirmation_keyboard()
    )
    await state.set_state(UserState.publishing_plan)
    await callback.answer()


@router.callback_query(UserState.publishing_plan, F.data == "publish_plan")
async def publish_plan(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logger.info('PUBLISH_PLAN')

    data = await state.get_data()
    plan_name = data.get('plan_name')
    tasks = data.get('tasks')
    

    logger.info('data: ' + str(data))
    await state.update_data(plan = {
        'name': plan_name,
        'tasks': tasks,
        'owner_id': callback.from_user.id,
        'owner_mention': callback.from_user.mention_html(),
    })
    current_date = datetime.now().strftime("%d.%m.%Y")
    tasks_text = "\n".join(task for task in tasks)
    formatted_plan = f"""
📅 {current_date}
📋 {plan_name}

{tasks_text}"""
    text = f"🌅 <strong>{callback.from_user.mention_html()} опубликовал свой план на сегодня:</strong>\n{formatted_plan}"
    user_id = callback.from_user.id

    await bot.send_message(
        chat_id=data.get('group_id'),
        text=text,
        parse_mode="HTML",
        reply_markup=plan_management_keyboard(user_id)
    )
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

@router.callback_query(F.data == "cancel_plan_creation")
async def handle_cancel_plan_creation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    group_id = data.get('group_id')
    
    if group_id:
        await callback.message.edit_text(
            f"❌ {callback.from_user.mention_html()} отменил создание плана.",
            parse_mode="HTML"
        )
        try:
            await bot.send_message(
                chat_id=group_id,
                text=f"❌ {callback.from_user.mention_html()} отменил создание плана.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в группу: {e}")
    else:
        await callback.message.edit_text(
            "Создание плана отменено.",
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "view_base_plans")
async def handle_show_base_plans(callback: CallbackQuery):
    base_plans = get_base_plans()
    callback_message = "Выберите базовый план:"
    
    if not base_plans:
        callback_message = "Базовые планы не найдены."

    await callback.message.edit_text(callback_message, reply_markup=plans_keyboard(base_plans, 'base'))
    await callback.answer()

@router.callback_query(F.data.startswith("plan_action:"))
async def handle_plan_action(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    _, plan_type, plan_id = callback.data.split(':')
    
    if plan_type == 'base':
        plans = get_base_plans()
    else:
        plans = get_user_plans(callback.from_user.id)
    
    selected_plan = next((p for p in plans if str(p.id) == plan_id), None)
    if not selected_plan:
        await callback.answer("План не найден!")
        return
    
    if current_state == 'UserState:selecting_existing_plan':
        current_date = datetime.now().strftime("%d.%m.%Y")
        plan_header = f"📅 {current_date}\n📋 {selected_plan.name}\n\n"
        
        tasks = [task.body for task in selected_plan.tasks]
        
        await state.update_data(
            is_new_plan=False,
            selected_plan_id=selected_plan.id,
            tasks=tasks,
            plan_name=selected_plan.name,
            header=selected_plan.name,
            current_date=current_date
        )
        
        plan_text = plan_header + "\n".join(task for task in tasks)
        await callback.message.edit_text(plan_text, reply_markup=plan_edit_keyboard())
    else:
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        await callback.message.edit_text(
            f"📅 {current_date}\n"
            f"✅ План <b>{selected_plan.name}</b>\n\n"
            f"Содержание:\n{get_plan_body(selected_plan)}",
            parse_mode='HTML',
            reply_markup=plan_actions_keyboard(selected_plan.name, plan_type, str(selected_plan.id))
        )
    
    await callback.answer()

@router.callback_query(UserState.selecting_existing_plan, F.data.startswith('select_user_'))
async def select_user_plan_for_new_day(callback: CallbackQuery, state: FSMContext):
    await show_user_plans(callback, state)

@router.callback_query(UserState.selecting_existing_plan, F.data.in_(["select_base_plans", "select_user_plans", "cancel_plan_creation"]))
async def handle_existing_plan_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data == "select_base_plans":
        plans = get_base_plans()
        await callback.message.edit_text(
            "Выберите базовый план:",
            reply_markup=plans_keyboard(plans, 'base')
        )
    elif callback.data == "select_user_plans":
        plans = get_user_plans(callback.from_user.id)
        if not plans:
            await callback.message.edit_text("У вас пока нет сохраненных планов.")
            return
        
        await callback.message.edit_text(
            "Выберите ваш план:",
            reply_markup=plans_keyboard(plans, 'user')
        )
    elif callback.data == "cancel_plan_creation":
        await handle_cancel_plan_creation(callback, state)
    
    await callback.answer()

@router.message(UserState.creating_new_plan)
async def process_new_day_plan_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await send_message_with_keyboard(
        message,
        "✏️ Теперь введите задачи для плана (каждая задача с новой строки):\n\n"
        "Пример:\n"
        "Зарядка\n"
        "Завтрак\n"
        "Работа над проектом"
    )
    await state.set_state(UserState.waiting_for_plan_tasks)

@router.message(UserState.waiting_for_plan_tasks)
async def process_new_day_plan_tasks(message: Message, state: FSMContext):
    data = await state.get_data()
    tasks = message.text.split('\n')
    current_date = data.get('current_date')
    plan_name = data.get('title')
    
    await state.update_data(
        tasks=tasks,
        plan_name=plan_name
    )
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(task for task in tasks)
    await send_message_with_keyboard(message, plan_text, reply_markup=plan_edit_keyboard())
    await state.set_state(UserState.editing_plan)

@router.callback_query(F.data == 'current_plan')
async def show_current_plan(callback: CallbackQuery):
    user_id = callback.from_user.id
    plan = get_current_plan(user_id)
    
    if not plan:
        await callback.message.edit_text("У вас нет активного плана.", reply_markup=back_keyboard())
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📋 Текущий план: {plan.name}\n\n{get_plan_body(plan)}",
        reply_markup=current_plan_keyboard()
    )
    await callback.answer()

@router.message(Command('view_plans'))
async def view_plans_command(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await send_message_with_keyboard(
            message,
            "Эта команда доступна только в личном чате с ботом."
        )
        return

    
    await send_message_with_keyboard(
        message,
        "📂 Выберите тип планов для просмотра:",
        reply_markup=existing_plans_keyboard()
    )
    await state.set_state(PlanView.viewing_plans)


@router.callback_query(F.data == "view_base_plans", PlanView.viewing_plans)
async def show_base_plans(callback: types.CallbackQuery):
    base_plans = get_base_plans()
    
    if not base_plans:
        await callback.message.edit_text("Базовые планы не найдены.")
        return
    
    await callback.message.edit_text(
        "📚 Доступные базовые планы:",
        reply_markup=base_plans_keyboard(base_plans)
    )
    await callback.answer()

@router.callback_query(F.data == "view_user_plans", PlanView.viewing_plans)
async def show_user_plans(callback: types.CallbackQuery, state: FSMContext):
    user_plans = get_user_plans(callback.from_user.id)
    if not user_plans:
        await callback.message.answer("У вас пока нет сохраненных планов.")
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📁 Ваши сохраненные планы:",
        reply_markup=user_plans_keyboard(user_plans)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_plan_types")
async def back_to_plan_types(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📂 Выберите тип планов для просмотра:",
        reply_markup=existing_plans_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("select_plan:"))
async def select_plan(callback: types.CallbackQuery):
    _, plan_type, plan_id = callback.data.split(':')
    
    if plan_type == "base":
        plans = get_base_plans()
    else:
        plans = get_user_plans(callback.from_user.id)
    
    selected_plan = next((p for p in plans if str(p.id) == plan_id), None)
    
    if not selected_plan:
        await callback.answer("План не найден!")
        return
    
    plan_text = get_plan_body(selected_plan)
    await callback.message.edit_text(
        f"📋 <b>{selected_plan.name}</b>\n\n"
        f"{plan_text}\n\n"
        "Вы можете выбрать этот план как текущий:",
        parse_mode='HTML',
        reply_markup=select_plan_keyboard(plan_type, plan_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("use_plan:"))
async def use_plan(callback: types.CallbackQuery):
    logger.info(callback.data)
    _, plan_type, plan_id = callback.data.split(':')
    logger.info('plan_type ' + plan_type + "plan_id" + plan_id)
    
    if plan_type == "base":
        plans = get_base_plans()
    else:
        plans = get_user_plans(callback.from_user.id)
    
    selected_plan = next((p for p in plans if str(p.id) == plan_id), None)
    
    if not selected_plan:
        await callback.answer("План не найден!")
        return
    
    set_current_plan(callback.from_user.id, selected_plan.id)
    plan_text = get_plan_body(selected_plan)
    
    await callback.message.edit_text(
        f"✅ План <b>{selected_plan.name}</b> теперь ваш текущий план!\n\n"
        f"Содержание:\n{plan_text}",
        parse_mode='HTML'
    )
    await callback.answer()

@router.message(Command('new_day'), F.chat.type.in_({"group", "supergroup"}))
async def new_day_group(message: Message, state: FSMContext, bot: Bot):
    try:
        bot_username = (await bot.get_me()).username
        await state.update_data(group_id=message.chat.id)
        await send_message_with_keyboard(
            message,
            f"🌅 {message.from_user.mention_html()} начинает новый день!\n"
            "Нажмите кнопку ниже, чтобы создать личный план ↓",
            reply_markup=new_day_keyboard(bot_username, message.chat.id),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в new_day_group: {e}")
        await send_message_with_keyboard(message, "Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data == "cancel_new_day")
async def cancel_new_day(callback: CallbackQuery):
    await send_message_with_keyboard(
        callback.message,
        f"❌ {callback.from_user.mention_html()} отменил создание плана.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(UserState.choosing_plan_type)
async def handle_plan_type_choice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if callback.data == "use_existing_plan":
        await show_existing_plans(callback)
        await state.set_state(UserState.selecting_existing_plan)
    elif callback.data == "create_new_plan":
        current_date = datetime.now().strftime("%d.%m.%Y")
        data['current_date'] = current_date
        await state.set_data(data)
        await callback.message.edit_text("📝 Введите название для нового плана на сегодня:")
        await state.set_state(UserState.creating_new_plan)
    elif callback.data == "use_current_plan":
        user_id = callback.from_user.id
        plan = get_current_plan(user_id)
        
        if not plan:
            await callback.message.edit_text("Ошибка: текущий план не найден.")
            await callback.answer()
            return
        
        plan_body = get_plan_body(plan)
        
        current_date = datetime.now().strftime("%d.%m.%Y")
        plan_header = f"📅 {current_date}\n📋 {plan.name}\n\n"
        
        tasks = plan_body.split('\n')
        
        data.update({
            'tasks': tasks,
            'plan_name': plan.name,
            'current_date': current_date
        })
        await state.set_data(data)
        
        plan_body = plan_header + "\n".join(task for task in tasks)

        await callback.message.edit_text(plan_body, reply_markup=plan_edit_keyboard())
        await state.set_state(UserState.editing_plan)
    elif callback.data == "cancel_plan_creation":
        await handle_cancel_plan_creation(callback, state)
    
    await callback.answer()

@router.callback_query(F.data == "edit_tasks")
async def start_task_editing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n"
    plan_text += "Текущие задачи:\n" + "\n".join(task for task in tasks)
    plan_text += "\n\nВыберите действие:"
    
    await state.update_data({
            'tasks': tasks,
            'message_id': callback.message.message_id,
            'chat_id': callback.message.chat.id
        })
    await callback.message.edit_text(plan_text, reply_markup=task_edit_keyboard(tasks))
    await state.set_state(UserState.editing_plan)
    await callback.answer()

@router.callback_query(F.data == "add_new_task")
async def add_new_task(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    
    await callback.message.edit_text(
        "Выберите, куда добавить новый пункт:",
        reply_markup=task_position_keyboard(tasks)
    )
    await callback.answer()

@router.callback_query(PlanManagement.managing_plan, F.data == "mark_tasks")
async def start_marking_tasks(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        tasks = data['tasks']
        
        keyboard = task_marking_keyboard(tasks)
        
        await callback.message.edit_text(
            "Выберите пункты для отметки:\n(✓ - отмеченные)",
            reply_markup=keyboard
        )
        await state.set_state(PlanManagement.marking_tasks)
    except Exception as e:
        logger.error(f"Ошибка в start_marking_tasks: {e}")
        await callback.answer("Ошибка при загрузке задач", show_alert=True)
    finally:
        await callback.answer()

@router.callback_query(PlanManagement.managing_plan, F.data == "task_comments")
async def task_comments_handler(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        tasks = data['tasks']
        
        await callback.message.edit_text(
            "Выберите пункт для добавления комментария:",
            reply_markup=task_comments_keyboard(tasks)
        )
    except Exception as e:
        logger.error(f"Ошибка в task_comments_handler: {e}")
        await callback.answer("Ошибка при загрузке задач", show_alert=True)
    finally:
        await callback.answer()

@router.callback_query(F.data == "back_to_manage")
async def back_to_management(callback: CallbackQuery, state: FSMContext):
    logger.info('BACK_TO_MANAGEMENT')
    try:
        data = await state.get_data()
        header = data['header']
        tasks = data['tasks']
        
        full_plan = f"{header}\n" + "\n".join(tasks)
        await callback.message.edit_text(
            full_plan,
            reply_markup=management_keyboard()
        )
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в back_to_management: {e}")
        await callback.answer("Ошибка при возврате", show_alert=True)
    finally:
        await callback.answer()

@router.callback_query(PlanManagement.managing_plan, F.data == "close_management")
async def close_management(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в close_management: {e}")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("comment_task_"))
async def select_task_for_comment(callback: CallbackQuery, state: FSMContext):
    try:
        task_index = int(callback.data.split('_')[2])
        await state.update_data({'commenting_task': task_index})
        await callback.message.edit_text(
            f"Введите комментарий для пункта {task_index+1}:\n"
            "(или отправьте /cancel для отмены)"
        )
        await state.set_state(PlanManagement.adding_comment)
    except Exception as e:
        logger.error(f"Ошибка в select_task_for_comment: {e}")
        await callback.answer("Ошибка при выборе задачи", show_alert=True)
    finally:
        await callback.answer()

@router.message(PlanManagement.adding_comment, F.text)
async def process_comment(message: Message, state: FSMContext):
    logger.info('PROCESS_COMMENT')
    try:
        if message.text.startswith('/'):
            await message.answer("Действие отменено")
            await show_management_menu(message)
            await state.set_state(PlanManagement.managing_plan)
            return
            
        data = await state.get_data()
        task_index = data['commenting_task']
        tasks = data['tasks']
        task = tasks[task_index]

        if '💬' in task:
            task = task.split('💬')[0].strip()
        
        tasks[task_index] = f"{task} 💬{message.text}"
        await state.update_data(tasks = tasks)
        
        header = data['header']
        full_plan = f"{header}\n" + "\n".join(tasks)
        
        await message.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=full_plan,
            reply_markup=management_keyboard()
        )
        
        await state.set_state(PlanManagement.managing_plan)
        await message.delete()
    except Exception as e:
        logger.error(f"Ошибка в process_comment: {e}")
        await message.answer("Ошибка при добавлении комментария")
        

@router.callback_query(PlanManagement.managing_plan, F.data == "edit_plan")
async def start_editing_plan(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        plan = data.get('plan', {})
        tasks = data.get('tasks')

        logger.info('data:' + str(data))

        await callback.message.edit_text(
            "Выберите пункт для редактирования:",
            reply_markup=plan_tasks_edit_keyboard(tasks)
        )
    except Exception as e:
        logger.error(f"Ошибка в start_editing_plan: {e}")
        await callback.answer("Ошибка при загрузке задач", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("edit_task_"))
async def select_task_to_edit(callback: CallbackQuery, state: FSMContext):
    try:
        task_index = int(callback.data.split('_')[2])
        data = await state.get_data()
        tasks = data['tasks']
        
        task_text = tasks[task_index]
        if '💬' in task_text:
            task_text = task_text.split('💬')[0].strip()
        task_text = task_text.replace('✅', '').strip()
        
        await state.update_data({
            'editing_task_index': task_index,
            'original_task_text': task_text
        })
        
        await callback.message.edit_text(
            f"Редактирование пункта {task_index+1}:\n\n"
            f"Текущий текст: {task_text}\n\n"
            "Введите новый текст для этого пункта:"
        )
        await state.set_state(PlanManagement.editing_task)
    except Exception as e:
        logger.error(f"Ошибка в select_task_to_edit: {e}")
        await callback.answer("Ошибка при выборе задачи", show_alert=True)
    finally:
        await callback.answer()

@router.message(PlanManagement.editing_task)
async def process_task_edit(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        plan: Plan = data.get('plan')
        tasks: List[Task] = plan.tasks
        index_to_update: int= data['editing_task_index']
        tasks[index_to_update].body = message.text
        plan.tasks = tasks

        await state.update_data(tasks = tasks)
        
        await message.answer(
            text=get_full_plan(plan),
            reply_markup=plan_edit_keyboard()
        )
        
        await message.answer("Пункт успешно обновлен!")
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в process_task_edit: {e}")
        await message.answer("Ошибка при обновлении пункта")
    
@router.callback_query(F.data == "add_new_task")
async def add_new_task_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "Введите текст нового пункта:"
        )
        await state.set_state(PlanManagement.adding_task) 
    except Exception as e:
        logger.error(f"Ошибка в add_new_task_handler: {e}")
        await callback.answer("Ошибка при добавлении пункта", show_alert=True)
    finally:
        await callback.answer()

@router.message(PlanManagement.adding_task)
async def process_new_task(message: Message, state: FSMContext):
    logger.info('PROCESS_NEW_TASK')
    try:
        data = await state.get_data()
        tasks = data.get('tasks', [])
        
        tasks.append(message.text)
        await state.update_data(tasks = tasks)
        
        header = data['header']
        full_plan = f"{header}\n" + "\n".join(tasks)
        
        await message.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=full_plan,
            reply_markup=management_keyboard()
        )
        
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в process_new_task: {e}")
        await message.answer("Ошибка при добавлении пункта")

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Выберите действие:", reply_markup=main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "edit_current_plan")
async def edit_current_plan(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    plan = get_current_plan(user_id)
    
    if not plan:
        await callback.message.edit_text("План не найден.", reply_markup=back_keyboard())
        await callback.answer()
        return
    
    plan_body = get_plan_body(plan)
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    tasks = plan_body.split('\n')
    
    await state.update_data(
        plan=plan,
        tasks=tasks,
        plan_name=plan.name,
        current_date=current_date
    )
    
    plan_body = f"📅 {current_date}\n📋 {plan.name}\n\n" + "\n".join(f"• {task}" for task in tasks)
    await callback.message.edit_text(plan_body, reply_markup=plan_editor_keyboard())
    await state.set_state(UserState.editing_plan)
    await callback.answer()

@router.callback_query(F.data == "save_current_plan")
async def save_current_plan(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    plan_name = data.get('plan_name')
    plan_text = "\n".join(tasks)

    create_user_plan(
        user_id=callback.from_user.id,
        name=plan_name,
        tasks_text=plan_text
    )
    
    await callback.message.edit_text("✅ План успешно сохранен!", reply_markup=back_keyboard())
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "finish_day")
async def finish_day(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    group_id = data.get('group_id')
    completed_tasks = sum(1 for task in tasks if '✅' in task)

    save_completed_tasks(
        user_id=callback.from_user.id,
        group_id=None,
        completed_tasks=completed_tasks
    )
    
    if group_id:
        save_completed_tasks(
            user_id=callback.from_user.id,
            group_id=group_id,
            completed_tasks=completed_tasks
        )
    
    await state.update_data(completed_tasks=completed_tasks)
    await callback.message.edit_text(
        "📚 Сколько часов вы сегодня учились?\n\n"
        "Введите количество часов (например: 2.5)"
    )
    await state.set_state(PlanManagement.waiting_for_study_time)
    await callback.answer()

@router.message(PlanManagement.waiting_for_study_time)
async def process_study_time(message: Message, state: FSMContext, bot: Bot):
    try:
        study_hours = float(message.text.replace(',', '.'))
        if study_hours < 0:
            await message.answer("❌ Время не может быть отрицательным. Введите корректное значение:")
            return
        if study_hours > 24:
            await message.answer("❌ Время не может быть больше 24 часов. Введите корректное значение:")
            return
            
        data = await state.get_data()
        completed_tasks = data.get('completed_tasks', 0)
        group_id = data.get('group_id')
        
        save_study_time(
            user_id=message.from_user.id,
            group_id=None,
            study_hours=study_hours
        )
        
        if group_id:
            save_study_time(
                user_id=message.from_user.id,
                group_id=group_id,
                study_hours=study_hours
            )
            await bot.send_message(
                chat_id=group_id,
                text=f"🌙 {message.from_user.mention_html()} завершил день!\n"
                     f"✅ Выполнено задач: {completed_tasks}\n"
                     f"📚 Время обучения: {study_hours:.1f} ч.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"🌙 День завершён!\n\n"
                f"✅ Выполнено задач: {completed_tasks}\n"
                f"📚 Время обучения: {study_hours:.1f} ч."
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число часов:")