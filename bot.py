from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ForceReply
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
from database import *

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаем таблицы в БД при запуске
logger.info("Инициализация базы данных...")
try:
    create_tables()
    logger.info("База данных успешно инициализирована")
except Exception as e:
    logger.error(f"Ошибка при инициализации базы данных: {e}")
    raise

# Состояния пользователя
class UserState(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_plan_title = State()
    waiting_for_plan_tasks = State()
    waiting_for_base_plan_choice = State()
    waiting_for_confirm = State()
    editing_plan = State()
    choosing_plan_type = State()
    selecting_existing_plan = State()
    creating_new_plan = State()
    publishing_plan = State()
    adding_new_task = State()


class PlanManagement(StatesGroup):
    managing_plan = State()
    marking_tasks = State()
    adding_comment = State()
    editing_task = State()  
    adding_task = State()

# Клавиатура для личных сообщений
personal_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start"), KeyboardButton(text="/help")],
        [KeyboardButton(text="/info"), KeyboardButton(text="/create_plan")],
        [KeyboardButton(text="/view_plans")]
    ],
    resize_keyboard=True,
    persistent=True
)

# Клавиатура для групповых чатов
group_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/new_day"), KeyboardButton(text="/static")],
        [KeyboardButton(text="/help")]
    ],
    resize_keyboard=True,
    persistent=True
)
####
@dp.message(F.chat.type == {"group", "supergroup"})
async def private_chat_handler(message: Message, state: FSMContext):
    # Если сообщение не обработано другими хендлерами
    if not message.text.startswith('/'):
        await message.answer(
            "Используйте кнопки меню или команды:",
            reply_markup=personal_keyboard
        )

async def show_main_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои планы", callback_data="view_user_plans")],
        [InlineKeyboardButton(text="Базовые планы", callback_data="view_base_plans")],
        [InlineKeyboardButton(text="Создать план", callback_data="create_plan")],
        [InlineKeyboardButton(text="Текущий план", callback_data="current_plan")]
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)


# Обработчик ввода ника
@dp.message(UserState.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_nick = message.text
    save_user_name(user_id, user_nick)
    await message.answer(f"Отлично, {user_nick}!", reply_markup=personal_keyboard)
    await state.clear()
    await show_main_menu(message)

# Команда /help
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

        # Добавляем кнопку для просмотра текущего плана
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Посмотреть текущий план", callback_data="current_plan")]
        ])

        await message.answer(help_text, reply_markup=personal_keyboard)
        await message.answer("Вы можете также:", reply_markup=inline_keyboard)
    else:
        await message.answer(
            "Групповые команды:\n"
            "/new_day - Начать день\n"
            "/static - Статистика",
            reply_markup=group_keyboard
        )

@dp.callback_query(F.data == "view_base_plans")
async def handle_show_base_plans(callback: CallbackQuery):
    logging.info("Пользователь выбрал базовые планы.")
    base_plans = get_base_plan()
    
    if not base_plans:
        await callback.message.edit_text("Базовые планы не найдены.")
        await callback.answer()
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:base:{plan['id']}")]
        for plan in base_plans
    ])
    
    await callback.message.edit_text("Выберите базовый план:", reply_markup=keyboard)
    await callback.answer()

# Обработчик для просмотра пользовательских планов
@dp.callback_query(F.data == "view_user_plans")
async def handle_show_user_plans(callback: CallbackQuery):
    try:
        user_plans = get_user_plan(callback.from_user.id)
        
        if not user_plans:
            await callback.message.edit_text(
                "У вас пока нет сохранённых планов.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Создать план", callback_data="create_plan")]
                ]))
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:user:{plan['id']}")]
            for plan in user_plans
        ])
        
        await callback.message.edit_text(
            "📁 Ваши планы:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка при показе планов: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")


# Обработчик авторсикх планов для start
# @dp.callback_query(F.data == 'my_plans')
# async def show_user_plans(callback: CallbackQuery, state: FSMContext):
#     user_plans = get_user_plan(callback.from_user.id)
    
#     if not user_plans:
#         await callback.message.answer("У вас пока нет сохраненных планов.")
#         await callback.answer()
#         return

#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:user:{plan['id']}")]
#         for plan in user_plans
#     ])
    
#     await callback.message.edit_text("Выберите свой план:", reply_markup=keyboard)
#     await callback.answer()

