# import os
# import json
# import re
# from dotenv import load_dotenv
# import asyncpg
# from pathlib import Path
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
# from supabase import create_client, Client
# from supabase.client import ClientOptions
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Any, List, Optional
# import asyncio 
# from langchain.messages import HumanMessage, AIMessage
# from agents import Runner
# from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
# from title_agent import title_agent
# import pprint
# from Clean_text import clean_text_with_groq
# import agent as agent_module
# import story_agent as story_module
# import logging
# import secrets
# import random
# import string
# import uuid
# from agents import ItemHelpers  
# from fastapi import UploadFile, File, Form
# from file_service import process_uploaded_file
# import shutil
# import tempfile
# from speech_to_text import SpeechToTextEngine
# from text_to_speech import TextToSpeechEngine
# from tools.audio_playback import (
#     extract_audio_data,
#     get_quran_audio,
#     get_available_reciters,
#     InvalidSurahError,
#     InvalidAyahError,
#     QuranAPIError
# )
# from tools.utils import normalize_surah
# from api import (
#     auth_router,
#     notif_router,
#     bookmark_router,
#     profile_router,
#     feedback_router,
    
# )
# from reset_password_api import password_reset_router
# from quran_api import quran_router , parah_router, story_router
# from reset_password_api import password_reset_router
# from reflection_api import reflection_router
# from database import init_db_pool, close_db_pool, create_tables
# from fastapi.security import HTTPBearer
# from fastapi.openapi.utils import get_openapi
# import sys

# if sys.platform.startswith("win"):
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# load_dotenv()

# session_file_context = {}

# pp = pprint.PrettyPrinter(indent=2)
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# TADABBUR_PROJECT_URL = os.getenv('TADABBUR_PROJECT_URL')
# TADABBUR_API_KEY = os.getenv('TADABBUR_API_KEY')

# # ------------------- APP CONFIG -------------------
# app = FastAPI(title="Tadabbur Agent API")

# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     openapi_schema = get_openapi(
#         title="Tadabbur Agent API",
#         version="1.0.0",
#         description="Backend API for Quranic Tadabbur Agent Application",
#         routes=app.routes,
#     )
#     openapi_schema["components"]["securitySchemes"] = {
#         "bearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT"
#         }
#     }
#     openapi_schema["security"] = [{"bearerAuth": []}]
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema
# app.openapi = custom_openapi

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.on_event("startup")
# async def startup_event():
#     """Initialize database pool on startup"""
#     await init_db_pool()

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Close database pool on shutdown"""
#     await close_db_pool()


# # ================= Routes =================
# app.include_router(auth_router)
# app.include_router(password_reset_router)
# app.include_router(notif_router)
# app.include_router(bookmark_router)
# app.include_router(profile_router)
# app.include_router(feedback_router)
# app.include_router(quran_router)
# app.include_router(parah_router)
# app.include_router(story_router)
# app.include_router(reflection_router)


# API_KEY = os.getenv("CHAT_API_KEY")
# # ------------------- OPTIONAL HTTP ENDPOINT -------------------
# # === SESSION CODE START ===
# DB_PATH = "chat.db"



# def generate_short_id() -> str:
#     return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# def generate_session_id() -> str:
#     """Generate unique session ID: sess_ + 12 hex chars"""
#     return f"sess_{secrets.token_hex(6)}"


# # def ensure_db_exists():
# #     """Force creation of sessions.db file"""
# #     db_file = Path(DB_PATH)
# #     if not db_file.exists():
# #         temp_id = generate_session_id()
# #         temp_session = SQLiteSession(temp_id, DB_PATH)


# # ensure_db_exists()



# def get_chat_messages(session_id: str, supabase_client) -> List[str]:
#     """Get all messages of a specific session"""
#     if not session_id or not supabase_client:
#         return []
#     chat_messages = supabase_client.table('chat_messages').select('message_id','role','message').order('created_at').eq('session_id', session_id).execute().data
#     chat_messages = [
#     {'role': msg['role'], 'content': msg['message']}
#     for msg in chat_messages
#     ]
#     return chat_messages


# def get_message_ids(session_id: str, supabase_client) -> list[str | None]:
#     """Get all message IDs for a specific session"""
#     if not session_id or not supabase_client:
#         return []

#     message_ids = supabase_client.table('chat_messages').select('message_id').order('created_at').eq('session_id', session_id).execute().data
#     print(f"All message IDs for session {session_id}, {message_ids}")
#     return message_ids

# # ------------------- OPTIONAL HTTP ENDPOINT -------------------
# class Message(BaseModel):
#     role: str
#     content: str

# class ChatRequest(BaseModel):
#     messages: List[Message]

# @app.post("/api/upload")
# async def upload_file(
#     file: UploadFile = File(...), 
#     session_id: str = Form(...)
# ):
#     try:
#         extracted_text = await process_uploaded_file(file)
#         existing_context = session_file_context.get(session_id, "")
#         updated_context = existing_context + "\n\n--- UPLOADED FILE CONTENT ---\n" + extracted_text 
#         session_file_context[session_id] = updated_context

#         supabase = create_client(TADABBUR_PROJECT_URL, TADABBUR_API_KEY)

#         supabase.table('chat_sessions').update({
#             'file_context': updated_context
#         }).eq('session_id', session_id).execute()
        
#         logger.info(f"File processed for session {session_id}. Text length: {len(extracted_text)}")
#         return {"status": "success", "message": "File processed successfully."}
#     except Exception as e:
#         logger.error(f"Upload failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/chat")
# async def chat(req: ChatRequest, authorization: str | None = Header(None)):
#     conversation = "\n".join([f"{m.role}: {m.content}" for m in req.messages])
#     try:
#         logger.info("hey")
#         result = await Runner.run(
#             agent_module.agent,
#             conversation,
#             run_config=getattr(agent_module, "config", None)
#         )


#         reply_text = getattr(result, "final_output", None) or getattr(result, "output_text", None) or str(result)
#         return {"reply": reply_text}


#     except InputGuardrailTripwireTriggered as e:
#         msg = getattr(e.guardrail_result, "output_info", "Sorry, your question seems unrelated to the Quranic context.")
#         return {"reply": msg}


#     except OutputGuardrailTripwireTriggered as e:
#         msg = getattr(e.guardrail_result, "output_info",
#                       "Sorry, I can only respond within Quranic context.")
#         return {"reply": msg}


#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
# stt_engine = SpeechToTextEngine()

# @app.post("/api/transcribe")
# async def transcribe_audio(file: UploadFile = File(...)):
#     """
#     Receives an audio file (Blob) from frontend, saves it temporarily,
#     and sends it to Fireworks for transcription.
#     """
#     try:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
#             shutil.copyfileobj(file.file, temp_audio)
#             temp_path = temp_audio.name

#         text = await stt_engine.transcribe(temp_path)

#         os.remove(temp_path)

#         return {"text": text}

#     except Exception as e:
#         logger.error(f"Transcription endpoint error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# def _normalize_name(name: Optional[str]) -> Optional[str]:
#     if not name:
#         return None
#     return "".join(c for c in name.lower() if c.isalnum())


