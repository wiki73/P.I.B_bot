from aiogram.types import BotCommand

BOT_COMMANDS = [
    BotCommand(command="start", description="Запуск бота"),
    BotCommand(command="help", description="Помощь"),
    BotCommand(command="info", description="О планировании"),
    BotCommand(command="create_plan", description="Создать новый план"),
    BotCommand(command="view_plans", description="Посмотреть планы"),
]

async def set_bot_commands(bot):
    await bot.set_my_commands(BOT_COMMANDS)