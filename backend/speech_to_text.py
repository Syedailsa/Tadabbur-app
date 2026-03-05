import os
import httpx
import logging

FIREWORKS_API_KEY = os.getenv("FIREWORKS_AI_API_KEY")
FIREWORKS_URL = "https://audio-prod.api.fireworks.ai/v1/audio/transcriptions"

logger = logging.getLogger(__name__)

class SpeechToTextEngine:
    """
    A simple client to upload audio files to Fireworks AI for transcription.
    """
    def __init__(self):
        self.api_key = FIREWORKS_API_KEY
        self.url = FIREWORKS_URL

    async def transcribe(self, file_path: str, language: str = "en") -> str:
        """
        Uploads an audio file to Fireworks and returns the transcribed text.
        """
        if not self.api_key:
            logger.error("Fireworks API Key is missing.")
            return "Error: API Key missing."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": "whisper-v3", # "whisper-v3-turbo" for speed
            "response_format": "json",
            "temperature": "0.0",
            "language": "en"
        }

        if language:
            data["language"] = language

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(file_path, "rb") as f:
                    files = {"file": f}
                    
                    logger.info(f"📤 Uploading {file_path} to Fireworks AI...")
                    
                    response = await client.post(
                        self.url, 
                        headers=headers, 
                        data=data, 
                        files=files,
                        timeout=60.0
                    )

                if response.status_code == 200:
                    result = response.json()
                    text = result.get("text", "")
                    logger.info("✅ Transcription complete.")
                    return text.strip()
                else:
                    error_msg = f"Fireworks API Error {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return ""

        except Exception as e:
            logger.exception(f"❌ Transcription failed: {e}")
            return ""