# Обработчик базовых планов для start
# @dp.callback_query(F.data == 'base_plans')
# async def show_base_plans(callback: CallbackQuery, state: FSMContext):
#     base_plans = get_base_plan()
    
#     if not base_plans:
#         await callback.message.answer("Нет доступных базовых планов.")
#         await callback.answer()
#         return

#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:base:{plan['id']}")]
#         for plan in base_plans
#     ])
#     await callback.message.edit_text("Выберите базовый план:", reply_markup=keyboard)
#     await callback.answer()

# Единый обработчик для работы с планами
@dp.callback_query(F.data.startswith("plan_action:"))
async def handle_plan_action(callback: CallbackQuery, state: FSMContext):
    logging.info("Пользователь выбрал план.")
    current_state = await state.get_state()
    _, plan_type, plan_id = callback.data.split(':')
    plan_id = int(plan_id)
    
    # Получаем план в зависимости от типа
    if plan_type == 'base':
        plans = get_base_plan()
    else:
        plans = get_user_plan(callback.from_user.id)
    
    selected_plan = next((p for p in plans if p['id'] == plan_id), None)
    if not selected_plan:
        await callback.answer("План не найден!")
        return
    
    # Если мы в процессе создания нового дня
    if current_state == 'UserState:selecting_existing_plan':
        # Добавляем текущую дату к плану
        current_date = datetime.now().strftime("%d.%m.%Y")
        plan_header = f"📅 {current_date}\n📋 {selected_plan['name']}\n\n"
        
        # Разбиваем текст плана на задачи
        tasks = selected_plan['plan_text'].split('\n')
        
        # Сохраняем данные в состояние
        await state.update_data(
            selected_plan=selected_plan,
            tasks=tasks,
            plan_name=selected_plan['name'],
            current_date=current_date
        )
        
        # Показываем редактор плана
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
            [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
        ])
        
        plan_text = plan_header + "\n".join(f"• {task}" for task in tasks)
        await callback.message.edit_text(plan_text, reply_markup=keyboard)
    else:
        # Если просто выбираем план
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        buttons = []
        buttons.append([InlineKeyboardButton(text="📌 Сделать текущим", callback_data=f"set_current_plan:{selected_plan['name']}")])
        
        if plan_type == 'user':
            buttons.append([InlineKeyboardButton(text="🗑 Удалить план", callback_data=f"confirm_delete_plan:{plan_type}:{plan_id}")])
            
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_plan_types")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(
            f"📅 {current_date}\n"
            f"✅ План <b>{selected_plan['name']}</b>\n\n"
            f"Содержание:\n{selected_plan['plan_text']}",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    await callback.answer()




# Обработчик выбора пользовательского плана в контексте создания нового дня
@dp.callback_query(UserState.selecting_existing_plan, F.data.startswith('select_user_'))
async def select_user_plan_for_new_day(callback: CallbackQuery, state: FSMContext):
    await show_user_plans(callback, state)

# Обработчик выбора существующего плана
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
        await callback.message.edit_text("Создание плана отменено.")
        await state.clear()
    
    await callback.answer()

# Обработчик создания плана через главное меню
@dp.callback_query(F.data == 'create_plan')
async def create_plan_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Введите название для нового плана:"
    )
    await state.set_state(PlanCreation.waiting_for_title)
    await callback.answer()


# Создание плана - шаг 2
@dp.message(UserState.creating_new_plan)
async def process_new_day_plan_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "✏️ Теперь введите задачи для плана (каждая задача с новой строки):\n\n"
        "Пример:\n"
        "1. Зарядка\n"
        "2. Завтрак\n"
        "3. Работа над проектом"
    )
    await state.set_state(UserState.waiting_for_plan_tasks)

# Создание плана - шаг 3
@dp.message(UserState.waiting_for_plan_tasks)
async def process_new_day_plan_tasks(message: Message, state: FSMContext):
    data = await state.get_data()
    tasks = message.text.split('\n')
    current_date = data.get('current_date')
    plan_name = data.get('title')
    
    # Сохраняем данные в состояние
    await state.update_data(
        tasks=tasks,
        plan_name=plan_name
    )
    
    # Показываем редактор плана
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ])
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(f"• {task}" for task in tasks)
    await message.answer(plan_text, reply_markup=keyboard)
    await state.set_state(UserState.editing_plan)

