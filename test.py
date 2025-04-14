from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
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

# Загрузка конфигурации
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация БД
create_tables()

# ========== СОСТОЯНИЯ ==========
class UserStates(StatesGroup):
    # Основные состояния
    waiting_nickname = State()
    choosing_plan_type = State()
    
    # Создание плана
    creating_plan = State()
    entering_plan_title = State()
    entering_plan_tasks = State()
    
    # Редактирование плана
    editing_plan = State()
    adding_task = State()
    editing_task = State()
    
    # Просмотр планов
    viewing_plans = State()
    selecting_plan = State()

# ========== КЛАВИАТУРЫ ==========
def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура главного меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои планы", callback_data="view_user_plans")],
        [InlineKeyboardButton(text="Базовые планы", callback_data="view_base_plans")],
        [InlineKeyboardButton(text="Создать план", callback_data="create_plan")],
        [InlineKeyboardButton(text="Текущий план", callback_data="current_plan")]
    ])

def get_plan_types_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа плана"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Базовые планы", callback_data="view_base_plans")],
        [InlineKeyboardButton(text="Мои планы", callback_data="view_user_plans")]
    ])

def get_plan_actions_kb() -> InlineKeyboardMarkup:
    """Клавиатура действий с планом"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_tasks")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_plan")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plan")]
    ])

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    args = message.text.split()
    
    # Обработка deep link для группового плана
    if len(args) > 1 and args[1].startswith('newday_'):
        group_id = int(args[1].split('_')[1])
        await state.update_data(group_id=group_id)
        await show_plan_options(message, state)
        return
    
    # Обычный старт
    user_id = message.from_user.id
    user_name = get_user_name(user_id)
    
    if not user_name:
        await message.answer('Привет! Я бот для планирования. Как тебя зовут?')
        await state.set_state(UserStates.waiting_nickname)
    else:
        await message.answer(f"Привет, {user_name}! Чем помочь?", reply_markup=get_main_menu_kb())

@dp.message(Command('help'))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📌 Доступные команды:\n"
        "/start - Начало работы\n"
        "/help - Эта справка\n"
        "/create_plan - Создать новый план\n"
        "/view_plans - Просмотреть планы\n"
        "/info - О пользе планирования"
    )
    await message.answer(help_text, reply_markup=get_main_menu_kb())

@dp.message(Command('info'))
async def cmd_info(message: Message):
    """Обработчик команды /info"""
    info_text = (
        "📝 Планирование помогает:\n\n"
        "• Увеличить продуктивность\n"
        "• Снизить стресс\n"
        "• Лучше организовать время\n\n"
        "Попробуйте создать свой первый план!"
    )
    await message.answer(info_text)

# ========== ОБРАБОТКА НИКА ==========
@dp.message(UserStates.waiting_nickname)
async def process_nickname(message: Message, state: FSMContext):
    """Сохранение ника пользователя"""
    user_id = message.from_user.id
    user_nick = message.text.strip()
    
    if not user_nick:
        await message.answer("Пожалуйста, введите корректное имя")
        return
    
    save_user_name(user_id, user_nick)
    await message.answer(f"Отлично, {user_nick}!", reply_markup=get_main_menu_kb())
    await state.clear()

# ========== РАБОТА С ПЛАНАМИ ==========
@dp.callback_query(F.data == 'create_plan')
async def start_plan_creation(callback: CallbackQuery, state: FSMContext):
    """Начало создания плана"""
    await callback.message.answer("📝 Введите название для нового плана:")
    await state.set_state(UserStates.entering_plan_title)
    await callback.answer()

@dp.message(UserStates.entering_plan_title)
async def process_plan_title(message: Message, state: FSMContext):
    """Обработка названия плана"""
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте еще:")
        return
    
    await state.update_data(title=title)
    await message.answer(
        "✏️ Теперь введите задачи (каждая с новой строки):\n\n"
        "Пример:\n• Зарядка\n• Завтрак\n• Работа"
    )
    await state.set_state(UserStates.entering_plan_tasks)

@dp.message(UserStates.entering_plan_tasks)
async def process_plan_tasks(message: Message, state: FSMContext):
    """Обработка задач плана"""
    tasks = [t.strip() for t in message.text.split('\n') if t.strip()]
    if not tasks:
        await message.answer("Должна быть хотя бы одна задача. Попробуйте еще:")
        return
    
    data = await state.get_data()
    plan_text = "\n".join(f"• {task}" for task in tasks)
    
    # Формируем предпросмотр плана
    preview = f"📋 <b>{data['title']}</b>\n\n{plan_text}\n\nСохранить?"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="confirm_plan")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="cancel_plan")]
    ])
    
    await message.answer(preview, parse_mode='HTML', reply_markup=keyboard)
    await state.update_data(tasks=tasks)
    await state.set_state(UserStates.creating_plan)

@dp.callback_query(UserStates.creating_plan, F.data == 'confirm_plan')
async def confirm_plan_creation(callback: CallbackQuery, state: FSMContext):
    """Подтверждение создания плана"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Сохраняем план
    save_user_plan(
        user_id=user_id,
        name=data['title'],
        text="\n".join(data['tasks'])
    )
    
    await callback.message.edit_text(f"✅ План '{data['title']}' сохранен!")
    await state.clear()
    await callback.answer()

