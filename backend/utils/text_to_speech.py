import os
import json
import websockets
from dotenv import load_dotenv

load_dotenv()

MURF_API_KEY = os.getenv("MURF_AI_API_KEY")
WS_URL = "wss://global.api.murf.ai/v1/speech/stream-input"

class TextToSpeechEngine:
    def __init__(self):
        self.api_key = MURF_API_KEY
        self.format = "MP3" 
        self.sample_rate = 44100
        self.model = "FALCON" 

    async def stream_audio(self, text: str):
        """
        Connects to Murf, sends text, and yields audio chunks (base64 encoded strings).
        """
        if not self.api_key:
            print("❌ Error: MURF_API_KEY not found in environment variables.")
            return

        # Construct URI with parameters
        uri = f"{WS_URL}?api-key={self.api_key}&model={self.model}&sample_rate={self.sample_rate}&format={self.format}"

        try:
            async with websockets.connect(uri) as ws:
                voice_config_msg = {
                    "voice_config": {
                        "voice_id":"Finley",
                        "style":"Promo",
                        "model:":"Falcon",
                        "rate": 0,
                        "pitch": 0,
                        "variation": 1
                    }
                }
                {}
                await ws.send(json.dumps(voice_config_msg))

                # 2. Send Text Payload
                text_msg = {
                    "text": text,
                    "end": True 
                }
                await ws.send(json.dumps(text_msg))
                print("Text payload sent to MURF for transcription!")
                # 3. Receive Audio Loop
                while True:
                    response = await ws.recv()
                    data = json.loads(response)
                    
                    if "audio" in data:
                        yield data["audio"]
                    
                    if data.get("final"):
                        break
        except Exception as e:
            print(f"❌ Murf TTS Error: {e}")