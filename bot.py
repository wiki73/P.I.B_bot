from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
import asyncio
from datetime import datetime
from config import load_config, set_bot_commands
from database import *
from keyboards import *
from utils import logger, send_message_with_keyboard
from states import UserState, PlanCreation, PlanManagement, PlanView

config = load_config()
bot = Bot(token=config.bot_token)
dp = Dispatcher()

@dp.callback_query(F.data == "cancel_plan_creation")
async def handle_cancel_plan_creation(callback: CallbackQuery, state: FSMContext):
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

logger.info("Инициализация базы данных...")
try:
    create_tables()
    logger.info("База данных успешно инициализирована")
except Exception as e:
    logger.error(f"Ошибка при инициализации базы данных: {e}")
    raise

@dp.message(lambda message: message.chat.type == "private" and not message.text.startswith('/'))
async def private_chat_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        await send_message_with_keyboard(
            message,
            "Используйте кнопки меню или команды:"
        )

async def show_main_menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())


@dp.message(UserState.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_nick = message.text
    save_user_name(user_id, user_nick)
    await send_message_with_keyboard(message, f"Отлично, {user_nick}!")
    await state.clear()
    await show_main_menu(message)

@dp.message(Command('help'))
async def help_command(message: Message):
    if message.chat.type == "private":
        help_text = (
            "Личные команды:\n"
            "/start - Начало работы\n"
            "/help - Показать это сообщение\n"
            "/info - О планировании\n"
            "/create_plan - Создать новый план\n"
            "/view_plans - Посмотреть планы"
        )

        await send_message_with_keyboard(message, help_text, reply_markup=help_keyboard())
    else:
        await send_message_with_keyboard(
            message,
            "Групповые команды:\n"
            "/new_day - Начать день\n"
            "/static - Статистика"
        )

@dp.callback_query(F.data == "view_base_plans")
async def handle_show_base_plans(callback: CallbackQuery):
    base_plans = get_base_plan()
    keyboard = plans_keyboard(base_plans, 'base')
    callback_message = "Выберите базовый план:"
    
    if not base_plans:
        callback_message = "Базовые планы не найдены."

    await callback.message.edit_text(callback_message, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "view_user_plans")
async def handle_show_user_plans(callback: CallbackQuery):
    try:
        user_plans = get_user_plan(callback.from_user.id)
        logger.info(f'user_plans: {user_plans}')
        
        if not user_plans:
            await callback.message.edit_text(
                "У вас пока нет сохранённых планов.",
                reply_markup=create_plan_keyboard()
            )
            return
        
        
        await callback.message.edit_text(
            "📁 Ваши планы:",
            reply_markup=plans_keyboard(user_plans, 'user')
        )
    except Exception as e:
        logger.error(f"Ошибка при показе планов: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")

@dp.callback_query(F.data.startswith("plan_action:"))
async def handle_plan_action(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    _, plan_type, plan_id = callback.data.split(':')
    plan_id = int(plan_id)
    
    if plan_type == 'base':
        plans = get_base_plan()
    else:
        plans = get_user_plan(callback.from_user.id)
    
    selected_plan = next((p for p in plans if p['id'] == plan_id), None)
    if not selected_plan:
        await callback.answer("План не найден!")
        return
    
    if current_state == 'UserState:selecting_existing_plan':
        current_date = datetime.now().strftime("%d.%m.%Y")
        plan_header = f"📅 {current_date}\n📋 {selected_plan['name']}\n\n"
        
        tasks = selected_plan['plan_text'].split('\n')
        
        await state.update_data(
            selected_plan=selected_plan,
            tasks=tasks,
            plan_name=selected_plan['name'],
            current_date=current_date
        )
        
        plan_text = plan_header + "\n".join(task for task in tasks)
        await callback.message.edit_text(plan_text, reply_markup=plan_edit_keyboard())
    else:
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        keyboard = plan_actions_keyboard(selected_plan['name'], plan_type, plan_id)
        
        await callback.message.edit_text(
            f"📅 {current_date}\n"
            f"✅ План <b>{selected_plan['name']}</b>\n\n"
            f"Содержание:\n{selected_plan['plan_text']}",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    await callback.answer()




@dp.callback_query(UserState.selecting_existing_plan, F.data.startswith('select_user_'))
async def select_user_plan_for_new_day(callback: CallbackQuery, state: FSMContext):
    await show_user_plans(callback, state)

@dp.callback_query(UserState.selecting_existing_plan, F.data.in_(["select_base_plans", "select_user_plans", "cancel_plan_creation"]))
async def handle_existing_plan_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data == "select_base_plans":
        base_plans = get_base_plan()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:base:{plan['id']}")]
            for plan in base_plans
        ])
        await callback.message.edit_text(
            "Выберите базовый план:",
            reply_markup=keyboard
        )
    elif callback.data == "select_user_plans":
        user_plans = get_user_plan(callback.from_user.id)
        if not user_plans:
            await callback.message.edit_text("У вас пока нет сохраненных планов.")
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:user:{plan['id']}")]
            for plan in user_plans
        ])
        await callback.message.edit_text(
            "Выберите ваш план:",
            reply_markup=keyboard
        )
    elif callback.data == "cancel_plan_creation":
        await handle_cancel_plan_creation(callback, state)
    
    await callback.answer()

