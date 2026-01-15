import os
import json
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio # --- ADDED: Required for background tasks
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from agents import Runner
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from tadabbur_agents.report_rule_generator import report_rule_generator
from collections import defaultdict
import agent as agent_module
from utils.submit_feedback import submit_feedback
from utils.generate_title_description import generate_title_description
from utils.save_system_message import save_system_message_to_db
from Clean_text import clean_text_with_groq
from utils.generate_uuid import generate_uuid
from utils.report_rule import insert_report_rule, delete_report_rule
import story_agent as story_module
import logging
import secrets
import random
import string
import uuid
from agents import ItemHelpers  
from fastapi import UploadFile, File, Form
from file_service import process_uploaded_file
import shutil
import tempfile
from speech_to_text import SpeechToTextEngine
from text_to_speech import TextToSpeechEngine
from murf import Murf
from database import init_db_pool, close_db_pool
from file_service import process_uploaded_file
from tools.audio_playback import (
    extract_audio_data,
    get_quran_audio,
    get_available_reciters,
    InvalidSurahError,
    InvalidAyahError,
    QuranAPIError
)
from tools.verse_reader import extract_verse_data
from tools.verse_reader import (
    get_quran_verse,
    InvalidSurahError,
    InvalidAyahError,
    QuranVerseAPIError
)

from quran_api import quran_router , parah_router, story_router
from reset_password_api import password_reset_router
from reflection_api import reflection_router
from api import (
    auth_router,
    notif_router,
    bookmark_router,
    profile_router,
    feedback_router,
    
)
from reset_password_api import password_reset_router
from quran_api import quran_router , parah_router, story_router
from reset_password_api import password_reset_router
from reflection_api import reflection_router
from database import init_db_pool, close_db_pool, create_tables
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
import secrets
# --- IMPORT NEW STT CLASS ---
from speech_to_text import SpeechToTextEngine
from text_to_speech import TextToSpeechEngine
from config.db import get_supabase_client
from agents import ItemHelpers  # used to extract message text from items (STREAMING)
from data.data import comprehensive_surah_metadata
from tools.verse_reader import SURAH_METADATA
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()
from data.data import comprehensive_surah_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------- APP CONFIG -------------------
app = FastAPI(title="Tadabbur Agent API")

app.include_router(auth_router)
app.include_router(password_reset_router)
app.include_router(notif_router)
app.include_router(bookmark_router)
app.include_router(profile_router)
app.include_router(feedback_router)
app.include_router(quran_router)
app.include_router(parah_router)
app.include_router(story_router)
app.include_router(reflection_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database pool on startup"""
    await init_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool on shutdown"""
    await close_db_pool()

session_file_context = {}
API_KEY = os.getenv("CHAT_API_KEY")
# ------------------- OPTIONAL HTTP ENDPOINT -------------------
# === SESSION CODE START ===
DB_PATH = "chat.db"
supabase_client = None
TADABBUR_PROJECT_URL = os.getenv("TADABBUR_PROJECT_URL") 
TADABBUR_API_KEY = os.getenv("TADABBUR_API_KEY")
def generate_session_id() -> str:
    """Generate unique session ID: sess_ + 12 hex chars"""
    return f"sess_{secrets.token_hex(6)}"


def get_chat_messages(session_id: str, supabase_client) -> List[str]:
    """Get all messages of a specific session"""
    if not session_id or not supabase_client:
        print("Session id or supabase client none, so returning...")
        return []
        
    chat_messages = supabase_client.table('chat_messages').select('message_id', 'role', 'content', 'reply_to_message_id', 'feedback').in_("role", ["user", "assistant"]).eq('session_id', session_id).order('created_at').execute().data

    
    # print("chat messages", chat_messages)
    
    return chat_messages


def get_message_ids(supabase_client) -> list[str | None]:
    """Get all message IDs"""
    if not supabase_client:
        return []
    for i in range(8):
        try:
            print("Fetching all message_ids from chat_messages table")

            message_ids = supabase_client.table('chat_messages').select('message_id').order('created_at').execute().data
            print("✅ Successfully fetched all message IDs")
            return message_ids

        except Exception as e:
            print("Some error occurred while fetching all message IDs:", e)
            print(f"Trying again, total tries {i+1}/8")
            last_error = e
    raise RuntimeError(
    f"Failed to fetch all message IDs"
    ) from last_error
    
def group_by_category(system_rules):
    grouped_by_category = defaultdict(list)

    for item in system_rules:
        grouped_by_category[item['category']].append({
            "text": item['rule'],
            "hard_rule": item['hard_rule']
        })

    result = []
    for category, rules in grouped_by_category.items():
        result.append({
            "category": category,
            "rules": rules
        })

    return result



def extract_audio_data(response_text: str) -> Optional[dict]:
    """
    Check if response contains audio URLs and extract them
    Returns: dict with audio info or None
    """
    logging.info("[EXTRACT_AUDIO] Checking response for audio data")
    if not response_text:
        logging.info("[EXTRACT_AUDIO] Response text is empty")
        return None

    # Check for audio URL pattern
    if "🎧" in response_text:
        logging.info("[EXTRACT_AUDIO] Found audio indicators in response")
        # Extract first audio URL
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, response_text)
        logging.info(f"[EXTRACT_AUDIO] Found URLs: {urls}")

        if urls:
            # Extract surah and ayah info
            surah_match = re.search(r'Surah ([^\,\n]+)', response_text)
            ayah_match = re.search(r'Ayah (\d+)', response_text)
            logging.info(f"[EXTRACT_AUDIO] Surah match: {surah_match.group(1) if surah_match else None}, Ayah match: {ayah_match.group(1) if ayah_match else None}")

            audio_data = {
                "has_audio": True,
                "audio_url": urls[0],  # First URL
                "all_urls": urls,      # All URLs if multiple ayahs
                "surah_name": surah_match.group(1).strip() if surah_match else "Unknown",
                "ayah_number": ayah_match.group(1) if ayah_match else None,
                "full_response": response_text
            }
            logging.info(f"[EXTRACT_AUDIO] Extracted audio data: {audio_data}")
            return audio_data

    logging.info("[EXTRACT_AUDIO] No audio data found")
    return None