# ========== ПРОСМОТР ПЛАНОВ ==========
@dp.callback_query(F.data.in_(['view_user_plans', 'view_base_plans']))
async def view_plans(callback: CallbackQuery, state: FSMContext):
    """Просмотр списка планов"""
    plan_type = callback.data.split('_')[1]  # 'user' или 'base'
    
    if plan_type == 'user':
        plans = get_user_plan(callback.from_user.id)
        title = "Ваши планы:"
    else:
        plans = get_base_plan()
        title = "Базовые планы:"
    
    if not plans:
        await callback.answer("Нет доступных планов")
        return
    
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.add(InlineKeyboardButton(
            text=plan['name'],
            callback_data=f"select_{plan_type}_plan:{plan['id']}"
        ))
    
    builder.adjust(1)
    await callback.message.edit_text(
        title,
        reply_markup=builder.as_markup()
    )
    await state.set_state(UserStates.viewing_plans)
    await callback.answer()

@dp.callback_query(UserStates.viewing_plans, F.data.startswith('select_'))
async def select_plan(callback: CallbackQuery, state: FSMContext):
    """Выбор конкретного плана"""
    _, plan_type, plan_id = callback.data.split(':')
    plan_id = int(plan_id)
    
    # Получаем план из БД
    if plan_type == 'user':
        plan = next((p for p in get_user_plan(callback.from_user.id) if p['id'] == plan_id), None)
    else:
        plan = next((p for p in get_base_plan() if p['id'] == plan_id), None)
    
    if not plan:
        await callback.answer("План не найден")
        return
    
    # Показываем план с кнопками действий
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать как текущий", callback_data=f"use_{plan_type}_plan:{plan_id}")],
        [InlineKeyboardButton(text="← Назад", callback_data=f"view_{plan_type}_plans")]
    ])
    
    await callback.message.edit_text(
        f"📋 <b>{plan['name']}</b>\n\n{plan['plan_text']}",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.startswith('use_'))
async def use_plan(callback: CallbackQuery):
    """Установка плана как текущего"""
    _, plan_type, plan_id = callback.data.split(':')
    plan_id = int(plan_id)
    
    # Получаем название плана
    if plan_type == 'user':
        plan = next((p for p in get_user_plan(callback.from_user.id) if p['id'] == plan_id), None)
    else:
        plan = next((p for p in get_base_plan() if p['id'] == plan_id), None)
    
    if not plan:
        await callback.answer("План не найден")
        return
    
    # Сохраняем как текущий
    update_user_current_plan(callback.from_user.id, plan['name'])
    await callback.message.edit_text(
        f"✅ План '{plan['name']}' установлен как текущий!",
        parse_mode='HTML'
    )
    await callback.answer()

# ========== ТЕКУЩИЙ ПЛАН ==========
@dp.callback_query(F.data == 'current_plan')
async def show_current_plan(callback: CallbackQuery):
    """Показ текущего плана пользователя"""
    user_id = callback.from_user.id
    plan_name = get_current_plan(user_id)
    
    if not plan_name:
        await callback.answer("У вас нет активного плана")
        return
    
    plan_text = get_plan_text_by_name(plan_name)
    if plan_text:
        await callback.message.answer(f"📋 Текущий план: {plan_name}\n\n{plan_text}")
    else:
        await callback.message.answer("Не удалось загрузить план")
    await callback.answer()

# ========== ГРУППОВЫЕ ФУНКЦИИ ==========
@dp.message(Command('new_day'), F.chat.type.in_({"group", "supergroup"}))
async def new_day_group(message: Message):
    """Создание нового дня в группе"""
    try:
        bot_username = (await bot.get_me()).username
        deep_link = f"https://t.me/{bot_username}?start=newday_{message.chat.id}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Создать план", url=deep_link)],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_new_day")]
        ])
        
        await message.reply(
            f"🌅 {message.from_user.mention_html()} начинает новый день!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в new_day_group: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

# ========== ЗАПУСК БОТА ==========
async def main():
    """Основная функция запуска бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())