# # Helper: try to map an agent name to the actua Agent object using configured handoffs (STREAMING)
# def _map_name_to_agent(name: Optional[str]):
#     if not name:
#         return None
#     normalized = _normalize_name(name)
#     # Check known modules (main agent has handoffs list containing mapping dicts)
#     try:
#         handoff_entries = getattr(agent_module.agent, "handoffs", None) or []
#         for entry in handoff_entries:
#             if isinstance(entry, dict):
#                 for k, v in entry.items():
#                     if _normalize_name(k) == normalized:
#                         return v
#     except Exception:
#         pass
#     # fallback modules
#     if _normalize_name(getattr(story_module, "story_agent", None).name if getattr(story_module, "story_agent", None) else None) == normalized:
#         return getattr(story_module, "story_agent", None)
#     # try Tafsir agent 
#     try:
#         taf = getattr(agent_module, "Tafsir_Agent", None) or getattr(agent_module, "Tafsir_Agent", None)
#     except Exception:
#         taf = None
#     # If tafser agent exists in module scope under tafseer_agent module
#     import tafseer_agent as taf_mod
#     try:
#         if _normalize_name(getattr(taf_mod, "Tafsir_Agent", None).name if getattr(taf_mod, "Tafsir_Agent", None) else None) == normalized:
#             return getattr(taf_mod, "Tafsir_Agent", None)
#     except Exception:
#         pass
#     return None


# @app.websocket("/ws/chat")
# async def websocket_chat(websocket: WebSocket):
#     await websocket.accept()
#     logger.info("WebSocket connected successfully")

#     supabase_client = None
#     try:
#         print("Connecting to Database for saving user messages")
#         supabase_client: Client = create_client(
#             TADABBUR_PROJECT_URL,
#             TADABBUR_API_KEY,
#             options=ClientOptions(
#                 postgrest_client_timeout=10,
#                 storage_client_timeout=10,
#                 schema="public",
#             )
#         )
#         print("✅ Supabase Client connected successfully!")
#     except Exception as e:
#         print("Some error occured while connecting to supabase", e)

#     conversation_history = []
#     unique_message_ids = set()
#     # TTS State
#     tts_engine = TextToSpeechEngine()

#     # ====== SESSION CODE START ======
#     current_session = None
#     session_id = None
#     # ========== SESSION END  ======
#     session_model_key: str = "qwen2p5-72b-instruct"
#     active_agent = agent_module.main_agent
#     current_agent_name = active_agent.name

#     try:
#         while True:
#             message = await websocket.receive()

#             if "text" in message:
#                 try:
#                     data = json.loads(message["text"])
#                 except json.JSONDecodeError:
#                     continue

#                 if data.get("type") == "tts_request":
#                     raw_text = data.get("text")
#                     message_id_ref = data.get("message_id")
                    
#                     if raw_text:
#                         logger.info(f"🧹 Cleaning text with Groq Agent...")
                        
#                         clean_text = await clean_text_with_groq(raw_text)
                        
#                         logger.info(f"🎤 Stream audio for: {clean_text[:50]}...")
                        
#                         try:
#                             async for audio_chunk in tts_engine.stream_audio(clean_text):
#                                 await websocket.send_json({
#                                     "type": "tts_audio_chunk",
#                                     "message_id": message_id_ref,
#                                     "audio": audio_chunk 
#                                 })
#                         except Exception as e:
#                             logger.error(f"TTS Error: {e}")
#                     continue

#             if data.get("type") == "audio_request":
#                 surah = data.get("surah")
#                 ayah = data.get("ayah")
#                 reciter = data.get("reciter", "alafasy")
                
#                 logger.info(f"🎵 Audio request: Surah {surah}, Ayah {ayah}, Reciter: {reciter}")
                
#                 try:
#                     audio_result = get_quran_audio(
#                         surah=surah,
#                         ayah=ayah,
#                         reciter=reciter
#                     )
#                     # ========================================================
                    
#                     if audio_result.get("success"):
#                         await websocket.send_json({
#                             "type": "audio_response",
#                             "status": "success",
#                             "data": audio_result
#                         })
#                         logger.info("✅ Audio data sent successfully")
#                     else:
#                         error_msg = audio_result.get("error", "Failed to fetch audio")
#                         await websocket.send_json({
#                             "type": "audio_response",
#                             "status": "error",
#                             "message": error_msg
#                         })
#                         logger.error(f"❌ Audio fetch failed: {error_msg}")
                
