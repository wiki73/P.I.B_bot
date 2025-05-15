from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router()


@router.message(Command('static'))
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