# Обработчик для текущего плана
@dp.callback_query(F.data == 'current_plan')
async def show_current_plan(callback: CallbackQuery):
    user_id = callback.from_user.id
    plan_name = get_current_plan(user_id)
    
    if not plan_name:
        await callback.message.answer("У вас нет активного плана.")
        await callback.answer()
        return

    plan_text = get_plan_text_by_name(plan_name)
    if plan_text:
        await callback.message.answer(f"📋 Текущий план: {plan_name}\n\n{plan_text}")
    else:
        await callback.message.answer("Не удалось загрузить план.")
    await callback.answer()

# Команда /info
@dp.message(Command('info'))
async def info_command(message: Message):
    info_text = (
        "Планирование помогает:\n\n"
        "1. Избежать суеты в течение дня\n"
        "2. Освободить время для отдыха\n"
        "3. Развивать дисциплину\n\n"
        "Попробуйте создать свой первый план!"
    )
    await message.answer(info_text)


class PlanCreation(StatesGroup):# начало обработки создания плана
    waiting_for_title = State()
    waiting_for_tasks = State()
    waiting_for_confirmation = State()

# Обработчик команды /create_plan
@dp.message(Command('create_plan'))
async def create_plan_command(message: types.Message, state: FSMContext):
    await message.answer(
        "📝 Давайте создадим новый план.\n"
        "Введите название для вашего плана:"
    )
    await state.set_state(PlanCreation.waiting_for_title)

# Обработчик ввода названия плана (должен использовать PlanCreation.waiting_for_title)
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

# Обработчик ввода задач плана (должен использовать PlanCreation.waiting_for_tasks)
@dp.message(PlanCreation.waiting_for_tasks)
async def process_plan_tasks(message: types.Message, state: FSMContext):
    tasks = message.text.split('\n')
    data = await state.get_data()
    
    # Форматируем задачи в красивый список
    formatted_tasks = "\n".join(f"• {task.strip()}" for task in tasks if task.strip())
    
    await state.update_data(tasks=formatted_tasks)
    
    # Показываем предпросмотр плана
    preview = (
        f"📋 <b>{data['title']}</b>\n\n"
        f"{formatted_tasks}\n\n"
        "Всё верно? (да/нет)"
    )
    
    await message.answer(preview, parse_mode='HTML')
    await state.set_state(PlanCreation.waiting_for_confirmation)

