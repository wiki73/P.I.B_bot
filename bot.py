from aiogram import Bot, Dispatcher, types,F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message,InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from database import create_tables, get_user_name, save_user_name, save_user_plan, get_user_plan, get_base_plan, get_plan_name_by_id, update_user_current_plan, get_current_plan, get_db_connection, get_plan_text_by_name
from dotenv import load_dotenv
import os
from database import get_user_name, save_user_name,get_base_plan,get_plan_name_by_id,save_user_plan,get_user_plan,update_user_current_plan,get_current_plan,get_plan_text_by_name

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаем таблицы в БД при запуске
create_tables()

# Состояния пользователя
class UserState(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_plan_title = State()
    waiting_for_plan_tasks = State()
    waiting_for_base_plan_choice = State()
    waiting_for_confirm = State()

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
# @dp.message()
# async def auto_keyboard(message: Message):
#     if message.chat.type == "private" and not message.text.startswith('/'):
#         await message.answer("Выберите команду:", reply_markup=personal_keyboard)
#     elif message.chat.type in {"group", "supergroup"} and not message.text.startswith('/'):
#         await message.answer("Используйте групповые команды:", reply_markup=group_keyboard)

# Обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = get_user_name(user_id)
    
    if user_name is None:
        await message.answer('Привет! Я твой бот для планирования. Как мне тебя называть?')
        await state.set_state(UserState.waiting_for_nickname)
    else:
        await message.answer(f"Привет, {user_name}! Чем могу помочь?")
        await show_main_menu(message)

# Главное меню
async def show_main_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои планы", callback_data="my_plans")],
        [InlineKeyboardButton(text="Базовые планы", callback_data="base_plans")],
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

# Обработчик авторсикх планов для start
@dp.callback_query(F.data == 'my_plans')
async def show_user_plans(callback: CallbackQuery, state: FSMContext):
    user_plans = get_user_plan(callback.from_user.id)
    
    if not user_plans:
        await callback.message.answer("У вас пока нет сохраненных планов.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=plan['name'], callback_data=f"select_plan:user:{plan['id']}")]
        for plan in user_plans
    ])
    
    await callback.message.answer("Выберите свой план:", reply_markup=keyboard)
    await callback.answer()

# Обработчик базовых планов для start
@dp.callback_query(F.data == 'base_plans')
async def show_base_plans(callback: CallbackQuery, state: FSMContext):
    base_plans = get_base_plan()
    
    if not base_plans:
        await callback.message.answer("Нет доступных базовых планов.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=plan[1], callback_data=f"select_base_{plan[0]}")]
        for plan in base_plans
    ])
    await callback.message.answer("Выберите базовый план:", reply_markup=keyboard)
    await callback.answer()

# Обработчик выбора базового плана для start
@dp.callback_query(F.data.startswith('select_base_'))
async def select_base_plan(callback: CallbackQuery):
    plan_id = int(callback.data.split('_')[-1])
    plan_name = get_plan_name_by_id(plan_id)
    user_id = callback.from_user.id
    
    update_user_current_plan(user_id, plan_name)
    await callback.message.answer(f"Вы выбрали план: {plan_name}")
    await callback.answer()

# Создание плана - шаг 1
@dp.callback_query(F.data == 'create_plan')
async def create_plan_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название для нового плана:")
    await state.set_state(UserState.waiting_for_plan_title)
    await callback.answer()

# Создание плана - шаг 2
@dp.message(UserState.waiting_for_plan_title)
async def process_plan_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Теперь введите задачи плана (каждая задача с новой строки):")
    await state.set_state(UserState.waiting_for_plan_tasks)

# Создание плана - шаг 3
@dp.message(UserState.waiting_for_plan_tasks)
async def process_plan_tasks(message: Message, state: FSMContext):
    data = await state.get_data()
    plan_title = data['title']
    tasks = message.text.split('\n')
    
    # Сохраняем план в БД
    save_user_plan(
        user_id=message.from_user.id,
        plan_name=plan_title,
        plan_text='\n'.join(tasks)
    )
    
    await message.answer(f"План '{plan_title}' успешно создан!")
    await state.clear()

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

class PlanCreation(StatesGroup): # начало обработки создания плана
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

# Обработчик ввода названия плана
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

# Обработчик ввода задач плана
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
            plan_name=data['title'],
            plan_text=data['tasks']
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
    base_plans = get_base_plan()
    
    if not base_plans:
        await callback.message.edit_text("Базовые планы не найдены.")
        return
    
    builder = InlineKeyboardBuilder()
    
    for plan in base_plans:
        builder.add(
            types.InlineKeyboardButton(
                text=plan['name'],
                callback_data=f"select_plan:base:{plan['id']}"
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
async def show_user_plans(callback: types.CallbackQuery):
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
                callback_data=f"select_plan:user:{plan['id']}"
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
async def new_day_command(message: Message):
    await message.answer(
        "📅 Начинаем новый день! Вот что я могу для группы:",
        reply_markup=group_keyboard
    )
    # Здесь будет логика создания общего плана дня

# Обработчик /static для групп
@dp.message(Command('static'), F.chat.type.in_({"group", "supergroup"}))
async def static_command(message: Message):
    await message.answer(
        "📊 Статистика группы:",
        reply_markup=group_keyboard
    )
    # Здесь будет логика показа статистики

# Запуск бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())