def extract_verse_data(response_text: str) -> Optional[dict]:
    """
    Check if response contains verse data and extract it
    Returns: dict with verse info or None
    """
    if not response_text:
        return None
    
    # Check for verse/ayah indicators
    verse_indicators = ["📖", "🕌", "arabic text:", "surah", "ayah", "verse"]
    has_indicator = any(indicator in response_text.lower() for indicator in verse_indicators)
    
    if has_indicator:
        import re
        
        # Check for Arabic text (Unicode range for Arabic)
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', response_text))
        
        # Extract surah and ayah info
        surah_match = re.search(r'##\s*📖\s*([^\(]+)\s*\(([^\)]+)\)\s*-\s*Ayah\s*(\d+)', response_text)
        
        if surah_match and has_arabic:
            surah_name = surah_match.group(1).strip()
            surah_number = next((k for k, v in comprehensive_surah_metadata.items() if v["name_en"] == surah_name), None)
            return {
                "has_verse": True,
                "surah_name": surah_name,
                "surah_number": surah_number,
                "surah_name_ar": surah_match.group(2).strip(),
                "ayah_number": surah_match.group(3),
                "full_response": response_text,
                "contains_arabic": has_arabic
            }
        
        # Fallback: simple detection
        elif has_arabic:
            surah_simple = re.search(r'(?:Surah|surah)\s+([^\n,]+)', response_text)
            ayah_simple = re.search(r'(?:Ayah|ayah|Verse|verse)\s+(\d+)', response_text)
            surah_name = surah_simple.group(1).strip() if surah_simple else "Unknown"
            surah_number = next((k for k, v in SURAH_METADATA.items() if v["name_en"] == surah_name), None) if surah_name != "Unknown" else None

            return {
                "has_verse": True,
                "surah_name": surah_name,
                "surah_number": surah_number,
                "surah_name_ar": "",
                "ayah_number": ayah_simple.group(1) if ayah_simple else None,
                "full_response": response_text,
                "contains_arabic": True
            }
    
    return None
# ------------------- OPTIONAL HTTP ENDPOINT -------------------
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]