# Обработчик подтверждения плана
@dp.message(PlanCreation.waiting_for_confirmation, F.text.lower().in_(['да', 'нет']))
async def confirm_plan(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        data = await state.get_data()
        user_id = message.from_user.id
        
        # Сохраняем план в базу данных
        save_user_plan(
            user_id=user_id,
            name=data['title'],
            text=data['tasks']
        )
        
        await message.answer(
            f"✅ План <b>{data['title']}</b> успешно сохранён!\n"
            "Теперь вы можете использовать его в своём расписании.",
            parse_mode='HTML'
        )
    else:
        await message.answer(
            "Создание плана отменено.\n"
            "Если хотите начать заново, введите /create_plan"
        )
    
    await state.clear()

# Обработчик некорректного ввода подтверждения
@dp.message(PlanCreation.waiting_for_confirmation)
async def wrong_confirmation(message: types.Message):
    await message.answer("Пожалуйста, ответьте 'да' или 'нет'")



class PlanView(StatesGroup):
    viewing_plans = State()

# Обработчик команды /view_plans
@dp.message(Command('view_plans'))
async def view_plans_command(message: types.Message, state: FSMContext):
    # Создаем клавиатуру с выбором типа планов
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
    
    await message.answer(
        "📂 Выберите тип планов для просмотра:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(PlanView.viewing_plans)

# Обработчик выбора базовых планов
@dp.callback_query(F.data == "view_base_plans", PlanView.viewing_plans)
async def show_base_plans(callback: types.CallbackQuery):
    logging.info("Пользователь выбрал базовые планы.")
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

# Обработчик выбора пользовательских планов
@dp.callback_query(F.data == "view_user_plans", PlanView.viewing_plans)
async def show_user_plans(callback: types.CallbackQuery, state: FSMContext):
    logging.info("Пользователь выбрал свои планы.")
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

# Обработчик возврата к выбору типа планов
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

# Обработчик выбора конкретного плана
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

# Обработчик применения плана
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

# Обработчик /new_day для групп
@dp.message(Command('new_day'), F.chat.type.in_({"group", "supergroup"}))
async def new_day_group(message: Message):
    try:
        bot_username = (await bot.get_me()).username
        deep_link = f"https://t.me/{bot_username}?start=newday_{message.chat.id}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✨ Создать мой план",
                url=deep_link
            )],
            [InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_new_day"
            )]
        ])
        
        await message.reply(
            f"🌅 {message.from_user.mention_html()} начинает новый день!\n"
            "Нажмите кнопку ниже, чтобы создать личный план ↓",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в new_day_group: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

# Обработчик отмены создания плана
@dp.callback_query(F.data == "cancel_new_day")
async def cancel_new_day(callback: CallbackQuery):
    await callback.message.edit_text(
        f"❌ {callback.from_user.mention_html()} отменил создание плана.",
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик deep link для создания плана
@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('newday_'):
        group_id = int(args[1].split('_')[1])
        await state.update_data(group_id=group_id)
        await state.set_state(UserState.choosing_plan_type)  # Устанавливаем состояние перед показом опций
        await show_plan_creation_options(message, state)
    else:
        user_id = message.from_user.id
        user_name = get_user_name(user_id)
        
        if user_name is None:
            await message.answer('Привет! Я твой бот для планирования. Как мне тебя называть?')
            await state.set_state(UserState.waiting_for_nickname)
        else:
            await message.answer(f"Привет, {user_name}! Чем могу помочь?")
            await show_main_menu(message)

async def show_plan_creation_options(message: Message, state: FSMContext):
    logger.info("Показываем опции создания плана")
    current_state = await state.get_state()
    logger.info(f"Текущее состояние: {current_state}")
    
    # Проверяем, есть ли текущий план у пользователя
    user_id = message.from_user.id
    current_plan_name = get_current_plan(user_id)
    logger.info(f"Текущий план пользователя: {current_plan_name}")
    
    buttons = []
    if current_plan_name:
        logger.info("Добавляем кнопку использования текущего плана")
        buttons.append([InlineKeyboardButton(text="📌 Использовать текущий план", callback_data="use_current_plan")])
    
    buttons.extend([
        [InlineKeyboardButton(text="📋 Использовать существующий план", callback_data="use_existing_plan")],
        [InlineKeyboardButton(text="✨ Создать новый план", callback_data="create_new_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "Выберите действие:",
        reply_markup=keyboard
    )
    await state.set_state(UserState.choosing_plan_type)

# Обработчик выбора типа плана
@dp.callback_query(UserState.choosing_plan_type)
async def handle_plan_type_choice(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Обработка выбора типа плана: {callback.data}")
    if callback.data == "use_existing_plan":
        await show_existing_plans(callback, state)
        await state.set_state(UserState.selecting_existing_plan)
    elif callback.data == "create_new_plan":
        current_date = datetime.now().strftime("%d.%m.%Y")
        await state.update_data(current_date=current_date)
        await callback.message.edit_text("📝 Введите название для нового плана на сегодня:")
        await state.set_state(UserState.creating_new_plan)
    elif callback.data == "use_current_plan":
        logger.info("Обработка использования текущего плана")
        user_id = callback.from_user.id
        current_plan_name = get_current_plan(user_id)
        
        if not current_plan_name:
            await callback.message.edit_text("Ошибка: текущий план не найден.")
            await callback.answer()
            return
        
        # Получаем текст плана
        plan_text = get_plan_text_by_name(current_plan_name)
        if not plan_text:
            await callback.message.edit_text("Ошибка: не удалось загрузить текущий план.")
            await callback.answer()
            return
        
        logger.info("План успешно загружен, подготавливаем к редактированию")
        
        # Добавляем текущую дату к плану
        current_date = datetime.now().strftime("%d.%m.%Y")
        plan_header = f"📅 {current_date}\n📋 {current_plan_name}\n\n"
        
        # Разбиваем текст плана на задачи
        tasks = plan_text.split('\n')
        
        # Сохраняем данные в состояние
        await state.update_data(
            tasks=tasks,
            plan_name=current_plan_name,
            current_date=current_date
        )
        
        # Показываем редактор плана
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
            [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
        ])
        
        plan_text = plan_header + "\n".join(f"• {task}" for task in tasks)
        await callback.message.edit_text(plan_text, reply_markup=keyboard)
        await state.set_state(UserState.editing_plan)
    elif callback.data == "cancel_plan_creation":
        await callback.message.edit_text("Создание плана отменено.")
        await state.clear()
    
    await callback.answer()

# Обработчик редактирования задач
@dp.callback_query(F.data == "edit_tasks")
async def start_task_editing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    
    # Создаем клавиатуру для редактирования с кнопкой добавления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✏️ Изменить задачу {i+1}", callback_data=f"edit_task_{i}")]
        for i in range(len(tasks))
    ] + [
        [InlineKeyboardButton(text="➕ Добавить пункт", callback_data="add_new_task")],
        [InlineKeyboardButton(text="◀️ Назад к плану", callback_data="back_to_plan")]
    ])
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n"
    plan_text += "Текущие задачи:\n" + "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
    plan_text += "\n\nВыберите действие:"
    
    await callback.message.edit_text(plan_text, reply_markup=keyboard)
    await state.set_state(UserState.editing_plan)
    await callback.answer()

# Обработчик добавления нового пункта
@dp.callback_query(F.data == "add_new_task")
async def add_new_task(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    
    # Создаем клавиатуру для выбора позиции
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Добавить после пункта {i+1}", callback_data=f"add_at_{i+1}")]
        for i in range(len(tasks))
    ] + [
        [InlineKeyboardButton(text="Добавить в начало", callback_data="add_at_0")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="edit_tasks")]
    ])
    
    await callback.message.edit_text(
        "Выберите, куда добавить новый пункт:",
        reply_markup=keyboard
    )
    await callback.answer()

# Обработчик выбора позиции для нового пункта
@dp.callback_query(F.data.startswith("add_at_"))
async def select_task_position(callback: CallbackQuery, state: FSMContext):
    position = int(callback.data.split('_')[-1])
    await state.update_data(new_task_position=position)
    await callback.message.edit_text("Введите текст нового пункта:")
    await state.set_state(UserState.adding_new_task)
    await callback.answer()

# Обработчик ввода текста нового пункта
async def show_task_editor(chat_id: int, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✏️ Изменить задачу {i+1}", callback_data=f"edit_task_{i}")]
        for i in range(len(tasks))
    ] + [
        [InlineKeyboardButton(text="➕ Добавить пункт", callback_data="add_new_task")],
        [InlineKeyboardButton(text="◀️ Назад к плану", callback_data="back_to_plan")]
    ])
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n"
    plan_text += "Текущие задачи:\n" + "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
    plan_text += "\n\nВыберите действие:"
    
    await bot.send_message(
        chat_id=chat_id,
        text=plan_text,
        reply_markup=keyboard
    )

