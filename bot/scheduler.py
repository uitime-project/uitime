import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from services.api_service import ApiClient

api = ApiClient()

async def fetch_and_dispatch_reminders(bot: Bot):
    logging.info("Checking for pending reminders...")


    reminders = await api.get_pending_reminders()

    if not reminders:
        return
    
    for reminder in reminders:
        telegram_id = reminder.get("telegramId")
        message_text = reminder.get("message")

        if telegram_id and message_text:
            try:
                
                await bot.send_message(
                    chat_id=telegram_id,
                    text=f"🔔 **UiTime Reminder**\n\n{message_text}"
                )
                logging.info(f"Successfully sent reminder to {telegram_id}")

            except Exception as e:
                logging.error(f"Failed to send reminder to {telegram_id}. Error: {e}")

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()

    scheduler.add_job(fetch_and_dispatch_reminders, 'interval', minutes=15, args=[bot])

    scheduler.start()
    logging.info("APScheduler started. Polling every 15 minutes")
    return scheduler