#                 except (InvalidSurahError, InvalidAyahError) as e:
#                     await websocket.send_json({
#                         "type": "audio_response",
#                         "status": "error",
#                         "message": str(e)
#                     })
#                     logger.warning(f"⚠️ Validation error: {e}")
                
#                 except QuranAPIError as e:
#                     await websocket.send_json({
#                         "type": "audio_response",
#                         "status": "error",
#                         "message": f"API error: {str(e)}"
#                     })
#                     logger.error(f"❌ API error: {e}")
                
#                 except Exception as e:
#                     logger.exception("Unexpected audio error")
#                     await websocket.send_json({
#                         "type": "audio_response",
#                         "status": "error",
#                         "message": "An unexpected error occurred"
#                     })
                
#                 continue

#             if data.get("type") == "verse_request":
#                 surah = data.get("surah")
#                 ayah = data.get("ayah")
#                 include_audio = data.get("include_audio", False)
                
#                 logger.info(f"📖 Verse request: Surah {surah}, Ayah {ayah}, Audio: {include_audio}")
                
#                 try:
#                     verse_result = get_quran_verse(
#                     surah=surah,
#                     ayah=ayah,
#                     include_audio=include_audio
#                     )

#                     if verse_result.get("success"):
#                         await websocket.send_json({
#                         "type": "verse_response",
#                         "status": "success",
#                         "data": verse_result
#                         })
#                         logger.info(f"✅ Verse data sent: {surah}:{ayah}")
#                     else:
#                         await websocket.send_json({
#                         "type": "verse_response",
#                         "status": "error",
#                         "message": verse_result.get("error", "Failed to fetch verse")
#                         })
                
#                 except (InvalidSurahError, InvalidAyahError) as e:
#                     await websocket.send_json({
#                         "type": "verse_response",
#                         "status": "error",
#                         "message": str(e)
#                     })
#                     logger.warning(f"⚠️ Validation error: {e}")
                
#                 except QuranVerseAPIError as e:
#                     await websocket.send_json({
#                         "type": "verse_response",
#                         "status": "error",
#                         "message": f"API error: {str(e)}"
#                     })
#                     logger.error(f"❌ API error: {e}")
                
#                 except Exception as e:
#                     logger.exception("Unexpected verse error")
#                     await websocket.send_json({
#                         "type": "verse_response",
#                         "status": "error",
#                         "message": "An unexpected error occurred"
#                     })
                
#                 continue

#             # ========== SESsION CODE START ==========
#             # SESSION INIT
#             if data.get("type") == "session-init":
#                 requested_session_id = data.get("session_id", "").strip()

#                 user_data = data.get("user_data", {})
#                 user_age = user_data.get("age")
#                 user_name = user_data.get("username", "Friend")

#                 # 2. If age exists, use the factory function to switch the active_agent
#                 if user_age is not None:
#                     try:
#                         print(f"Configuring agent for User Data: \n Age: {user_age}, Name: {user_name}")
#                         active_agent = agent_module.get_agent_by_user_age(
#                             age=int(user_age), 
#                             username=user_name
#                         )
#                         current_agent_name = active_agent.name
#                     except Exception as e:
#                         logger.error(f"Error configuring agent by age: {e}")
                        
#                 if not requested_session_id:
#                     # Create brand new session
#                     session_id = generate_session_id()
#                     logger.info(f"New session created: {session_id}")
#                 else:
#                     # Resume existing session
#                     session_id = requested_session_id
#                     logger.info(f"Session resumed: {session_id}")
#                     try:
#                         if supabase_client:
#                             response = supabase_client.table('chat_sessions')\
#                                 .select('file_context')\
#                                 .eq('session_id', session_id)\
#                                 .execute()
                            