@dp.message(PlanManagement.adding_task)
async def process_new_task(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        tasks = data.get('tasks', [])
        
        tasks.append(message.text)
        await state.update_data({'tasks': tasks})
        
        # Обновляем сообщение с планом
        header = data['header']
        full_plan = f"{header}\n" + "\n".join(tasks)
        
        await message.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=full_plan,
            reply_markup=get_management_keyboard()
        )
        
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в process_new_task: {e}")
        await message.answer("Ошибка при добавлении пункта")

# Обработчик возврата к плану
@dp.callback_query(F.data == "back_to_plan")
async def back_to_plan(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ])
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(f"• {task}" for task in tasks)
    await callback.message.edit_text(plan_text, reply_markup=keyboard)
    await callback.answer()

# Обработчик выбора задачи для редактирования
@dp.callback_query(UserState.editing_plan, F.data.startswith("edit_task_"))
async def edit_task(callback: CallbackQuery, state: FSMContext):
    task_index = int(callback.data.split('_')[-1])
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    
    await state.update_data(editing_task_index=task_index)
    
    # Показываем текущий текст задачи и просим ввести новый
    current_task = tasks[task_index]
    await callback.message.edit_text(
        f"📝 Редактирование задачи {task_index + 1}:\n\n"
        f"Текущий текст:\n{current_task}\n\n"
        "Введите новый текст для этой задачи:"
    )
    await callback.answer()

