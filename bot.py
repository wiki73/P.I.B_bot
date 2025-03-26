from aiogram import Bot, Dispatcher, types
from aiogram import F
import asyncio
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from database import create_tables, get_user_name, save_user_name, save_user_plan, get_user_plan,get_base_plan,get_plan_name_by_id,update_user_current_plan, get_current_plan, get_db_connection,get_plan_text_by_name

TOKEN = '7947948717:AAF_yeOpDDLoOCrTUWQRzb_akKx05xWpNVU'
bot = Bot(token=TOKEN)
dp = Dispatcher()
create_tables()


chech_name = False
chech_new_plan = False
chech_create_plan = False
chech_change_plan = False
chech_base_plan = False

@dp.message(Command('start'))
async def start_command(message: types.Message):
    print("Команда /start")
    global chech_name
    user_id = message.from_user.id
    user_name = get_user_name(user_id)
    
    if user_name is None:
        await message.reply('Еу. Я твой бот для рассписания, меня завут P.I.B(пиб) - все названия и вся кринжовость текста связанная с моим создателем я думаю ты его знаешь). Я вижу тебя первый раз, так что давай для начала узнаем как мне тебя называть. Мой создатель назвал себя хер и я его теперь пеостоянно так назваю. Не будь как этот конч и давай ка придумай что-нибудь прикольное. ')
        await message.reply("Напиши ник")
        chech_name = True # Ожидание сообщения с ником
        
    else:
        await message.reply(f"Еу, {user_name}! Я твой бот для рассписания, меня завут P.I.B(пиб) - все названия и вся кринжовость текста связанная с моим создателем я думаю ты его знаешь). Чем могу помочь?Если что попробуй написать /help")


@dp.message(Command('help'))
async def help_command(message: types.Message):
    print("Команда /help")
    await message.reply("Доступные команды:\n"
                       "/start - Начать работу с ботом\n"
                       "/help - Показать это сообщение\n "
                       "/info - Получить информацию о планировании\n"
                       "/check_current_plan - Посмотреть актуальный план\n"
                       "/view_base_plans - Посмотреть базовые планы\n"
                       "/choose_plan - Выбрать или изменить план\n"
                       "/create_plan - Создать план\n ")


@dp.message(Command('create_plan'))
async def create_plan_command(message: types.Message):
    print("Команда /create_plan")
    global chech_create_plan
    await message.reply("Пожалуйста, введите текст вашего плана:")
    chech_create_plan = True   # Устанавливаем состояние ожидания плана

# Обработчик команды /view_base_plans
@dp.message(Command('view_base_plans'))
async def view_base_plans_command(message: types.Message):
    global chech_base_plan
    base_plans = get_base_plan() # Получаем план п
    if base_plans:
        for plan in base_plans:
            await message.reply(plan[1])
            await message.reply(plan[0])
        await message.reply("Вот планы, если хотите выберите один из них, просто напиши 1, 2, 3 или 4")
        chech_base_plan = True
    else:
        await message.reply("У вас нет сохраненных планов.")

                       
# Обработчик команды для выбора плана
@dp.message(Command('choose_plan'))
async def choose_plan_command(message: types.Message):
    global chech_change_plan, chech_new_plan
    print("Команда /choose_plan")
    user_id = message.from_user.id
    current_plan = get_user_plan(user_id)
    
    if current_plan:
        await message.reply(f"У вас уже выбран план: {current_plan}. Хотите его изменить? (да/нет)")
        chech_change_plan = True
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Базовый план", callback_data='base_plan')],
            [InlineKeyboardButton(text="Авторский план", callback_data='current_plan')]
        ])

        await message.reply("Выберите вид плана:", reply_markup=keyboard)