def clean_text(text: str) -> str:
    return text.replace("\x00", "")


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...), 
    session_id: str = Form(...)
):
    try:
        extracted_text = await process_uploaded_file(file)
        existing_context = session_file_context.get(session_id, "")
        updated_context = existing_context + "\n\n--- UPLOADED FILE CONTENT ---\n" + extracted_text 
        clean_context = clean_text(updated_context)
        print("Content to be inserted text", clean_context)
        print("1 done")
        session_file_context[session_id] = updated_context
        print("2 done")
        print("3 done")
        supabase_client = get_supabase_client()
        supabase_client.table('chat_sessions').update({
            'file_context': clean_context
        }).eq('session_id', session_id).execute()
        print("Context inserted successfully!")
        
        logger.info(f"File processed for session {session_id}. Text length: {len(extracted_text)}")
        return {"status": "success", "message": "File processed successfully."}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(None)):
    conversation = "\n".join([f"{m.role}: {m.content}" for m in req.messages])
    try:
        logger.info("hey")
        result = await Runner.run(
            agent_module.agent,
            conversation,
            run_config=getattr(agent_module, "config", None)
        )


        reply_text = getattr(result, "final_output", None) or getattr(result, "output_text", None) or str(result)
        return {"reply": reply_text}


    except InputGuardrailTripwireTriggered as e:
        msg = getattr(e.guardrail_result, "output_info", "Sorry, your question seems unrelated to the Quranic context.")
        return {"reply": msg}


    except OutputGuardrailTripwireTriggered as e:
        msg = getattr(e.guardrail_result, "output_info",
                      "Sorry, I can only respond within Quranic context.")
        return {"reply": msg}


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
stt_engine = SpeechToTextEngine()

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Receives an audio file (Blob) from frontend, saves it temporarily,
    and sends it to Fireworks for transcription.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            shutil.copyfileobj(file.file, temp_audio)
            temp_path = temp_audio.name

        text = await stt_engine.transcribe(temp_path)

        os.remove(temp_path)

        return {"text": text}

    except Exception as e:
        logger.error(f"Transcription endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility: normalize agent names to avoid minor mismatches (STREAMING)
def _normalize_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return "".join(c for c in name.lower() if c.isalnum())


# Helper: try to map an agent name to the actual Agent object using configured handoffs (STREAMING)
def _map_name_to_agent(name: Optional[str]):
    if not name:
        return None
    normalized = _normalize_name(name)
    # Check known modules (main agent has handoffs list containing mapping dicts)
    try:
        handoff_entries = getattr(agent_module.agent, "handoffs", None) or []
        for entry in handoff_entries:
            if isinstance(entry, dict):
                for k, v in entry.items():
                    if _normalize_name(k) == normalized:
                        return v
    except Exception:
        pass
    # fallback modules
    if _normalize_name(getattr(story_module, "story_agent", None).name if getattr(story_module, "story_agent", None) else None) == normalized:
        return getattr(story_module, "story_agent", None)
    # try Tafsir agent
    try:
        taf = getattr(agent_module, "Tafsir_Agent", None) or getattr(agent_module, "Tafsir_Agent", None)
    except Exception:
        taf = None
    # If tafser agent exists in module scope under tafseer_agent module
    import tafseer_agent as taf_mod
    try:
        if _normalize_name(getattr(taf_mod, "Tafsir_Agent", None).name if getattr(taf_mod, "Tafsir_Agent", None) else None) == normalized:
            return getattr(taf_mod, "Tafsir_Agent", None)
    except Exception:
        pass
    return None


async def stream_tts_audio(tts_engine, clean_text, websocket, message_id_ref):
    async for audio_chunk in tts_engine.stream_audio(clean_text):
        await websocket.send_json({
            "type": "tts_audio_chunk",
            "message_id": message_id_ref,
            "audio": audio_chunk
        })

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected successfully")

    try:

        supabase_client = get_supabase_client()
    except Exception as e:
        print("Some error occured initiating supabase connection", e)

    # initialize the conversation history and message_IDs set
    conversation_history = []
    unique_message_ids = []
    tts_engine = TextToSpeechEngine()

    
    # ====== SESSION CODE START ======
    current_session = None
    session_id = None
    # ========== SESSION END  ======
    session_model_key: str = "gpt-oss-20b"
    active_agent = agent_module.main_agent
    current_agent_name = active_agent.name

    try:
        while True:
            message = await websocket.receive()
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue


                if data.get("type") == "tts_request":
                    print("Got tts request, data", data)
                    raw_text = data.get("text")
                    message_id_ref = data.get("message_id")
                    
                    if raw_text:
                        logger.info(f"≡ƒº╣ Cleaning text with Groq Agent...")
                        
                        clean_text = await clean_text_with_groq(raw_text)
                        
                        logger.info(f"≡ƒÄñ Stream audio for: {clean_text[:50]}...")
                        client = Murf(
                            api_key=os.getenv("MURF_AI_API_KEY") # Not required if you have set the MURF_API_KEY environment variable
                        )
                        try:
                            res = client.text_to_speech.generate(
                                text=clean_text,
                                voice_id ="Finley",
                                style ="Promo",
                                rate = 0,
                                pitch = 0,
                                variation = 1
                            )
                            # await websocket.send_json({
                            # "type": "tts_audio_chunk",
                            # "message_id": message_id_ref,
                            # "audio": audio_chunk
                            # })
                            if res.audio_file:
                                print("Audio url", res.audio_file)
                                await websocket.send_json({
                                    "type": "tts_audio_chunk",
                                    "message_id": message_id_ref,
                                    "audio_url": res.audio_file
                                })
                                
                        except Exception as e:
                            print("Some error occured while generating audio for text", e)
                            continue

                        # try:
                        #     # fire-and-forget
                        #     asyncio.create_task(
                        #         stream_tts_audio(tts_engine, clean_text, websocket, message_id_ref)
                        #     )
                        # except Exception as e:
                        #     print("TTS Error", e)
                        #     logger.error(f"TTS Error: {e}")
                        #     continue
                    continue


            if data.get("type") == "audio_request":
                surah = data.get("surah")
                ayah = data.get("ayah")
                reciter = data.get("reciter", "alafasy")
                
                logger.info(f"≡ƒÄ╡ Audio request: Surah {surah}, Ayah {ayah}, Reciter: {reciter}")
                
                try:
                    audio_result = get_quran_audio(
                        surah=surah,
                        ayah=ayah,
                        reciter=reciter
                    )
                    # ========================================================
                    
                    if audio_result.get("success"):
                        await websocket.send_json({
                            "type": "audio_response",
                            "status": "success",
                            "data": audio_result
                        })
                        logger.info("Γ£à Audio data sent successfully")
                    else:
                        error_msg = audio_result.get("error", "Failed to fetch audio")
                        await websocket.send_json({
                            "type": "audio_response",
                            "status": "error",
                            "message": error_msg
                        })
                        logger.error(f"Γ¥î Audio fetch failed: {error_msg}")
                
                except (InvalidSurahError, InvalidAyahError) as e:
                    await websocket.send_json({
                        "type": "audio_response",
                        "status": "error",
                        "message": str(e)
                    })
                    logger.warning(f"ΓÜá∩╕Å Validation error: {e}")
                
                except QuranAPIError as e:
                    await websocket.send_json({
                        "type": "audio_response",
                        "status": "error",
                        "message": f"API error: {str(e)}"
                    })
                    logger.error(f"Γ¥î API error: {e}")
                
                except Exception as e:
                    logger.exception("Unexpected audio error")
                    await websocket.send_json({
                        "type": "audio_response",
                        "status": "error",
                        "message": "An unexpected error occurred"
                    })
                
                continue


            if data.get("type") == "verse_request":
                surah = data.get("surah")
                ayah = data.get("ayah")
                include_audio = data.get("include_audio", False)
                
                logger.info(f"≡ƒôû Verse request: Surah {surah}, Ayah {ayah}, Audio: {include_audio}")
                
                try:
                    verse_result = get_quran_verse(
                    surah=surah,
                    ayah=ayah,
                    include_audio=include_audio
                    )

                    if verse_result.get("success"):
                        await websocket.send_json({
                        "type": "verse_response",
                        "status": "success",
                        "data": verse_result
                        })
                        logger.info(f"Γ£à Verse data sent: {surah}:{ayah}")
                    else:
                        await websocket.send_json({
                        "type": "verse_response",
                        "status": "error",
                        "message": verse_result.get("error", "Failed to fetch verse")
                        })
                
                except (InvalidSurahError, InvalidAyahError) as e:
                    await websocket.send_json({
                        "type": "verse_response",
                        "status": "error",
                        "message": str(e)
                    })
                    logger.warning(f"ΓÜá∩╕Å Validation error: {e}")
                
                except QuranVerseAPIError as e:
                    await websocket.send_json({
                        "type": "verse_response",
                        "status": "error",
                        "message": f"API error: {str(e)}"
                    })
                    logger.error(f"Γ¥î API error: {e}")
                
                except Exception as e:
                    logger.exception("Unexpected verse error")
                    await websocket.send_json({
                        "type": "verse_response",
                        "status": "error",
                        "message": "An unexpected error occurred"
                    })
                
                continue

            # ========== SESsION CODE START ==========
            # SESSION INIT
            if data.get("type") == "session-init":
                requested_session_id = data.get("session_id", "").strip()
                if not requested_session_id:
                    # Create brand new session
                    session_id = generate_session_id()
                    logger.info(f"New session created: {session_id}")
                else:
                    # Resume existing session
                    session_id = requested_session_id
                    logger.info(f"Session resumed: {session_id}")
                    try:
                        if supabase_client:
                            response = supabase_client.table('chat_sessions')\
                                .select('file_context')\
                                .eq('session_id', session_id)\
                                .execute()
                            
                            if response.data and response.data[0].get('file_context'):
                                restored_context = response.data[0]['file_context']
                                session_file_context[session_id] = restored_context
                                logger.info(f"Restored file context from DB: {len(restored_context)} chars")
                    except Exception as e:
                        logger.error(f"Failed to restore file context: {e}")
                # add a record in chat_sessions table
                try:    
                    print("🔃 Creating a new session record")
                    supabase_client.table("chat_sessions").insert({'session_id': session_id, "title": "Chat Title", "description":"Description for the chat session" }).execute()

                    message_ids = get_message_ids(supabase_client)
                    # convert message IDs to a list
                    unique_message_ids = list({record['message_id'] for record in message_ids})
                    # reset the conversation history and unique message ids
                    conversation_history = []
                    print("✅ Successfully created a new session record!")            
                    # Send confirmation — this unblocks frontend
                    await websocket.send_json({
                        "type": "session_id",
                        "status": "acknowledged",
                        "session_id": session_id,
                        "current_agent": current_agent_name,
                        "current_model": session_model_key,
                        "message_ids": unique_message_ids
                    })
                except Exception as e:
                    print("Some error occured while adding a new session record", e)
                    await websocket.send_json({
                        "type": "session_id",
                        "status": "not-acknowledged",
                        "error": e
                    })
                    raise

                continue  

            # Handle CHAT HISTORY request
            if data.get("type") == "chat_history":
                try:
                    # first get all unique session IDs from chat_messages
                    all_session_ids = supabase_client.table("chat_messages").select("session_id").execute().data
                    # unique session_ids as a list
                    unique_session_ids = list({
                        record["session_id"]
                        for record in all_session_ids
                    })

                    chat_sessions = supabase_client.table('chat_sessions').select('session_id', 'title', 'description', 'created_at').in_('session_id', unique_session_ids).execute().data

                    print("All sessions", chat_sessions)
                    await websocket.send_json({
                        "type": "chat_history",
                        "status":"acknowledged",
                        "chat_history": chat_sessions
                    })
                    logger.info(f"Sent {len(chat_sessions)} sessions to frontend")
                except Exception as e:
                    logger.error(f"Error fetching chat history: {e}")

            #         await websocket.send_json({
            #             "type": "chat_history",
            #             "status": "non-acknowledged",
            #             "chat_history": [],
            #             "error": str(e)
            #         })
            #     continue


            # Handle Get SPECIFIC REQUEST
            if data.get("type") == "get_chat":
                requested_session_id = data.get("session_id", "")
                if not requested_session_id:
                    await websocket.send_json({
                        "type": "get_chat",
                        "status": "non-acknowledged",
                        "error": "session_id is required"
                    })
                    continue
                try:
                    # switch to this session
                    session_id = requested_session_id
                    print(f"🔃 Retrieving messages for chat with session-id {session_id}")
                    # get chat messages
                    chat_history = get_chat_messages(session_id, supabase_client)
                    # get all message ids
                    message_ids = get_message_ids(supabase_client)
                    # convert message IDs to a list
                    unique_message_ids = list({record['message_id'] for record in message_ids})

                    # override conversation_history with new_chat_history
                    conversation_history = chat_history or []
                    await websocket.send_json({
                        "type": "get_chat",
                        "status": "acknowledged",
                        "session_id": session_id,
                        "chat_history": chat_history,
                        "unique_message_ids": unique_message_ids 
                    })
                    logger.info(f"Loaded chat: {session_id} with {len(chat_history)} messages")
                except Exception as e:
                    logger.error(f"Error loading chat: {e}")
                    await websocket.send_json({
                        "type": "get_chat",
                        "status": "not-acknowledged",
                        "error": str(e)
                    })
                continue

            # ============================= MODEL SELECTION HANDLER =============================
            # if data.get("type") == "model-selection":
            #     requested_model = data.get("model")  # e.g., "kimi-k2-instruct-0905", "deepseek-v3p1-terminus"

            #     # Validate against supported models
            #     if requested_model in agent_module.SUPPORTED_MODELS:
            #         session_model_key = requested_model
            #         model_info = agent_module.SUPPORTED_MODELS[requested_model]


            #         await websocket.send_json({
            #             "type": "model-selection",
            #             "status": "acknowledged",
            #             "model": requested_model,
            #             "display_name": model_info["name"]
            #         })
            #         await websocket.send_json({
            #             "type": "loading_message",
            #             "content": f"Switched to **{model_info['name']}**"
            #         })
            #         logger.info(f"Model switched to: {requested_model} ({model_info['name']})")
            #     else:
            #         await websocket.send_json({
            #             "type": "model-selection",
            #             "status": "not-acknowledged",
            #             "model": requested_model,
            #             "error": "This model is not supported.",
            #             "available": list(agent_module.SUPPORTED_MODELS.keys())
            #         })
            #     continue  # Skip to next message
            
            # === AGENT SWITCH ===
            if data.get("type") == "agent":
                agent_name = data.get("agent")
                mapped = _map_name_to_agent(agent_name)
                if mapped:
                    active_agent = mapped
                    active_config = getattr(mapped, "config", active_config)
                    current_agent_name = getattr(mapped, "name", agent_name)
                elif agent_name == "story-telling":
                    active_agent = story_module.story_agent
                    # active_config = getattr(story_module, "config", None)
                    # current_agent_name = "Quran Storyteller"
                else:
                    active_agent = agent_module.agent
                    # active_config = getattr(agent_module, "config", None)
                    # current_agent_name = "Quran Tadabbur Agent"

                current_agent_normalized = _normalize_name(current_agent_name)
                await websocket.send_json({
                    "type": "loading_message",
                    "content": f"Switched to **{current_agent_name}** mode"
                })
                continue

            if data.get("type") == "undo-report":
                message_id = data.get("message_id")
                if not message_id:
                    print("No message ID found for reported message, can't proceed to undo")
                    continue
                try:
                    # delete hard rule in a different thread for optimization
                    await asyncio.to_thread(delete_report_rule, supabase_client, message_id)
                    await websocket.send_json({
                        "type": "undo-report",
                        "message_id": message_id,
                        "status": "acknowledged"
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "undo-report",
                        "status": "not-acknowledged"
                    })
                    continue
                continue


            if data.get("type") == "report":
                print("A response is reported")
                ack_sent = False
                try:
                    message_id = data.get("message_id", "")
                    feedback = data.get("feedback", "")
                    
                    if not message_id or not feedback:
                        print("No variant/message ID/feedback, can't proceed to report content")
                        await websocket.send_json({
                        "type": "report",
                        "status": "not-acknowledged"
                    })
                        ack_sent = True
                        continue
                    
                    reported_assistant_message = next(
                    (msg for msg in conversation_history if msg["id"] == message_id),
                    None
                    )
                    if reported_assistant_message:
                        try:
                            # insert hard rule in a different thread for optimization
                            print("Reported assistant message",reported_assistant_message['content'] )
                            response = await asyncio.to_thread(insert_report_rule, rule, supabase_client, message_id, feedback)

                            print("Report response", response)
                            if not response:
                                await websocket.send_json({
                                    "type": "report",
                                    "status": "not-acknowledged"
                                })
                            else:
                                await websocket.send_json(response)
                            ack_sent = True
                            
                        except Exception as e:
                            await websocket.send_json({
                            "type": "report",
                            "status": "not-acknowledged"
                            })
                            ack_sent = True
                        continue
                            
                    else:
                        print(f"No assistant message found for message_id {message_id}, can't report message. Proceeding...")
                        continue
                                
                except Exception as e:
                    print(f"An error occured while the assistant's response {message_id}")    
                    if not ack_sent:
                        await websocket.send_json({
                        "type": "report",
                        "status": "not-acknowledged"
                    })
                continue

            if data.get("type") in ["like", "dislike"]:
                type = data.get("type")
                session_id = data.get('session_id')
                message_id = data.get('message_id')
                message = data.get("message")
                if not session_id or not message_id or not message:
                    print("No message or session ID, can't proceed to feedback submission")
                    continue
                try:
                    print("Submitting user feedback")
                    # create a new task with a thread to optimize operations
                    await asyncio.to_thread(submit_feedback, type, message, message_id)
                    
                    supabase_client.table("chat_messages").update({"feedback": type}).eq("message_id", message_id).execute()

                    print("✅ Successfully submitted user feedback!")
                except Exception as e:
                    print("Failed to submit user feedback",e)
                    continue

                continue
            # === MAIN CHAT MESSAGE ===

            if data.get("type") == "user_message":
                role = data.get("role", "user")
                message = data.get("content", "")
                user_message_id = data.get("message_id")
                additional_instructions = data.get("system_instructions")
                resend_flag = data.get("resend_flag")
                resend_message_id = data.get("resend_message_id")

                # check resend_message_id if resend flag is True
                if resend_flag:
                    if not resend_message_id:
                        print("Can't proceed forward with the received message because of no message ID")
                        continue
                print("New message received", message)
                if not resend_flag:
                    if user_message_id:
                        unique_message_ids.append(user_message_id)
                    else:
                        user_message_id = generate_uuid()
                        while user_message_id in unique_message_ids:
                            user_message_id = generate_uuid()
                        unique_message_ids.append(user_message_id)
                # save user message in db
                message_string = message + f"\n\n {additional_instructions}" if additional_instructions else message
                if not resend_flag:
                    try:
                        supabase_client.table('chat_messages').insert({
                            "message_id": user_message_id,
                            "session_id": session_id,
                            "role": role,
                            "content": message_string,
                        }).execute()
                        print("✅ User message saved successfully!")
                    except Exception as e:
                        print("Some error occured while inserting user messages", e)
                        raise

                logger.info(f"[{current_agent_name}] Session: {session_id} | Message: {message_string} ...")
                # File Feature
                file_context = session_file_context.get(session_id, "")
                
                message_for_history = message 

                if file_context:
                    logger.info(f"📚 Found context for session {session_id}: {len(file_context)} chars")
                    safe_context = (file_context[:8000] + '... [TRUNCATED]') if len(file_context) > 8000 else file_context
                    injected_message = (
                        f"SYSTEM: The user has attached a file. Use the following content to answer their question:\n"
                        f"========================================\n"
                        f"{safe_context}\n"
                        f"========================================\n\n"
                        f"USER QUESTION: {message}"
                    )
                    
                    message_for_history = injected_message
                    logger.info(f"✅ Injected file context into prompt for {session_id}")
                    # append user message to conversation history
                    conversation_history.append(HumanMessage(message_for_history))
                    
                dynamic_system_instruction_string = ""
                try:
                    # fetch those rules whose weight exceeds 0.8 and build the dynamic system instructions
                    print("Fetching rules with weights >= 0.8")
                    system_rules = supabase_client.table('chat_rules').select('rule','category', 'hard_rule').or_("weight.gte.0.7,hard_rule.eq.True").execute().data
                    hard_rules_injected = False
                    if system_rules:
                        system_rules = group_by_category(system_rules)
                        print("System rules after being grouped by category", system_rules)
                        dynamic_system_instruction_string += f"## STRICT RULES\n\n"

                        # iterate and build strict guidelines
                        for record in system_rules:
                            category = record["category"]
                            rules = record["rules"]
                            hard_rule_count = 1
                            for rule in rules:
                                rule_text = rule["text"]
                                hard_rule = rule["hard_rule"]
                                if not rule:
                                    print("Rule is not present, can't add to system instruction")
                                    continue
                                if hard_rule:
                                    dynamic_system_instruction_string += f"{hard_rule_count}.  {rule_text} \n"
                                    hard_rule_count += 1
                                    hard_rules_injected = True
                        
                        if not hard_rules_injected:
                            dynamic_system_instruction_string = f'\n ## OTHER GUIDELINES \n'
                        else:
                            dynamic_system_instruction_string += f"\n ## GUIDELINES \n"
                        # now build soft guidelines
                        for record in system_rules:
                            category = record["category"]
                            rules = record["rules"]
                            soft_rule_count = 1
                            dynamic_system_instruction_string += f'\n {category}_Rules \n'
                            for rule in rules:
                                rule_text = rule['text']
                                hard_rule = rule["hard_rule"]
                                if not rule:
                                    print("Rule is not present, can't add to system instruction")
                                    continue
                                if not hard_rule:        
                                    dynamic_system_instruction_string += f'{soft_rule_count}. {rule_text} \n'
                                    soft_rule_count += 1
                            
                            # iterate over all rules and add below corresponding category in the instruction string

                        if dynamic_system_instruction_string != "":
                            print("Dynamic system instructions string", dynamic_system_instruction_string)
                            # save system message in db

                            # use a different thread to optimize performance
                            asyncio.create_task(asyncio.to_thread(save_system_message_to_db, session_id,  dynamic_system_instruction_string,  unique_message_ids, supabase_client))
                            
                            # the rules injection logic in system message here
                        else:
                            print("No system instructions, continuing...")
                            continue
                except Exception as e:
                    print("Some error occured while building system instructions", e)
                    raise

                try:
                    # Prepare messages
                    base_messages = (
                        [{"role": "system", "content": dynamic_system_instruction_string}]
                        if dynamic_system_instruction_string else []
                    )
                    if not resend_flag:
                        # append user message to conversation history
                        conversation_history.append({"role": "user", "content": message_string, "id": user_message_id})
                        messages = base_messages + conversation_history
                
                    else:
                        messages = base_messages + conversation_history + [{"role": "user", "content": message_string}]
                        
                    response = active_agent.invoke(
                        {"messages": messages},
                    )

                    response = response['messages'][-1].content
                    
                    # generate a message id for response message
                    response_message_id = generate_uuid()
                    while response_message_id in unique_message_ids:
                        response_message_id = generate_uuid()
                    unique_message_ids.append(response_message_id)

                    user_message_id = user_message_id if not resend_flag else resend_message_id
                    # append assistant message to conversation history
                    conversation_history.append({"role": "assistant", "content": response or "", "id": response_message_id, "reply_to_message_id": user_message_id})

                    try:
                        supabase_client.table('chat_messages').insert({
                            "message_id": response_message_id,
                            "session_id": session_id,
                            "role": "assistant",
                            "content": response or "",
                            "reply_to_message_id": user_message_id
                        }).execute()
                        print("✅ Assistant message saved successfully!")
                    except Exception as e:
                        print("Some error occured while inserting assistant messages", e)

                    # generate title and description for the current chat history if there are 2 user/assistant messages each
                    # run the below logic in a seperate thread
                    asyncio.create_task(
                        asyncio.to_thread(
                            generate_title_description,
                            conversation_history,
                            session_id,
                            supabase_client
                        )
                    )

                    
                    if response:
                        await websocket.send_json({
                            "type": "assistance_response",
                            "message_id": response_message_id,
                            "content": response or "",
                            "resend_flag": resend_flag,
                            "reply_to_message_id": user_message_id,
                            "final": True
                        })


                    await websocket.send_json({"type": "streaming_end"})
                    await websocket.send_json({"type": "run_complete"})


                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                    print("Closing websocket...")
                    websocket.close()
                    break


                except Exception as e:
                    await websocket.send_json({"type": "assistance_response", "content": "Sorry, something went wrong."})
                    await websocket.send_json({"type": "streaming_end"})
                    await websocket.send_json({"type": "run_complete"})
                    raise


    except WebSocketDisconnect:
        logger.info("WebSocket closed")
        

    except Exception as e:
        logger.exception("WebSocket error")


# ------------------- APP RUNNER -------------------


if __name__ == "__main__":
    import uvicorn
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