# Обработчик ввода нового текста задачи
@dp.message(UserState.editing_plan)
async def process_task_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    task_index = data.get('editing_task_index')
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    
    # Обновляем задачу
    tasks[task_index] = message.text
    await state.update_data(tasks=tasks)
    
    # Показываем обновленный план
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ])
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(f"• {task}" for task in tasks)
    await message.answer(plan_text, reply_markup=keyboard)

# Обработчик завершения редактирования плана
@dp.callback_query(F.data == "finish_plan")
async def finish_plan_editing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    group_id = data.get('group_id')
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ])
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(f"• {task}" for task in tasks)
    await callback.message.edit_text(
        plan_text + "\n\nХотите опубликовать этот план в группу?",
        reply_markup=keyboard
    )
    await state.set_state(UserState.publishing_plan)
    await callback.answer()

# Обработчик публикации плана
@dp.callback_query(UserState.publishing_plan, F.data == "publish_plan")
async def publish_plan(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get('tasks', [])
    current_date = data.get('current_date')
    plan_name = data.get('plan_name')
    group_id = data.get('group_id')
    
    plan_text = f"📅 {current_date}\n📋 {plan_name}\n\n" + "\n".join(f"• {task}" for task in tasks)
    
    # Создаем клавиатуру с кнопкой для работы с планом
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⚙️ Управление планом",
            callback_data=f"manage_plan:{callback.from_user.id}"
        )]
    ])
    
    # Публикуем план в группу
    await bot.send_message(
        chat_id=group_id,
        text=f"🌅 {callback.from_user.mention_html()} опубликовал свой план на сегодня:\n\n{plan_text}",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await callback.message.edit_text("✅ План успешно опубликован в группу!")
    await state.clear()
    await callback.answer()

# Обработчик для работы с планом
async def show_plan_editor(message: Message, state: FSMContext, plan_data: dict):
    # Разбиваем текст плана на задачи
    tasks = plan_data['plan_text'].split('\n')
    
    # Сохраняем данные в состояние
    await state.update_data(
        selected_plan=plan_data,
        tasks=tasks,
        plan_name=plan_data['name']
    )
    
    # Показываем редактор плана
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать задачи", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan_creation")]
    ])
    
    plan_text = "📋 Ваш план:\n\n" + "\n".join(f"• {task}" for task in tasks)
    await message.edit_text(plan_text, reply_markup=keyboard)

# Обработчик выбора существующих планов
@dp.callback_query(UserState.choosing_plan_type, F.data == "use_existing_plan")
async def show_existing_plans(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Базовые планы", callback_data="select_base_plans")],
        [InlineKeyboardButton(text="Мои планы", callback_data="select_user_plans")]
    ])
    
    await callback.message.edit_text("Выберите тип существующего плана:", reply_markup=keyboard)
    await callback.answer()

# Обработчик выбора базовых планов
@dp.callback_query(F.data == "select_base_plans")
async def show_base_plans(callback: CallbackQuery):
    logging.info("Обработчик show_base_plans вызван.")
    base_plans = get_base_plan()  # Получаем базовые планы
    
    if not base_plans:
        await callback.message.edit_text("Базовые планы не найдены.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:base:{plan['id']}")]
        for plan in base_plans
    ])
    
    await callback.message.edit_text("Выберите базовый план:", reply_markup=keyboard)
    await callback.answer()

# Обработчик выбора пользовательских планов
@dp.callback_query(F.data == "select_user_plans")
async def show_user_plans(callback: CallbackQuery, state: FSMContext):
    logging.info("Пользователь выбрал свои планы.")
    user_plans = get_user_plan(callback.from_user.id)  # Получаем пользовательские планы
    
    if not user_plans:
        await callback.message.edit_text("У вас пока нет сохраненных планов.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=plan['name'], callback_data=f"plan_action:user:{plan['id']}")]
        for plan in user_plans
    ])
    
    await callback.message.edit_text("Выберите свой план:", reply_markup=keyboard)
    await callback.answer()

# Обработчик подтверждения удаления плана
@dp.callback_query(F.data.startswith("confirm_delete_plan:"))
async def confirm_delete_plan(callback: CallbackQuery):
    _, plan_type, plan_id = callback.data.split(':')
    plan_id = int(plan_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_plan:{plan_type}:{plan_id}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"plan_action:{plan_type}:{plan_id}")
        ]
    ])
    
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить этот план?\n"
        "Это действие нельзя будет отменить.",
        reply_markup=keyboard
    )
    await callback.answer()

