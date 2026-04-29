import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv() 
BOT_TOKEN = os.getenv("BOT_TOKEN")

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import auth_router
from scheduler import setup_scheduler 

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    if not BOT_TOKEN:
        logging.error("CRITICAL: BOT_TOKEN environment variable is missing!")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(auth_router)
    
    setup_scheduler(bot)
    
    logging.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())