#                             if response.data and response.data[0].get('file_context'):
#                                 restored_context = response.data[0]['file_context']
#                                 session_file_context[session_id] = restored_context
#                                 logger.info(f"Restored file context from DB: {len(restored_context)} chars")
#                     except Exception as e:
#                         logger.error(f"Failed to restore file context: {e}")
#                 # add a record in chat_sessions table
#                 try:    
#                     if supabase_client:
#                         print("🔃 Creating a new session record")
#                         supabase_client.table("chat_sessions").insert({'session_id': session_id, "title": "Chat Title", "description":"Description for the chat session" }).execute()
#                         # reset the conversation history and unique message ids
#                         conversation_history = []
#                         unique_message_ids.clear()
#                         print("✅ Successfully created a new session record!")
#                 except Exception as e:
#                     print("Some error occured while adding a new session record", e)

#                 # Send confirmation — this unblocks frontend
#                 await websocket.send_json({
#                     "type": "session_id",
#                     "user_age": user_age,
#                     "user_name": user_name,
#                     "status": "acknowledged",
#                     "session_id": session_id,
#                     "current_agent": current_agent_name,
#                     "current_model": session_model_key
#                 })
#                 continue  

#             # Handle CHAT HISTORY request
#             if data.get("type") == "chat_history":
#                 try:
#                     if supabase_client:
#                         chat_sessions = supabase_client.table('chat_sessions').select('session_id', 'title', 'description', 'created_at').execute().data
#                         print("All sessions", chat_sessions)
#                         await websocket.send_json({
#                             "type": "chat_history",
#                             "status":"acknowledged",
#                             "chat_history": chat_sessions
#                         })
#                         logger.info(f"Sent {len(chat_sessions)} sessions to frontend")
#                 except Exception as e:
#                     logger.error(f"Error fetching chat history: {e}")

#                     await websocket.send_json({
#                         "type": "chat_history",
#                         "status": "non-acknowledged",
#                         "chat_history": [],
#                         "error": str(e)
#                     })
#                 continue


#             # Handle Get SPECIFIC REQUEST
#             if data.get("type") == "get_chat":
#                 requested_session_id = data.get("session_id", "")
#                 if not requested_session_id:
#                     await websocket.send_json({
#                         "type": "get_chat",
#                         "status": "non-acknowledged",
#                         "error": "session_id is required"
#                     })
#                     continue
#                 try:
#                     # switch to this session
#                     session_id = requested_session_id
#                     print(f"🔃 Retrieving messages for chat with session-id {session_id}")
#                     # get chat messages
#                     chat_history = get_chat_messages(session_id, supabase_client)
#                     # get message ids for this session
#                     message_ids = get_message_ids(session_id, supabase_client)
#                     unique_message_ids = set(message_ids)
#                     # override conversation_history with new_chat_history
#                     conversation_history = chat_history or []
#                     await websocket.send_json({
#                         "type": "get_chat",
#                         "status": "acknowledged",
#                         "session_id": session_id,
#                         "chat_history": chat_history
#                     })
#                     logger.info(f"Loaded chat: {session_id} with {len(chat_history)} messages")
#                 except Exception as e:
#                     logger.error(f"Error loading chat: {e}")
#                     await websocket.send_json({
#                         "type": "get_chat",
#                         "status": "non-acknowledged",
#                         "session_id": requested_session_id,
#                         "error": str(e)
#                     })
#                 continue

#             # ============================= MODEL SELECTION HANDLER =============================
#             # if data.get("type") == "model-selection":
#             #     requested_model = data.get("model")  # e.g., "kimi-k2-instruct-0905", "deepseek-v3p1-terminus"

#             #     # Validate against supported models
#             #     if requested_model in agent_module.SUPPORTED_MODELS:
#             #         session_model_key = requested_model
#             #         model_info = agent_module.SUPPORTED_MODELS[requested_model]


