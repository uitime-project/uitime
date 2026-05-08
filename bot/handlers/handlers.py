from aiogram import Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F, Bot
from aiogram.types import LinkPreviewOptions
from datetime import datetime, timedelta, date

from services.api_service import ApiClient
from keyboards.keyboards import get_main_menu, get_browser_keyboard, get_settings_keyboard, get_confirm_delete_keyboard
from services.storage_service import db 

auth_router = Router()
api = ApiClient()

class RegistrationFSM(StatesGroup):
    waiting_for_invite = State()

class BrowserFSM(StatesGroup):
    browsing = State()

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

async def get_cached_day(target_date: date, token: str, state: FSMContext) -> list:
    
    data = await state.get_data()
    cache_start_str = data.get("cache_start")
    cache_end_str = data.get("cache_end")
    lessons_cache = data.get("lessons_cache", {})

    target_str = target_date.isoformat()

    if not cache_start_str or target_str < cache_start_str or target_str >= cache_end_str:
        start_date = target_date - timedelta(days=3)
        end_date = target_date + timedelta(days=4)
        
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        response = await api.get_schedule_range(token, start_str, end_str)
        lessons_cache = {}
        
        if response.get("status") == "success":
            for lesson in response.get("data", []):
                lesson_date = lesson['startTime'].split('T')[0]
                if lesson_date not in lessons_cache:
                    lessons_cache[lesson_date] = []
                lessons_cache[lesson_date].append(lesson)

        await state.update_data(
            cache_start=start_str,
            cache_end=end_str,
            lessons_cache=lessons_cache
        )

    return lessons_cache.get(target_str, [])


@auth_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    if db.get(message.from_user.id):
        await message.answer("Welcome back! What would you like to do?", reply_markup=get_main_menu())
        return

    await message.answer("Welcome to UiTime! 👋\nPlease enter your invite code to get started:")
    await state.set_state(RegistrationFSM.waiting_for_invite)

@auth_router.message(StateFilter(RegistrationFSM.waiting_for_invite))
async def process_invite_code(message: types.Message, state: FSMContext):
    invite_code = message.text
    telegram_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    processing_msg = await message.answer("Verifying code securely with the server... ⏳")
    response = await api.login(telegram_id, username, invite_code)
    
    if response.get("status") == "success":
        db.set(telegram_id, response.get("token"))
        await processing_msg.delete()
        await message.answer(f"✅ {response.get('message')}\n\nSelect an option below:", reply_markup=get_main_menu())
        await state.clear()
    else:
        await processing_msg.edit_text(f"❌ {response.get('message')}\n\nPlease try again:")

@auth_router.message(lambda message: message.text in ["📅 Today", "📅 Tomorrow"])
async def handle_schedule_buttons(message: types.Message):
    token = db.get(message.from_user.id)
    if not token:
        return await message.answer("Session expired. Type /start", reply_markup=types.ReplyKeyboardRemove())

    processing_msg = await message.answer("Fetching your schedule... 📥")

    if message.text == "📅 Today":
        response = await api.get_today_schedule(token)
        day_title = "Today's Schedule"
    else:
        response = await api.get_tomorrow_schedule(token)
        day_title = "Tomorrow's Schedule"

    if response.get("status") == "success":
        schedule_text = format_schedule(day_title, response.get("data", []))
        await processing_msg.edit_text(schedule_text, link_preview_options=LinkPreviewOptions(is_disabled=True))
    else:
        await processing_msg.edit_text(f"❌ {response.get('message')}")

@auth_router.message(lambda message: message.text == "🗓️ Week Browser")
async def enter_browser_mode(message: types.Message, state: FSMContext):
    token = db.get(message.from_user.id)
    if not token:
        return await message.answer("Session expired. Type /start")

    processing_msg = await message.answer("Loading browser... ⏳")
    
    current_date = date.today()
    await state.set_state(BrowserFSM.browsing)
    await state.update_data(current_date=current_date.isoformat())

    lessons = await get_cached_day(current_date, token, state)
    
    day_title = current_date.strftime("%A, %d %b %Y")
    schedule_text = format_schedule(day_title, lessons)

    await processing_msg.edit_text(
        schedule_text, 
        reply_markup=get_browser_keyboard(),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@auth_router.callback_query(lambda c: c.data.startswith("browser_"))
async def handle_browser_callbacks(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split("_")[1]

    if action == "exit":
        await callback_query.message.delete()
        await callback_query.message.answer("Exited browser mode.", reply_markup=get_main_menu())
        await state.clear()
        return

    data = await state.get_data()
    current_date_str = data.get("current_date")
    if not current_date_str:
        await callback_query.answer("Session expired. Please restart browser mode.", show_alert=True)
        return

    token = db.get(callback_query.from_user.id)
    current_date = date.fromisoformat(current_date_str)

    if action == "prev":
        current_date -= timedelta(days=1)
    elif action == "next":
        current_date += timedelta(days=1)

    await state.update_data(current_date=current_date.isoformat())

    lessons = await get_cached_day(current_date, token, state)
    
    day_title = current_date.strftime("%A, %d %b %Y")
    schedule_text = format_schedule(day_title, lessons)

    try:
        await callback_query.message.edit_text(
            schedule_text,
            reply_markup=get_browser_keyboard(),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    except Exception:
        pass

    await callback_query.answer()

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

@auth_router.message(lambda message: message.text == "⚙️ Settings")
async def open_settings(message: types.Message):
    token = db.get(message.from_user.id)
    if not token:
        return await message.answer("Session expired. Type /start", reply_markup=types.ReplyKeyboardRemove())
    
    await message.answer(
        "⚙️ <b>Settings Menu</b>\n\nChoose an option below:", 
        reply_markup=get_settings_keyboard()
    )

@auth_router.callback_query(lambda c: c.data.startswith("settings_"))
async def handle_settings_callbacks(callback_query: types.CallbackQuery):
    action = callback_query.data.split("_", 1)[1]
    
    if action == "delete_account":
        await callback_query.message.edit_text(
            "⚠️ <b>WARNING!</b>\n\nAre you sure you want to delete your account?\n"
            "This action is <b>irreversible</b>. All your schedule data will be permanently wiped.",
            reply_markup=get_confirm_delete_keyboard()
        )
    await callback_query.answer()

@auth_router.callback_query(lambda c: c.data.startswith("confirm_delete_"))
async def handle_confirm_delete(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split("_", 2)[2]
    
    if action == "no":
        await callback_query.message.edit_text("Phew! Your account is safe. 🛡️")
        return await callback_query.answer()
    
    if action == "yes":
        telegram_id = callback_query.from_user.id
        token = db.get(telegram_id)
        
        if not token:
            await callback_query.answer("Session expired.", show_alert=True)
            return
        
        await callback_query.message.edit_text("Deleting account... ⏳")
        response = await api.delete_account(token)
        
        if response.get("status") == "success":
            db.delete(telegram_id)
            await state.clear()
            await callback_query.message.edit_text("✅ Your account and schedule data have been successfully wiped from our servers.")
            await callback_query.message.answer("Goodbye! 👋\nType /start if you want to use the bot again.", reply_markup=types.ReplyKeyboardRemove())
        else:
            await callback_query.message.edit_text(f"❌ {response.get('message')}")
            
    await callback_query.answer()