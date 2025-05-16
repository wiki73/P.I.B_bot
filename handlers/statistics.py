from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.statistics import get_group_statistics_by_chat_id, get_user_lifetime_statistics


router = Router()


@router.message(Command('static'))
async def show_statistics(message: Message):
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    if message.chat.type in ["group", "supergroup"]:
        completed_stats = get_group_statistics_by_chat_id(message.chat.id)

        if completed_stats['total_completed'] == 0 and completed_stats['total_study_hours'] == 0:
           await message.answer("📊 В этой группе пока нет статистики!")
           return

        await message.answer(
            f"📊 Статистика группы на {current_date}:\n\n"
            f"✅ Всего выполнено задач: {completed_stats['total_completed']}\n"
            f"📚 Общее время обучения: {completed_stats['total_study_hours']:.1f} ч."
        )
    else:
        statistics = get_user_lifetime_statistics(message.from_user.id)
        
        if statistics['total_completed'] == 0 and statistics['total_study_hours'] == 0:
            await message.answer("📊 У вас пока нет статистики!")
            return
            
        await message.answer(
            f"📊 Ваша статистика на {current_date}:\n\n"
            f"✅ Всего выполнено задач: {statistics['total_completed']}\n"
            f"📚 Общее время обучения: {statistics['total_study_hours']:.1f} ч."
        )