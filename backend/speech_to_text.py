# import os
# import asyncio
# import json
# import shutil
# import websockets
# from dotenv import load_dotenv


# load_dotenv()


# # fireworks-asr-v2
# FIREWORKS_WS_URL = "wss://audio-streaming-v2.api.fireworks.ai/v1/audio/transcriptions/streaming?language=en"
# FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")


# if not shutil.which("ffmpeg"):
#     raise RuntimeError("FFmpeg is not installed or not in PATH.")


# class SpeechToTextEngine:
#     def __init__(self):
#         self.ffmpeg_process = None
#         self.fw_socket = None
#         self.running = False
#         self.output_queue = asyncio.Queue()


#     async def start(self):
#         """Starts the FFmpeg process and Fireworks connection."""
#         self.running = True
#         print("🟢 Starting STT Engine...")


#         self.ffmpeg_process = await asyncio.create_subprocess_exec(
#         "ffmpeg",
#         "-protocol_whitelist", "file,pipe,stdio,webm",
#         "-f", "webm",
#         "-i", "pipe:0",
#         "-f", "s16le",
#         "-ac", "1",
#         "-ar", "16000",
#         "-acodec", "pcm_s16le",
#         "pipe:1",
#         stdin=asyncio.subprocess.PIPE,
#         stdout=asyncio.subprocess.PIPE,
#         stderr=asyncio.subprocess.DEVNULL
#         )



#         # 2. Connect to Fireworks
#         self.fw_socket = await websockets.connect(
#             FIREWORKS_WS_URL,
#             additional_headers={"Authorization": f"Bearer {FIREWORKS_API_KEY}"}
#         )
       
#         # 3. Start background tasks to move data
#         asyncio.create_task(self._ffmpeg_to_fireworks())
#         asyncio.create_task(self._fireworks_to_queue())
#         print("🟢 STT Engine Ready")


#     async def process_audio(self, audio_data: bytes):
#         """Feed audio chunks from the browser into FFmpeg."""
#         if self.running and self.ffmpeg_process:
#             try:
#                 self.ffmpeg_process.stdin.write(audio_data)
#                 await self.ffmpeg_process.stdin.drain()
#             except Exception as e:
#                 print(f"🔴 Error feeding audio: {e}")


#     async def _ffmpeg_to_fireworks(self):
#         """Internal: Reads PCM from FFmpeg and sends to Fireworks."""
#         try:
#             while self.running:
#                 chunk = await self.ffmpeg_process.stdout.read(4096)
#                 if not chunk:
#                     break
#                 await self.fw_socket.send(chunk)
#         except Exception:
#             pass


#     async def _fireworks_to_queue(self):
#         """Internal: Reads JSON from Fireworks and puts text in output queue."""
#         try:
#             async for message in self.fw_socket:
#                 data = json.loads(message)
#                 if data.get("text"):
#                     # Put the text into the queue for main.py to pick up
#                     is_final = data.get("is_final", False)
#                     await self.output_queue.put((data["text"], is_final))
#                     # await self.output_queue.put(data["text"])
#         except Exception as e:
#             print(f"🔴 Fireworks Receive Error: {e}")


#     async def get_text_stream(self):
#         """Generator that yields text as it arrives."""
#         while self.running:
#             # Yield tuple (text, is_final)
#             data = await self.output_queue.get()
#             yield data
#             # text = await self.output_queue.get()
#             # yield text


#     async def stop(self):
#         """Clean up resources."""
#         self.running = False
#         print("🟡 Stopping STT Engine...")
       
#         if self.fw_socket:
#             await self.fw_socket.close()
       
#         if self.ffmpeg_process:
#             if self.ffmpeg_process.stdin:
#                 self.ffmpeg_process.stdin.close()
#             try:
#                 self.ffmpeg_process.terminate()
#             except:
#                 pass
