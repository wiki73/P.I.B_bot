from aiogram import Bot, Dispatcher
import asyncio
from config import load_config, set_bot_commands
from database import *
from keyboards import *
from database.models import init_db
from handlers import base, plans, statistics, user
from database.init_db import create_default_plans


async def main():
    init_db()
    create_default_plans()
    config = load_config()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.include_router(user.router)
    dp.include_router(plans.router)
    dp.include_router(statistics.router)
    dp.include_router(base.router)

    await set_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
