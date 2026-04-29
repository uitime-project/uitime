from aiogram import Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F, Bot
from aiogram.types import LinkPreviewOptions
from datetime import datetime

from services.api_client import ApiClient
from keyboards.keyboards import get_main_menu
from services.storage import db 

auth_router = Router()
api = ApiClient()

class RegistrationFSM(StatesGroup):
    waiting_for_invite = State()

def format_schedule(day_title: str, lessons: list) -> str:
    if not lessons:
        return f"🏝️ <b>{day_title}</b>\n\nYou have no lessons! Enjoy your free time."

    msg = f"📅 <b>{day_title}</b>\n\n"
    for i, lesson in enumerate(lessons, 1):
        start_time = datetime.fromisoformat(lesson['startTime']).strftime('%H:%M')
        end_time = datetime.fromisoformat(lesson['endTime']).strftime('%H:%M')

        msg += f"<b>{i}. {lesson['subjectName']}</b> ({lesson['subjectType']})\n"
        msg += f"🕒 {start_time} - {end_time}\n"
        
        if lesson.get('location'):
            msg += f"📍 {lesson['location']}\n"
        if lesson.get('onlineLink'):
            msg += f"🔗 <a href='{lesson['onlineLink']}'>Join Online</a>\n"
        
        msg += "\n"
    return msg


@auth_router.message(lambda message: message.text in ["📅 Today", "📅 Tomorrow"])
async def handle_schedule_buttons(message: types.Message):
    token = db.get(message.from_user.id)
    
    if not token:
        await message.answer(
            "Your session has expired. Please type /start to log in again.", 
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    processing_msg = await message.answer("Fetching your schedule... 📥")

    if message.text == "📅 Today":
        response = await api.get_today_schedule(token)
        day_title = "Today's Schedule"
    else:
        response = await api.get_tomorrow_schedule(token)
        day_title = "Tomorrow's Schedule"

    if response.get("status") == "success":
        schedule_text = format_schedule(day_title, response.get("data", []))

        await processing_msg.edit_text(
            schedule_text, 
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    else:
        await processing_msg.edit_text(f"❌ {response.get('message')}")

@auth_router.message(lambda message: message.text == "📤 Upload Schedule")
async def prompt_upload(message: types.Message):
    """Triggers when the user clicks the Upload button"""
    token = db.get(message.from_user.id)
    if not token:
        await message.answer("Your session has expired. Please type /start to log in")
        return
    
    await message.answer(
        "Please send me your schedule file as a **Document** 📎.\n\n"
        "*(Don't send it as a photo, use the 'File' or 'Document' option)*"
    )

@auth_router.message(F.document)
async def handle_schedule_document(message: types.Message, bot: Bot):
    """Catches any document sent to the bot and forwards it to the C# API"""
    token = db.get(message.from_user.id)
    if not token:
        await message.answer("Please log in using /start before uploading a schedule")
        return
    
    document = message.document
    processing_msg = await message.answer("Downloading file from Telegram... 📥")

    try:
        file_info = await bot.get_file(document.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        file_bytes = downloaded_file.read()

        await processing_msg.edit_text("Uploading to the Uitime Server... 📥")

        response = await api.upload_schedule(token, file_bytes, document.file_name)

        if response.get("status") == "success":
            await processing_msg.edit_text(f"✅ {response.get('message')}")
        else:
            await processing_msg.edit_text(f"❌ Error: {response.get('message')}")

    except Exception as e:
        await processing_msg.edit_text("❌ Failed to process the document. Please try again")