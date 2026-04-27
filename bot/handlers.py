from aiogram import Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F, Bot
from datetime import datetime

from api_client import ApiClient
from keyboards import get_main_menu

auth_router = Router()
api = ApiClient()

session_db = {}

class RegistrationFSM(StatesGroup):
    waiting_for_invite = State()

def format_schedule(day_title: str, lessons: list) -> str:
    """Formats the JSON list of LessonDtos into a clean Telegram message."""
    if not lessons:
        return f"🏝️ **{day_title}**\n\nYou have no lessons! Enjoy your free time."

    msg = f"📅 **{day_title}**\n\n"
    for i, lesson in enumerate(lessons, 1):
        # Parse the ISO time string from C# (e.g., 2026-04-26T08:00:00Z)
        start_time = datetime.fromisoformat(lesson['startTime'].replace('Z', '+00:00')).strftime('%H:%M')
        end_time = datetime.fromisoformat(lesson['endTime'].replace('Z', '+00:00')).strftime('%H:%M')

        msg += f"**{i}. {lesson['subjectName']}** ({lesson['subjectType']})\n"
        msg += f"🕒 {start_time} - {end_time}\n"
        
        if lesson.get('location'):
            msg += f"📍 {lesson['location']}\n"
        if lesson.get('onlineLink'):
            msg += f"🔗 [Join Online]({lesson['onlineLink']})\n"
        
        msg += "\n"
    return msg

@auth_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    if message.from_user.id in session_db:
        # If they are already logged in, just show them the menu
        await message.answer(
            "Welcome back! What would you like to do?", 
            reply_markup=get_main_menu()
        )
        return

    await message.answer(
        "Welcome to UiTime! 👋\n"
        "Please enter your invite code to get started:"
    )
    await state.set_state(RegistrationFSM.waiting_for_invite)

@auth_router.message(StateFilter(RegistrationFSM.waiting_for_invite))
async def process_invite_code(message: types.Message, state: FSMContext):
    invite_code = message.text
    telegram_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    processing_msg = await message.answer("Verifying code securely with the server... ⏳")
    response = await api.login(telegram_id, username, invite_code)
    
    if response.get("status") == "success":
        jwt_token = response.get("token")
        server_message = response.get("message")
        
        session_db[telegram_id] = jwt_token
        
        # We delete the "Verifying..." message and send a fresh one with the keyboard
        await processing_msg.delete()
        await message.answer(
            f"✅ {server_message}\n\nSelect an option below:",
            reply_markup=get_main_menu()
        )
        await state.clear()
    else:
        await processing_msg.edit_text(f"❌ {response.get('message')}\n\nPlease try again:")

# --- NEW: Schedule Handlers ---

@auth_router.message(lambda message: message.text in ["📅 Today", "📅 Tomorrow"])
async def handle_schedule_buttons(message: types.Message):
    """Catches the custom keyboard button presses for the schedule."""
    token = session_db.get(message.from_user.id)
    
    if not token:
        # Remove the keyboard if they aren't logged in
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
        # disable_web_page_preview stops large link thumbnails from ruining the layout
        await processing_msg.edit_text(schedule_text, disable_web_page_preview=True)
    else:
        await processing_msg.edit_text(f"❌ {response.get('message')}")

@auth_router.message(lambda message: message.text == "📤 Upload Schedule")
async def prompt_upload(message: types.Message):
    """Triggers when he user clicks the Upload button"""
    token = session_db.get(message.from_user.id)
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
    token = session_db.get(message.from_user.id)
    if not token:
        await message.answer("Please log in using /start before uploading a schedule")
        return
    
    document = message.document
    processing_msg = await message.answer("Downloading file from Telegrm... 📥")

    try:
        # Get the file path from servers
        file_info = await bot.get_file(document.file_id)

        # Download the file into memory
        downloaded_file = await bot.download_file(file_info.file_path)
        file_bytes = downloaded_file.read()

        await processing_msg.edit_text("Uploading to the Uitime Server... 📥")

        # Send it ti the C# Backend
        response = await api.upload_schedule(token, file_bytes, document.file_name)

        # Report the results
        if response.get("status") == "success":
            await processing_msg.edit_text(f"✅ {response.get('message')}")
        else:
            await processing_msg.edit_text(f"❌ Error: {response.get('message')}")

    except Exception as e:
        await processing_msg.edit_text("❌ Failed to process the document. Please try again")