#             #         await websocket.send_json({
#             #             "type": "model-selection",
#             #             "status": "acknowledged",
#             #             "model": requested_model,
#             #             "display_name": model_info["name"]
#             #         })
#             #         await websocket.send_json({
#             #             "type": "loading_message",
#             #             "content": f"Switched to **{model_info['name']}**"
#             #         })
#             #         logger.info(f"Model switched to: {requested_model} ({model_info['name']})")
#             #     else:
#             #         await websocket.send_json({
#             #             "type": "model-selection",
#             #             "status": "not-acknowledged",
#             #             "model": requested_model,
#             #             "error": "This model is not supported.",
#             #             "available": list(agent_module.SUPPORTED_MODELS.keys())
#             #         })
#             #     continue  # Skip to next message
            
#             # === AGENT SWITCH ===
#             if data.get("type") == "agent":
#                 agent_name = data.get("agent")
#                 mapped = _map_name_to_agent(agent_name)
#                 if mapped:
#                     active_agent = mapped
#                     active_config = getattr(mapped, "config", active_config)
#                     current_agent_name = getattr(mapped, "name", agent_name)
#                 elif agent_name == "story-telling":
#                     active_agent = story_module.story_agent
#                     # active_config = getattr(story_module, "config", None)
#                     # current_agent_name = "Quran Storyteller"
#                 else:
#                     active_agent = agent_module.agent
#                     # active_config = getattr(agent_module, "config", None)
#                     # current_agent_name = "Quran Tadabbur Agent"

#                 current_agent_normalized = _normalize_name(current_agent_name)
#                 await websocket.send_json({
#                     "type": "loading_message",
#                     "content": f"Switched to **{current_agent_name}** mode"
#                 })
#                 continue

#             if data.get("type") in ["like", "dislike", "report_content"]:
#                 feedback_type = data["type"]                    # "like" / "dislike" / "report_content"
#                 index = data.get("index")
#                 sess_id = data.get("session_id") or session_id  # Use provided session_id or current session_id

#                 # Validation
#                 if not sess_id:
#                     await websocket.send_json({"type": "error", "message": "session_id missing"})
#                     continue
#                 if not isinstance(index, int) or index < 0:
#                     await websocket.send_json({"type": "error", "message": "invalid index"})
#                     continue

#                 # Save to PostgreSQL (Supabase)
#                 try:
#                     conn = await asyncpg.connect(os.getenv("DATABASE_URL"),statement_cache_size=0)
#                     await conn.execute(
#                         """
#                         INSERT INTO content_feedback (session_id, item_index, feedback_type)
#                         VALUES ($1, $2, $3)
#                         ON CONFLICT (session_id, item_index, feedback_type) DO NOTHING
#                         """,
#                         sess_id, index, feedback_type
#                     )
#                     await conn.close()

#                     # Success response
#                     await websocket.send_json({
#                         "type": "feedback_ack",
#                         "status": "success",
#                         "action": feedback_type,
#                         "index": index
#                     })

#                     # Optional: 10+ reports pe alert
#                     if feedback_type == "report_content":
#                         conn = await asyncpg.connect(os.getenv("DATABASE_URL"),statement_cache_size=0)
#                         reports = await conn.fetchval(
#                             "SELECT COUNT(*) FROM content_feedback WHERE item_index = $1 AND feedback_type = 'report_content'",
#                             index
#                         )
#                         await conn.close()
#                         if reports and reports > 10:
#                             await websocket.send_json({
#                                 "type": "content_reported",
#                                 "index": index,
#                                 "reports": reports
#                             })

#                 except Exception as e:
#                     logger.error(f"Feedback save failed: {e}")
#                     await websocket.send_json({
#                         "type": "error",
#                         "message": "feedback save failed"
#                     })

#                 continue  
#             # === MAIN CHAT MESSAGE ===

#             if data.get("type") == "user_message":
#                 role = data.get("role", "user")
#                 message = data.get("content", "")
#                 message_id = data.get("message_id")
#                 if not message_id:
#                     message_id = str(uuid.uuid4())
                
