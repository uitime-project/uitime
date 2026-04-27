import os
import aiohttp
import logging

class ApiClient:
    def __init__(self):

        raw_url = os.getenv("API_BASE_URL", "https://uitime.onrender.com")
        self.base_url = raw_url.rstrip('/')

    async def login(self, telegram_id: int, username: str, invite_code: str) -> dict:
        endpoint = f"{self.base_url}/api/Auth/login" 
        
        payload = {
            "telegramId": telegram_id,
            "username": username,
            "inviteCode": invite_code.strip()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "token": data.get("token"),
                            "message": data.get("message", "Login successful!")
                        }
                    elif response.status == 403:
                        error_data = await response.text()
                        return {
                            "status": "error",
                            "message": error_data or "Invalid or already used invite code."
                        }
                    else:
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
        
    async def _fetch_schedule(self, endpoint_path: str, token: str) -> dict:
        endpoint = f"{self.base_url}/api/Schedule/{endpoint_path}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"status": "success", "data": data}
                    elif response.status == 401:
                        return {"status": "error", "message": "Session expired. Please log in again"}
                    else:
                        error_text = await response.text()
                        logging.error(f"Schedule fetch failed. Status: {response.status}. Response: {error_text}")
                        return {"status": "error", "message": "Failed to retrieve schedule from the server"}
                    
        except Exception as e:
            logging.error(f"API error:{e}")
            return {"status": "error", "message": "An unexpected error occurred"}
        
    async def get_today_schedule(self, token: str) -> dict:
        return await self._fetch_schedule("today", token)
    
    async def get_tomorrow_schedule(self, token: str) -> dict:

        return await self._fetch_schedule("tomorrow", token)
    
    async def upload_schedule(self, token: str, file_bytes: bytes, filename: str) -> dict:
        # Велика літера S
        endpoint = f"{self.base_url}/api/Schedule/upload"
        headers = {"Authorization": f"Bearer {token}"}

        form_data = aiohttp.FormData()
        form_data.add_field('file', file_bytes, filename=filename, content_type='application/octet-stream')

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, data=form_data) as response:
                    if response.status == 200:
                        data = await response.json()

                        return {"status": "success", "message": data.get("message", "Upload successful")}
                    elif response.status == 401:
                        return {"status": "error", "message": "Session expired. Please log in again"}
                    else:

                        error_text = await response.text()
                        logging.error(f"Upload failed: {response.status} - {error_text}")
                        return {"status": "error", "message": "Failed to upload the file to the server"}
                    
        except Exception as e:
            logging.error(f"API Upload Error: {e}")
            return {"status": "error", "message": "An unexpected error occurred during upload"}