@dp.callback_query(F.data == 'create_plan')
async def create_plan_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введите название для нового плана:",
        reply_markup=create_plan_keyboard
    )
    await state.set_state(PlanCreation.waiting_for_title)
    await callback.answer()


@dp.message(UserState.creating_new_plan)
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

@dp.message(UserState.waiting_for_plan_tasks)
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

@dp.callback_query(F.data == 'current_plan')
async def show_current_plan(callback: CallbackQuery):
    user_id = callback.from_user.id
    plan_name = get_current_plan(user_id)
    
    if not plan_name:
        await callback.message.edit_text("У вас нет активного плана.", reply_markup=back_keyboard())
        await callback.answer()
        return

    plan_text = get_plan_text_by_name(plan_name)
    if plan_text:
        await callback.message.edit_text(
            f"📋 Текущий план: {plan_name}\n\n{plan_text}",
            reply_markup=current_plan_keyboard()
        )
    else:
        await callback.message.edit_text("Не удалось загрузить план.", reply_markup=back_keyboard())
    await callback.answer()

@dp.message(Command('info'))
async def info_command(message: Message):
    info_text = (
        "Планирование помогает:\n\n"
        "1. Избежать суеты в течение дня\n"
        "2. Освободить время для отдыха\n"
        "3. Развивать дисциплину\n\n"
        "Попробуйте создать свой первый план!"
    )
    await send_message_with_keyboard(message, info_text)

@dp.message(Command('create_plan'))
async def create_plan_command(message: types.Message, state: FSMContext):
    if message.chat.type == "private":
        await send_message_with_keyboard(
            message,
            "📝 Давайте создадим новый план.\n"
            "Введите название для вашего плана:"
        )
        await state.set_state(PlanCreation.waiting_for_title)
    else:
        await send_message_with_keyboard(
            message,
            "Эта команда доступна только в личном чате с ботом."
        )

@dp.message(PlanCreation.waiting_for_title)
async def process_plan_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "✏️ Теперь введите задачи для плана (каждая задача с новой строки):\n\n"
        "Пример:\n"
        "1. Зарядка\n"
        "2. Завтрак\n"
        "3. Работа над проектом"
    )
    await state.set_state(PlanCreation.waiting_for_tasks)

@dp.message(PlanCreation.waiting_for_tasks)
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

@dp.message(PlanCreation.waiting_for_confirmation, F.text.lower().in_(['да', 'нет']))
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

@dp.message(PlanCreation.waiting_for_confirmation)
async def wrong_confirmation(message: Message):
    await send_message_with_keyboard(message, "Пожалуйста, ответьте 'да' или 'нет'")

