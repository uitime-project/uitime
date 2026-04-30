import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv() 
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from handlers.handlers import auth_router 
from scheduler import setup_scheduler 

async def on_startup(bot: Bot):
    if not WEBHOOK_URL:
        logging.error("WEBHOOK_URL is missing! Check RENDER_EXTERNAL_URL env variable.")
        return

    try:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        logging.info(f"Webhook securely set to {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")

    setup_scheduler(bot)
    logging.info("Scheduler started successfully.")

async def on_shutdown(bot: Bot):
    logging.info("Shutting down... Removing webhook.")
    await bot.delete_webhook()

def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    if not BOT_TOKEN:
        logging.error("CRITICAL: BOT_TOKEN is missing!")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(auth_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    async def health_check(request):
        return web.Response(text="Bot is alive!", status=200)
    
    app.router.add_get("/", health_check)

    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    port = int(os.environ.get("PORT", 10000))
    logging.info(f"Starting web app on port {port}...")
    web.run_app(app, host="0.0.0.0", port=port, access_log=None)

if __name__ == "__main__":
    main()