# Обработчик нажатий на инлайн-кнопки
@dp.callback_query(lambda c: c.data in ['base_plan', 'current_plan'])
async def process_plan_selection(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)  # Подтверждаем нажатие кнопки

    if callback_query.data == 'base_plan':
        await bot.send_message(callback_query.from_user.id, "Вы выбрали Базовый план.")
        
        # Получаем все базовые планы
        base_plans = get_base_plan()  # Получаем планы из базы данных
        
        if base_plans:
            for plan in base_plans:
                await bot.send_message(callback_query.from_user.id, plan[1])
                await bot.send_message(callback_query.from_user.id, plan[0])

            # Создаем кнопки для каждого плана
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=plan[1], callback_data=plan[1]) for plan in base_plans]
            ])
            await bot.send_message(callback_query.from_user.id, "Выберите план:", reply_markup=keyboard)
        else:
            await bot.send_message(callback_query.from_user.id, "Нет доступных базовых планов.")

    elif callback_query.data == 'current_plan':
        await bot.send_message(callback_query.from_user.id, "Вы выбрали Актуальный план.")
        
        # Получаем все авторские планы
        user_id = callback_query.from_user.id
        auth_plans = get_user_plan(user_id)  # Получаем планы из базы данных
        
        if auth_plans:
            for plan in auth_plans:
                await bot.send_message(callback_query.from_user.id, plan[1])
                await bot.send_message(callback_query.from_user.id, plan[0])

            # Создаем кнопки для каждого плана
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=plan[1], callback_data=plan[1]) for plan in auth_plans]
            ])
            await bot.send_message(callback_query.from_user.id, "Выберите план:", reply_markup=keyboard)
        else:
            await bot.send_message(callback_query.from_user.id, "Нет доступных авторских планов.")

@dp.callback_query(lambda c: c.data in [plan[1] for plan in get_base_plan()])
async def handle_plan_selection(callback_query: CallbackQuery):
    selected_plan = callback_query.data
    name_plan = selected_plan
    user_id = callback_query.from_user.id
    update_user_current_plan(user_id,name_plan)
    await bot.send_message(callback_query.from_user.id, f"Вы выбрали план: {selected_plan}.")
    # Здесь можно добавить логику для обработки выбранного планаe

# Обработчик выбора плана
@dp.callback_query(lambda c: c.data in [plan[1] for plan in get_user_plan(c.from_user.id)])
async def handle_plan_selection(callback_query: CallbackQuery):
    selected_plan = callback_query.data
    name_plan = selected_plan
    user_id = callback_query.from_user.id  # Получаем ID пользователя
    update_user_current_plan(user_id, name_plan)  # Обновляем текущий план пользователя
    await bot.send_message(user_id, f"Вы выбрали план: {name_plan}.")  # Отправляем сообщение пользователю


# Обработчик команды /info
@dp.message(Command('info'))
async def info_command(message: types.Message):
    print("Команда /info")
    user_id = message.from_user.id
    user_name = get_user_name(user_id)
    
    if user_name is None:
        await message.reply('Ваше имя еще не установлено. Пожалуйста, используйте команду /start, чтобы ввести его.')
    else:
        await message.reply(f'{user_name}, давай подумаем, а зачем нам вообще нужно планировать? Ведь если подумать — ты каждый день тратишь определённое время на написание плана на день, и появляется вопрос — а зачем это надо? Но мой создатель неплохо так изучил этот вопрос и, главное, проверил планирование в жизни. Если не веришь этому "херу с горы", то послушай 100 роликов (которые он посмотрел) и убедись в этом.\n\n1.  Те 5 минут, которые ты тратишь на составление плана, спасают тебя от суеты посреди дня. Сам подумай, когда тебе легче: когда ты знаешь, что тебе нужно сделать с утра, и, сделав одно, переходишь к другому? Или ты проснулся, думаешь, что тебе надо сделать, сделал это, а потом опять думаешь, и так далее? И при этом поверь мне, ты суетишься, и это отнимает в десятки раз больше времени, чем 5 минут.\n\n2.  Ты можешь думать: Я такая свободная личность, мне бы летать, а я сам себя в клетку сажаю? Нет, тебе так кажется. План как раз освобождает тебя. Ты же знаешь, что "Делу время, а потехе час". Так вот, если ты чётко поставь делу время, то, во-первых, сократишь его, а во-вторых, ты точно будешь знать, когда настанет время для "потехи". В итоге на залипание в стену будет больше времени.\n\n3.  Само дисциплина. Очень полезный навык. Как он работает? Да вот как: когда ты сам написал себе план, будь добр его выполнить. Пусть твоё слово что-то значит. Ты оцениваешь свои возможности, ты ставишь приоритеты, и ты управляешь временем, а не наоборот.На самом деле, очень много плюсов. Если ты хочешь узнать больше, то спроси у "хера с горы", который меня создал.')