#                 print("New message received", message)
#                 if message_id:
#                     unique_message_ids.add(message_id)
#                 else:
#                     message_id = str(uuid.uuid4())
#                     while message_id in unique_message_ids:
#                         message_id = str(uuid.uuid4())
#                     unique_message_ids.add(message_id)
#                 # save user message in db
#                 try:
#                     if supabase_client:
#                         supabase_client.table('chat_messages').insert({
#                             "message_id": message_id,
#                             "session_id": session_id,
#                             "role": role,
#                             "content": message,
#                         }).execute()
#                         print("✅ User message saved successfully!")
#                 except Exception as e:
#                     print("Some error occured while inserting user messages", e)

#                 logger.info(f"[{current_agent_name}] Session: {session_id} | Message: {message} ...")

#                 # File Feature
#                 file_context = session_file_context.get(session_id, "")
                
#                 message_for_history = message 

#                 if file_context:
#                     logger.info(f"📚 Found context for session {session_id}: {len(file_context)} chars")
#                     safe_context = (file_context[:8000] + '... [TRUNCATED]') if len(file_context) > 8000 else file_context
#                     injected_message = (
#                         f"SYSTEM: The user has attached a file. Use the following content to answer their question:\n"
#                         f"========================================\n"
#                         f"{safe_context}\n"
#                         f"========================================\n\n"
#                         f"USER QUESTION: {message}"
#                     )
                    
#                     message_for_history = injected_message
#                     logger.info(f"✅ Injected file context into prompt for {session_id}")

#                 try:
#                     # append user message to conversation history
#                     conversation_history.append(HumanMessage(message_for_history))
#                     response = active_agent.invoke(
#                         {"messages": conversation_history},
#                     )
#                     response = response['messages'][-1].content
#                     # append assistant message to conversation history
#                     conversation_history.append(AIMessage(response or ""))

#                     response_message_id = str(uuid.uuid4())
#                     while response_message_id in unique_message_ids:
#                         response_message_id = str(uuid.uuid4())

#                     unique_message_ids.add(response_message_id)

#                     try: 
#                         if supabase_client:
#                             supabase_client.table('chat_messages').insert({
#                                 "message_id": response_message_id,
#                                 "session_id": session_id,
#                                 "role": "assistant",
#                                 "content": response or "",
#                             }).execute()
#                             print("✅ Assistant message saved successfully!")
#                     except Exception as e:
#                         print("Some error occured while inserting assistant messages", e)

#                     # generate title and description for the current chat history if there are 2 user/assistant messages each
#                     # run the below logic in a seperate thread
#                     if (len(conversation_history) == 2):
#                         conversation_string = ""
#                         # build a conversation string from user & assistant messages
#                         for message in conversation_history:
#                             if isinstance(message, HumanMessage):
#                                 conversation_string += f"User message: {message.content} \n"
#                             else:
#                                 conversation_string += f"Assistant message: {message.content} \n"
#                         if conversation_string:
#                             try:
#                                 agent_response = title_agent.invoke(conversation_string)
#                                 title = agent_response.title or "Title"
#                                 description = agent_response.description or "Description of chat session"
#                                 # insert title and description in session table
#                                 try:
#                                     if supabase_client:
#                                         print("🔃 Inserting title and description in session record")
#                                         supabase_client.table('chat_sessions').update({"title": title, "description": description}).eq("session_id", session_id).execute()
#                                         print("✅ Successfully insert title and description")
#                                 except Exception as e:
#                                     print("Some error occured while inserting title and description in session table", e)
#                             except Exception as e:
#                                 print("Some error occured while generating title and description", e)
#                         else: 
#                             print("No conversation string so not generating title and description.")

                    
#                     # tool logic

#                     response_lower = response.lower() if response else ""

#                     has_audio_indicators = any(indicator in response_lower for indicator in ["🎧", "http", "play", "listen", "audio", "recite"])
#                     has_verse_indicators = (
#                         any(indicator in response_lower for indicator in ["surah", "ayah", "verse", "chapter"]) 
#                         and bool(re.search(r'[\u0600-\u06FF]', response or ""))
#                     )

