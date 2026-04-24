import aiohttp
import logging

class ApiClient:
    def __init__(self, base_url: str = "http://localhost:5068"):
        self.base_url = base_url

    async def login(self, telegram_id: int, username: str, invite_code: str) -> dict:
        
        endpoint = f"{self.base_url}/api/auth/login" 
        
        # Matches LoginRequestDto in C# (ASP.NET Core automatically expects camelCase by default)
        payload = {
            "telegramId": telegram_id,
            "username": username,
            "inviteCode": invite_code.strip()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload) as response:
                    
                    if response.status == 200:
                        # Success! Maps to AuthResponseDto
                        data = await response.json()
                        return {
                            "status": "success",
                            "token": data.get("token"),
                            "message": data.get("message", "Login successful!")
                        }
                    elif response.status == 403:
                        # Matches Forbid() return in AuthController
                        error_data = await response.text()
                        return {
                            "status": "error",
                            "message": error_data or "Invalid or already used invite code."
                        }
                    else:
                        # Fallback for 500s or other errors
                        error_data = await response.text()
                        logging.warning(f"Auth failed. Status: {response.status}. Response: {error_data}")
                        return {
                            "status": "error",
                            "message": "An unexpected error occurred during login. Please try again later."
                        }
                        
        except aiohttp.ClientConnectorError:
            logging.error("Failed to connect to the C# backend. Is it running?")
            return {
                "status": "error", 
                "message": "The server is currently unreachable. Please ensure the backend is running."
            }
        except Exception as e:
            logging.error(f"Unexpected API error: {e}")
            return {
                "status": "error", 
                "message": "An unexpected error occurred."
            }
        
    async def get_pending_reminders(self) -> list:
        """Pings the C# backend to get a list of reminders that need to be sent."""
        endpoint = f"{self.base_url}/api/reminders/pending"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logging.error(f"Failed to fetch reminders. Status: {response.status}")
                        return []
        except Exception as e:
            logging.error(f"Scheduler API error: {e}")
            return []