# Обработчик удаления плана
@dp.callback_query(F.data.startswith("delete_plan:"))
async def delete_plan(callback: CallbackQuery):
    _, plan_type, plan_id = callback.data.split(':')
    plan_id = int(plan_id)
    user_id = callback.from_user.id
    
    try:
        # Удаляем план из базы данных
        delete_user_plan(user_id, plan_id)
        
        # Показываем сообщение об успешном удалении
        await callback.message.edit_text(
            "✅ План успешно удален!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ К списку планов", callback_data="view_user_plans")]
            ])
        )
    except Exception as e:
        logging.error(f"Ошибка при удалении плана: {e}")
        await callback.answer("Произошла ошибка при удалении плана", show_alert=True)
    
    await callback.answer()

# Добавляем обработчик для установки текущего плана
@dp.callback_query(F.data.startswith("set_current_plan:"))
async def set_current_plan(callback: CallbackQuery):
    plan_name = callback.data.split(':')[1]
    user_id = callback.from_user.id
    
    # Обновляем текущий план пользователя
    update_user_current_plan(user_id, plan_name)
    
    await callback.message.edit_text(
        f"✅ План <b>{plan_name}</b> установлен как текущий!",
        parse_mode='HTML'
    )
    await callback.answer("План успешно установлен как текущий!")

# Обработчик кнопки управления планом
@dp.callback_query(F.data.startswith("manage_plan:"))
async def manage_plan_handler(callback: CallbackQuery, state: FSMContext):
    try:
        # Парсим текст плана и сохраняем задачи в состояние
        plan_text = callback.message.text
        lines = plan_text.split('\n')
        
        # Отделяем заголовок (первые 2 строки) и задачи
        header = "\n".join(lines[:2])
        tasks = [line.strip() for line in lines[2:] if line.strip()]
        
        await state.update_data({
            'header': header,
            'tasks': tasks,
            'message_id': callback.message.message_id,
            'chat_id': callback.message.chat.id
        })
        
        # Показываем меню управления
        await show_management_menu(callback.message)
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в manage_plan_handler: {e}")
        await callback.answer("Ошибка при обработке плана", show_alert=True)
    finally:
        await callback.answer()

async def show_management_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметить пункты", callback_data="mark_tasks")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_plan")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_management")]
    ])
    await message.edit_reply_markup(reply_markup=keyboard)

# Обработчик начала отметки задач
@dp.callback_query(PlanManagement.managing_plan, F.data == "mark_tasks")
async def start_marking_tasks(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        tasks = data['tasks']
        
        keyboard = InlineKeyboardBuilder()
        for i, task in enumerate(tasks):
            clean_task = task.replace('✅', '').strip()
            prefix = "✓ " if '✅' in task else f"{i+1}."
            keyboard.add(InlineKeyboardButton(
                text=f"{prefix} {clean_task}",
                callback_data=f"toggle_{i}"
            ))
        
        keyboard.adjust(1)
        keyboard.row(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_manage"
        ))
        
        await callback.message.edit_text(
            "Выберите пункты для отметки:\n(✓ - отмеченные)",
            reply_markup=keyboard.as_markup()
        )
        await state.set_state(PlanManagement.marking_tasks)
    except Exception as e:
        logger.error(f"Ошибка в start_marking_tasks: {e}")
        await callback.answer("Ошибка при загрузке задач", show_alert=True)
    finally:
        await callback.answer()

