from aiogram import Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from api_client import ApiClient

auth_router = Router()
api = ApiClient()

# Temporary in-memory storage for JWTs (user_id -> jwt_token)
session_db = {}

class RegistrationFSM(StatesGroup):
    waiting_for_invite = State()

@auth_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    if message.from_user.id in session_db:
        await message.answer("Welcome back! You are already authenticated. ✅")
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
    
    # Telegram users aren't required to have a username. 
    # If it's missing, we fallback to their first name so the C# API doesn't get a null string.
    username = message.from_user.username or message.from_user.first_name
    
    processing_msg = await message.answer("Verifying code securely with the server... ⏳")
    
    # Call the C# API with the newly required fields
    response = await api.login(telegram_id, username, invite_code)
    
    if response.get("status") == "success":
        jwt_token = response.get("token")
        server_message = response.get("message")
        
        # Store the token
        session_db[telegram_id] = jwt_token
        
        await processing_msg.edit_text(f"✅ {server_message}")
        await state.clear()
        
        print(f"Stored Token for {username} ({telegram_id}): {jwt_token}")
    else:
        # Pass the 403 error message back to the user
        await processing_msg.edit_text(f"❌ {response.get('message')}\n\nPlease try again:")