@dp.message(Command('view_plans'))
async def view_plans_command(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await send_message_with_keyboard(
            message,
            "Эта команда доступна только в личном чате с ботом."
        )
        return

    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Базовые планы",
            callback_data="view_base_plans"
        ),
        types.InlineKeyboardButton(
            text="Мои планы",
            callback_data="view_user_plans"
        )
    )
    builder.adjust(1)
    
    await send_message_with_keyboard(
        message,
        "📂 Выберите тип планов для просмотра:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(PlanView.viewing_plans)

@dp.callback_query()
async def handle_callback_query(callback: CallbackQuery ):
    try:
        if callback.message.chat.type == "private":
            await callback.message.answer(
                "Используйте меню для быстрого доступа:",
                reply_markup=personal_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке callback: {e}")
    
    await callback.answer()

@dp.callback_query(F.data == "view_base_plans", PlanView.viewing_plans)
async def show_base_plans(callback: types.CallbackQuery):
    base_plans = get_base_plan()
    
    if not base_plans:
        await callback.message.edit_text("Базовые планы не найдены.")
        return
    
    builder = InlineKeyboardBuilder()
    
    for plan in base_plans:
        builder.add(
            types.InlineKeyboardButton(
                text=plan['name'],
                callback_data=f"select_base_{plan['id']}"
            )
        )
    
    builder.add(
        types.InlineKeyboardButton(
            text="← Назад",
            callback_data="back_to_plan_types"
        )
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📚 Доступные базовые планы:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "view_user_plans", PlanView.viewing_plans)
async def show_user_plans(callback: types.CallbackQuery, state: FSMContext):
    user_plans = get_user_plan(callback.from_user.id)
    if not user_plans:
        await callback.message.answer("У вас пока нет сохраненных планов.")
        await callback.answer()
        return
    
    builder = InlineKeyboardBuilder()
    
    for plan in user_plans:
        builder.add(
            types.InlineKeyboardButton(
                text=plan['name'],
                callback_data=f"plan_action:user:{plan['id']}"
            )
        )
    
    builder.add(
        types.InlineKeyboardButton(
            text="← Назад",
            callback_data="back_to_plan_types"
        )
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📁 Ваши сохраненные планы:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_plan_types")
async def back_to_plan_types(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Базовые планы",
            callback_data="view_base_plans"
        ),
        types.InlineKeyboardButton(
            text="Мои планы",
            callback_data="view_user_plans"
        )
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📂 Выберите тип планов для просмотра:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("select_plan:"))
async def select_plan(callback: types.CallbackQuery):
    _, plan_type, plan_id = callback.data.split(':')
    
    if plan_type == "base":
        plans = get_base_plan()
    else:
        plans = get_user_plan(callback.from_user.id)
    
    selected_plan = next((p for p in plans if p['id'] == int(plan_id)), None)
    
    if not selected_plan:
        await callback.answer("План не найден!")
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Выбрать этот план",
            callback_data=f"use_plan:{plan_type}:{plan_id}"
        ),
        types.InlineKeyboardButton(
            text="← Назад",
            callback_data=f"view_{plan_type}_plans"
        )
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📋 <b>{selected_plan['name']}</b>\n\n"
        f"{selected_plan['plan_text']}\n\n"
        "Вы можете выбрать этот план как текущий:",
        parse_mode='HTML',
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("use_plan:"))
async def use_plan(callback: types.CallbackQuery):
    _, plan_type, plan_id = callback.data.split(':')
    
    if plan_type == "base":
        plans = get_base_plan()
    else:
        plans = get_user_plan(callback.from_user.id)
    
    selected_plan = next((p for p in plans if p['id'] == int(plan_id)), None)
    
    if not selected_plan:
        await callback.answer("План не найден!")
        return
    
    update_user_current_plan(callback.from_user.id, selected_plan['name'])
    
    await callback.message.edit_text(
        f"✅ План <b>{selected_plan['name']}</b> теперь ваш текущий план!\n\n"
        f"Содержание:\n{selected_plan['plan_text']}",
        parse_mode='HTML'
    )
    await callback.answer()

@dp.message(Command('new_day'), F.chat.type.in_({"group", "supergroup"}))
async def new_day_group(message: Message, state: FSMContext):
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