@dp.message(Command('check_current_plan'))
async def check_current_plan_command(message: types.Message):
    print('команда - check_current_plan')
    user_id = message.from_user.id
    current_plan_name = get_current_plan(user_id)
    print(current_plan_name)
    if current_plan_name:
        # Получаем текст плана из base_plans с помощью новой функции. Или если в base_plans нет то в user_plan
        plan_text = get_plan_text_by_name(current_plan_name)
        if plan_text:
            await message.reply(f"Ваш текущий план: {current_plan_name}\n\n{plan_text}")
        else:
            await message.reply("План не найден в базе данных.")
    else:
        await message.reply("У вас нет текущего плана.")

# Обработчик текстовых сообщений для выбора плана
@dp.message()
async def handle_plan_selection(message: types.Message):
    global chech_name, chech_new_plan, chech_create_plan, chech_change_plan, chech_base_plan
    user_id = message.from_user.id
    current_plan = get_user_plan(user_id)
    if chech_name:
        user_id = message.from_user.id
        user_nick = message.text
        save_user_name(user_id, user_nick)
        await message.reply(f"Умничка,{user_nick}")
        await message.reply(f'Давай подумаем, а зачем нам вообще нужно планировать? Ведь если подумать — ты каждый день тратишь определённое время на написание плана на день, и появляется вопрос — а зачем это надо? Но мой создатель неплохо так изучил этот вопрос и, главное, проверил планирование в жизни. Если не веришь этому "херу с горы", то послушай 100 роликов (которые он посмотрел) и убедись в этом.\n1.Те 5 минут, которые ты тратишь на составление плана, спасают тебя от суеты посреди дня. Сам подумай, когда тебе легче: когда ты знаешь, что тебе нужно сделать с утра, и, сделав одно, переходишь к другому? Или ты проснулся, думаешь, что тебе надо сделать, сделал это, а потом опять думаешь, и так далее? И при этом поверь мне, ты суетишься, и это отнимает в десятки раз больше времени, чем 5 минут.\n2.Ты можешь думать: Я такая свободная личность, мне бы летать, а я сам себя в клетку сажаю? Нет, тебе так кажется. План как раз освобождает тебя. Ты же знаешь, что "Делу время, а потехе час". Так вот, если ты чётко поставь делу время, то, во-первых, сократишь его, а во-вторых, ты точно будешь знать, когда настанет время для "потехи". В итоге на залипание в стену будет больше времени.\n3.Само дисциплина. Очень полезный навык. Как он работает? Да вот как: когда ты сам написал себе план, будь добр его выполнить. Пусть твоё слово что-то значит. Ты оцениваешь свои возможности, ты ставишь приоритеты, и ты управляешь временем, а не наоборот.На самом деле, очень много плюсов. Если ты хочешь узнать больше, то спроси у "хера с горы", который меня создал.')
        chech_name = False

    elif chech_new_plan:
        if message.text in ['1', '2', '3']:
            plan_types = { '1': 'lite', '2': 'med', '3': 'hard' }
            selected_plan = plan_types[message.text]

            if current_plan:
                await message.reply(f"Вы действительно хотите изменить план с {current_plan} на {selected_plan}? (да/нет)")
            else:
                save_user_plan(user_id, selected_plan)
                await message.reply(f"Вы выбрали план: {selected_plan}.")
        elif current_plan and message.text.lower() == 'да':
            save_user_plan(user_id, selected_plan)
            await message.reply(f"План успешно изменен на: {selected_plan}.")
        elif current_plan and message.text.lower() == 'нет':
            await message.reply("Вы оставили текущий план без изменений.")
        else:
            await message.reply("Пожалуйста, выберите 1, 2 или 3 для выбора плана.")
        chech_new_plan = False
    elif chech_create_plan:
        test = (message.text).split('\n')
        name_plan = test[0]
        text_plan = '\n'.join(test[1:])
        save_user_plan(user_id,name_plan,text_plan)
        await message.reply(f"Ваш план сохранен: {message.text}.")
        chech_create_plan = False
    elif chech_change_plan:
        if message.text.lower() == 'да':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Базовый план", callback_data='base_plan')],
                [InlineKeyboardButton(text="Актуальный план", callback_data='current_plan')]
            ])
            await message.reply("Какой план хотите посмотреть:", reply_markup=keyboard)
        chech_change_plan = False
    elif chech_base_plan:
        id_plan = message.text
        name_plan = get_plan_name_by_id(id_plan)
        user_id = message.from_user.id
        update_user_current_plan(user_id,name_plan)
        await message.reply(f"Ура. План выбран")

        chech_base_plan = False



def get_text_plan(plan):
    pass


# Функция запуска бота
async def main():
    print('Бот запущен...')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 