# Обработчик переключения отметки задачи
@dp.callback_query(PlanManagement.marking_tasks, F.data.startswith("toggle_"))
async def toggle_task_mark(callback: CallbackQuery, state: FSMContext):
    try:
        task_index = int(callback.data.split('_')[1])
        data = await state.get_data()
        tasks = data['tasks']
        
        if task_index >= len(tasks):
            await callback.answer("Неверный номер пункта", show_alert=True)
            return
        
        # Создаем копию задачи до изменения
        original_task = tasks[task_index]
        
        # Переключаем отметку
        if '✅' in original_task:
            new_task = original_task.replace('✅', '').strip()
        else:
            new_task = f"✅ {original_task.replace('✅', '').strip()}"
        
        # Если задача не изменилась (редкий случай, но возможен)
        if new_task == original_task:
            await callback.answer()
            return
            
        # Обновляем задачу в списке
        tasks[task_index] = new_task
        await state.update_data({'tasks': tasks})
        
        # Создаем новую клавиатуру
        keyboard = InlineKeyboardBuilder()
        for i, task in enumerate(tasks):
            clean_task = task.replace('✅', '').strip()
            prefix = "✓ " if '✅' in task else f"{i+1}."
            keyboard.add(InlineKeyboardButton(
                text=f"{prefix} {clean_task}",
                callback_data=f"toggle_{i}"
            ))
        
        keyboard.adjust(1)
        keyboard.row(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_manage"
        ))
        
        # Обновляем только если есть изменения
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard.as_markup())
            await callback.answer(f"Пункт {task_index+1} обновлен")
        except:
            # Если не получилось обновить (например, нет изменений), просто подтверждаем нажатие
            await callback.answer()
            
    except Exception as e:
        logger.error(f"Ошибка в toggle_task_mark: {e}")
        await callback.answer("Ошибка при обновлении", show_alert=True)

# Обработчик возврата к меню управления
@dp.callback_query(F.data == "back_to_manage")
async def back_to_management(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        header = data['header']
        tasks = data['tasks']
        
        full_plan = f"{header}\n" + "\n".join(tasks)
        await callback.message.edit_text(
            full_plan,
            reply_markup=get_management_keyboard()
        )
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в back_to_management: {e}")
        await callback.answer("Ошибка при возврате", show_alert=True)
    finally:
        await callback.answer()

def get_management_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметить пункты", callback_data="mark_tasks"),
         InlineKeyboardButton(text="💬 Комментарии", callback_data="task_comments")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_plan"),
         InlineKeyboardButton(text="❌ Закрыть", callback_data="close_management")]
    ])

# Обработчик закрытия меню
@dp.callback_query(PlanManagement.managing_plan, F.data == "close_management")
async def close_management(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в close_management: {e}")
    finally:
        await callback.answer()


# Обработчик кнопки комментариев
@dp.callback_query(PlanManagement.managing_plan, F.data == "task_comments")
async def task_comments_handler(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        tasks = data['tasks']
        
        keyboard = InlineKeyboardBuilder()
        for i, task in enumerate(tasks):
            # Убираем отметки для отображения
            clean_task = task.replace('✅', '').strip()
            keyboard.add(InlineKeyboardButton(
                text=f"{i+1}. {clean_task[:20]}...",  # Обрезаем длинные названия
                callback_data=f"comment_task_{i}"
            ))
        
        keyboard.adjust(1)
        keyboard.row(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_manage"
        ))
        
        await callback.message.edit_text(
            "Выберите пункт для добавления комментария:",
            reply_markup=keyboard.as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка в task_comments_handler: {e}")
        await callback.answer("Ошибка при загрузке задач", show_alert=True)
    finally:
        await callback.answer()

# Обработчик выбора задачи для комментария
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

# Обработчик текста комментария
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
        
        # Добавляем комментарий к задаче
        task = tasks[task_index]
        if '💬' in task:
            # Удаляем старый комментарий если есть
            task = task.split('💬')[0].strip()
        
        tasks[task_index] = f"{task} 💬{message.text}"
        await state.update_data({'tasks': tasks})
        
        # Обновляем сообщение с планом
        header = data['header']
        full_plan = f"{header}\n" + "\n".join(tasks)
        
        await message.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=full_plan,
            reply_markup=get_management_keyboard()
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
            # Убираем отметки и комментарии для чистого отображения
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
        await state.set_state(PlanManagement.editing_task)  # Устанавливаем состояние редактирования
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
            reply_markup=get_management_keyboard()
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
        await state.set_state(PlanManagement.adding_task)  # Используем новое состояние
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
        
        # Обновляем сообщение с планом
        header = data['header']
        full_plan = f"{header}\n" + "\n".join(tasks)
        
        await message.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=full_plan,
            reply_markup=get_management_keyboard()
        )
        
        await state.set_state(PlanManagement.managing_plan)
    except Exception as e:
        logger.error(f"Ошибка в process_new_task: {e}")
        await message.answer("Ошибка при добавлении пункта")

# Запуск бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())