@dp.callback_query(F.data == "cancel_new_day")
async def cancel_new_day(callback: CallbackQuery):
    await send_message_with_keyboard(
        callback.message,
        f"❌ {callback.from_user.mention_html()} отменил создание плана.",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    args = message.text.split()[1:]
    logger.info('/start args: ' + str(args))
    if len(args) > 0:
        group_id = int(args[0].split('_')[1])

        await state.update_data(group_id=group_id)
        await state.set_state(UserState.choosing_plan_type)
        await show_plan_creation_options(message, state)
    else:
        user_id = message.from_user.id
        user_name = get_user_name(user_id)
        
        if user_name is None:
            await send_message_with_keyboard(
                message,
                'Привет! Я твой бот для планирования. Как мне тебя называть?'
            )
            await state.set_state(UserState.waiting_for_nickname)
        else:
            await send_message_with_keyboard(
                message,
                f"Привет, {user_name}! Чем могу помочь?"
            )
            await show_main_menu(message)

async def show_plan_creation_options(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_plan_name: str | None = get_current_plan(user_id)
    
    await send_message_with_keyboard(
        message,
        "Выберите действие:",
        reply_markup=plan_creation_options_keyboard(current_plan_name)
    )
    await state.set_state(UserState.choosing_plan_type)

@dp.callback_query(UserState.choosing_plan_type)
async def handle_plan_type_choice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if callback.data == "use_existing_plan":
        await show_existing_plans(callback, state)
        await state.set_state(UserState.selecting_existing_plan)
    elif callback.data == "create_new_plan":
        current_date = datetime.now().strftime("%d.%m.%Y")
        data['current_date'] = current_date
        await state.set_data(data)
        await callback.message.edit_text("📝 Введите название для нового плана на сегодня:")
        await state.set_state(UserState.creating_new_plan)
    elif callback.data == "use_current_plan":
        user_id = callback.from_user.id
        current_plan_name = get_current_plan(user_id)
        
        if not current_plan_name:
            await callback.message.edit_text("Ошибка: текущий план не найден.")
            await callback.answer()
            return
        
        plan_text = get_plan_text_by_name(current_plan_name)
        if not plan_text:
            await callback.message.edit_text("Ошибка: не удалось загрузить текущий план.")
            await callback.answer()
            return
        
        current_date = datetime.now().strftime("%d.%m.%Y")
        plan_header = f"📅 {current_date}\n📋 {current_plan_name}\n\n"
        
        tasks = plan_text.split('\n')
        
        data.update({
            'tasks': tasks,
            'plan_name': current_plan_name,
            'current_date': current_date
        })
        await state.set_data(data)
        
        plan_text = plan_header + "\n".join(task for task in tasks)

        await callback.message.edit_text(plan_text, reply_markup=plan_edit_keyboard())
        await state.set_state(UserState.editing_plan)
    elif callback.data == "cancel_plan_creation":
        await handle_cancel_plan_creation(callback, state)
    
    await callback.answer()

@dp.callback_query(F.data == "edit_tasks")
async def start_task_editing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n"
    plan_text += "Текущие задачи:\n" + "\n".join(task for task in tasks)
    plan_text += "\n\nВыберите действие:"
    
    await callback.message.edit_text(plan_text, reply_markup=task_edit_keyboard(tasks))
    await state.set_state(UserState.editing_plan)
    await callback.answer()

@dp.callback_query(F.data == "add_new_task")
async def add_new_task(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    
    await callback.message.edit_text(
        "Выберите, куда добавить новый пункт:",
        reply_markup=task_position_keyboard(tasks)
    )
    await callback.answer()

@dp.callback_query(PlanManagement.managing_plan, F.data == "mark_tasks")
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

@dp.callback_query(PlanManagement.managing_plan, F.data == "task_comments")
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

@dp.callback_query(F.data == "back_to_manage")
async def back_to_management(callback: CallbackQuery, state: FSMContext):
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

@dp.callback_query(PlanManagement.managing_plan, F.data == "close_management")
async def close_management(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в close_management: {e}")
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("comment_task_"))
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

@dp.message(PlanManagement.adding_comment, F.text)
async def process_comment(message: Message, state: FSMContext):
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
        await state.update_data({'tasks': tasks})
        
        header = data['header']
        full_plan = f"{header}\n" + "\n".join(tasks)
        
        await message.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=full_plan,
            reply_markup=management_keyboard()
        )
        
        await state.set_state(PlanManagement.managing_plan)
        await message.answer("Комментарий успешно добавлен!")
    except Exception as e:
        logger.error(f"Ошибка в process_comment: {e}")
        await message.answer("Ошибка при добавлении комментария")
        

@dp.callback_query(PlanManagement.managing_plan, F.data == "edit_plan")
async def start_editing_plan(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        tasks = data['tasks']
        
        keyboard = InlineKeyboardBuilder()
        for i, task in enumerate(tasks):
            clean_task = task.replace('✅', '').split('💬')[0].strip()
            keyboard.add(InlineKeyboardButton(
                text=f"{i+1}. {clean_task[:20]}...",
                callback_data=f"edit_task_{i}"
            ))
        
        keyboard.adjust(1)
        keyboard.row(InlineKeyboardButton(
            text="➕ Добавить пункт",
            callback_data="add_new_task"
        ))
        keyboard.row(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_manage"
        ))
        
        await callback.message.edit_text(
            "Выберите пункт для редактирования:",
            reply_markup=keyboard.as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка в start_editing_plan: {e}")
        await callback.answer("Ошибка при загрузке задач", show_alert=True)
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("edit_task_"))
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

@dp.message(PlanManagement.editing_task)
async def process_task_edit(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        task_index = data['editing_task_index']
        tasks = data['tasks']
        
        old_task = tasks[task_index]
        marks = '✅' if '✅' in old_task else ''
        comment = ''
        if '💬' in old_task:
            comment = ' 💬' + old_task.split('💬')[1]
        
        tasks[task_index] = f"{marks} {message.text}{comment}".strip()
        await state.update_data({'tasks': tasks})
        
        header = data['header']
        full_plan = f"{header}\n" + "\n".join(tasks)
        
        await message.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=full_plan,
            reply_markup=management_keyboard()
        )
        
        await message.answer("Пункт успешно обновлен!")
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в process_task_edit: {e}")
        await message.answer("Ошибка при обновлении пункта")
    
@dp.callback_query(F.data == "add_new_task")
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

@dp.message(PlanManagement.adding_task)
async def process_new_task(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        tasks = data.get('tasks', [])
        
        tasks.append(message.text)
        await state.update_data({'tasks': tasks})
        
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

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Выберите действие:", reply_markup=main_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "edit_current_plan")
async def edit_current_plan(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    plan_name = get_current_plan(user_id)
    
    if not plan_name:
        await callback.message.edit_text("План не найден.", reply_markup=back_keyboard())
        await callback.answer()
        return
    
    plan_text = get_plan_text_by_name(plan_name)
    if not plan_text:
        await callback.message.edit_text("Не удалось загрузить план.", reply_markup=back_keyboard())
        await callback.answer()
        return
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    tasks = plan_text.split('\n')
    
    await state.update_data(
        tasks=tasks,
        plan_name=plan_name,
        current_date=current_date
    )
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(f"• {task}" for task in tasks)
    await callback.message.edit_text(plan_text, reply_markup=plan_editor_keyboard())
    await state.set_state(UserState.editing_plan)
    await callback.answer()

@dp.callback_query(F.data == "save_current_plan")
async def save_current_plan(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    plan_name = data.get('plan_name')
    plan_text = "\n".join(tasks)

    save_user_plan(callback.from_user.id, plan_name, plan_text)
    
    await callback.message.edit_text("✅ План успешно сохранен!", reply_markup=back_keyboard)
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "finish_day")
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

@dp.message(PlanManagement.waiting_for_study_time)
async def process_study_time(message: Message, state: FSMContext):
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

@dp.message(Command('static'))
async def show_statistics(message: Message):
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    if message.chat.type in ["group", "supergroup"]:
        completed_stats = get_group_completed_tasks(message.chat.id)
        study_time = get_group_study_time(message.chat.id)
        
        if completed_stats['total_completed'] == 0 and study_time == 0:
            await message.answer("📊 В этой группе пока нет статистики!")
            return
            
        await message.answer(
            f"📊 Статистика группы на {current_date}:\n\n"
            f"✅ Всего выполнено задач: {completed_stats['total_completed']}\n"
            f"📚 Общее время обучения: {study_time:.1f} ч."
        )
    else:
        completed_tasks = get_user_completed_tasks(message.from_user.id)
        study_time = get_user_study_time(message.from_user.id)
        
        if completed_tasks == 0 and study_time == 0:
            await message.answer("📊 У вас пока нет статистики!")
            return
            
        await message.answer(
            f"📊 Ваша статистика на {current_date}:\n\n"
            f"✅ Всего выполнено задач: {completed_tasks}\n"
            f"📚 Общее время обучения: {study_time:.1f} ч."
        )

async def main():
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())