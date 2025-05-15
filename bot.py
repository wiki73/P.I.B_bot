from aiogram import Bot, Dispatcher
import asyncio
from config import load_config, set_bot_commands
from database import *
from keyboards import *
from models import init_db
from handlers import base, plans, statistics, user
from scripts.init_db import create_default_plans


async def main():
    init_db()
    create_default_plans()
    config = load_config()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    
    # Register routers in correct order - from most specific to most general
    dp.include_router(user.router)  # User-specific handlers first
    dp.include_router(plans.router)  # Then plan-related handlers
    dp.include_router(statistics.router)  # Then statistics
    dp.include_router(base.router)  # Base handlers with catch-all last
    
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())