#                     audio_data = None
#                     verse_data = None

#                     if has_audio_indicators:
#                         logging.info("[SMART-CHECK] 🎵 Audio indicators detected - calling extract_audio_data()")
#                         audio_data = extract_audio_data(response)
#                         logging.info(f"[DEBUG] Audio extracted: {audio_data is not None}")
#                     else:
#                         logging.info("[SMART-CHECK] ⏭️ No audio indicators - skipping extraction")

#                     if has_verse_indicators and not audio_data: 
#                         logging.info("[SMART-CHECK] 📖 Verse indicators detected - calling extract_verse_data()")
#                         verse_data = extract_verse_data(response)
#                         logging.info(f"[DEBUG] Verse extracted: {verse_data is not None}")
#                     else:
#                         if not has_verse_indicators:
#                             logging.info("[SMART-CHECK] ⏭️ No verse indicators - skipping extraction")

#                     logging.info(f"[DEBUG] Audio detected: {audio_data is not None}")
#                     logging.info(f"[DEBUG] Verse detected: {verse_data is not None}")

#                     if audio_data:
#                         await websocket.send_json({
#                             "type": "open_audio_dialog",  
#                             "parsed_request": {
#                                 "surah": audio_data["surah_number"],
#                                 "ayah": audio_data["ayah_number"]
#                             },
#                             "original_message": f"Play Surah {audio_data['surah_name']}",
#                             "available_reciters": get_available_reciters(), 
#                             "note": "Audio auto-detected"
#                         })
#                         logging.info("[WS]opening dialog cleanly")
                      
#                     elif verse_data and isinstance(verse_data, dict) and verse_data.get("surah_number"):
#                         logging.info("[WS] Vers - opening Quran Verse ")
#                         await websocket.send_json({
#                             "type": "open_verse_dialog",
#                             "parsed_request": {
#                                 "surah": verse_data["surah_number"],
#                                 "ayah": verse_data["ayah_number"]
#                             },
#                             "original_message": "Quran Verse",
#                             "note": None  
#                         })                       
                   
#                     else:
#                         await websocket.send_json({
#                             "type": "assistance_response",
#                             "message_id": response_message_id,
#                             "content": response,
#                             "final": True
#                         })


#                     # === FINAL RESPONSE & CLEANUP ===
#                     # await websocket.send_json({
#                     #     "type": "assistance_response",
#                     #     "content": final_text.strip() if final_text.strip() else "I'm not sure how to respond to that."
#                     # })


#                     await websocket.send_json({"type": "streaming_end"})
#                     await websocket.send_json({"type": "run_complete"})


#                 except OutputGuardrailTripwireTriggered as e:
#                     msg = getattr(e.guardrail_result, "output_info",
#                                 "Sorry, I can only respond within the context of the Quran and authentic Islamic sources.")


#                     await websocket.send_json({
#                         "type": "assistance_response",
#                         "content": msg.strip()
#                     })
#                     await websocket.send_json({"type": "streaming_end"})
#                     await websocket.send_json({"type": "run_complete"})


#                 except WebSocketDisconnect:
#                     logger.info("Client disconnected")
#                     break


#                 except Exception as e:
#                     logger.exception("Streaming error")
#                     await websocket.send_json({"type": "assistance_response", "content": "Sorry, something went wrong."})
#                     await websocket.send_json({"type": "streaming_end"})
#                     await websocket.send_json({"type": "run_complete"})


#     except WebSocketDisconnect:
#         logger.info("WebSocket closed")

#     except Exception as e:
#         logger.exception("WebSocket error")


# # ------------------- APP RUNNER -------------------


# if __name__ == "__main__":
#     import uvicorn
#     # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
#     uvicorn.run("main:app", host="0.0.0.0", port=8000)