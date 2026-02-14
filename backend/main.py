import sys
import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, UploadFile, File, Form, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import List, Optional
import asyncio 
from dotenv import load_dotenv
from collections import defaultdict
import agent as agent_module
from contextlib import asynccontextmanager
from story_agent import story_agent
from utils.handle_feedback import handle_feedback
from utils.generate_title_description import generate_title_description
from utils.generate_uuid import generate_uuid
from utils.report_rule import insert_report_rule, delete_report_rule
from utils.refresh_instructions import refresh_system_instructions
from Clean_text import clean_text_with_groq
import logging
import secrets
from fastapi import UploadFile, File, Form
from file_service import process_uploaded_file
import shutil
import tempfile
from speech_to_text import SpeechToTextEngine
from text_to_speech import TextToSpeechEngine
from murf import Murf
from database import init_db_pool, close_db_pool
from file_service import process_uploaded_file
from quran_api import quran_router , parah_router, story_router
from reset_password_api import password_reset_router
from reflection_api import reflection_router
from api import (
    auth_router,
    notif_router,
    bookmark_router,
    profile_router,
    feedback_router,
    personalization_router
    
)
from reset_password_api import password_reset_router
from quran_api import quran_router , parah_router, story_router
from reset_password_api import password_reset_router
from reflection_api import reflection_router
from database import init_db_pool, close_db_pool, create_tables, delete_all_user_sessions, delete_user_session
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
import secrets
from speech_to_text import SpeechToTextEngine
from text_to_speech import TextToSpeechEngine
from config.db import get_supabase_client
from data.data import comprehensive_surah_metadata
from data.data import comprehensive_surah_metadata

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())



# Production logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    """Initialize database pool on startup"""
    print("Instantiating db pool")
    db_pool_instance = await init_db_pool()
    app.state.db_pool = db_pool_instance
    yield  # app stays active here while receiving requests
    
    # --- Shutdown Logic ---
    """Close database pool on shutdown"""
    await close_db_pool()
    
# ------------------- APP CONFIG -------------------
app = FastAPI(title="Tadabbur Agent API", lifespan=lifespan)
# ------------------- APP CONFIG -------------------
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Tadabbur Agent API",
        version="1.0.0",
        description="Backend API for Quranic Tadabbur Agent Application",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",\
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = custom_openapi


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
app.include_router(personalization_router)

FRONTEND_URL = os.getenv("FRONTEND_URL")  

print("FRONTEND_URL =", FRONTEND_URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def get_user_from_token(token: str):
    """
    Decodes the JWT token to get user_id.
    """
    if not SECRET_KEY:
        logger.error(" CRITICAL: SECRET_KEY is missing in main.py")
        return None

    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
         
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            logger.error(f" Token Valid but 'user_id' missing. Payload: {payload}")
            return None
        return user_id

    except JWTError as e:
        logger.error(f" JWT Validation Failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f" Unexpected Token Error: {str(e)}")
        return None


def get_chat_messages(session_id: str, user_id: str, supabase_client) -> List[str]:
    """Get all messages of a specific session"""
    if not session_id or not supabase_client:
        print("Session id or supabase client none, so returning...")
        return []

    chat_messages = supabase_client.table('chat_messages').select('message_id', 'user_id', 'role', 'content', 'reply_to_message_id', 'feedback', 'audio_url', 'has_verse_audio', 'audio_data', 'has_verse_image', 'verse_images').in_("role", ["user", "assistant"]).eq('session_id', session_id).eq('user_id', user_id).order('created_at').execute().data

    
    if chat_messages:
        return chat_messages
    else:
        return []

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

# ------------------- OPTIONAL HTTP ENDPOINT -------------------
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]


def clean_text(text: str) -> str:
    return text.replace("\x00", "")


@app.get("/")
def read_root():
    return {"message": "Hello brothers"}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...), 
    session_id: str = Form(...)
):
    try:
        extracted_text = await process_uploaded_file(file)
        logger.info(f"File processed for session {session_id}. Text length: {len(extracted_text)}")
        return {"status": "success", "message": "File processed successfully.", "extracted_text": clean_text(extracted_text)}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}/files")
async def get_session_files(session_id: str):
    """Get all uploaded files for a session"""
    try:
        supabase_client = get_supabase_client()

        files = supabase_client.table('session_files')\
            .select('file_id, file_name, file_type, file_size, created_at')\
            .eq('session_id', session_id)\
            .order('created_at', desc=True)\
            .execute()

        return {
            "status": "success",
            "session_id": session_id,
            "files": files.data or []
        }

    except Exception as e:
        logger.error(f"Error fetching files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}/files/{file_id}")
async def delete_session_file(session_id: str, file_id: str):
    """Delete a specific file from session"""
    try:
        supabase_client = get_supabase_client()

        # Delete from session_files
        supabase_client.table('session_files')\
            .delete()\
            .eq('file_id', file_id)\
            .eq('session_id', session_id)\
            .execute()

        # Rebuild file_context from remaining files
        remaining_files = supabase_client.table('session_files')\
            .select('file_content')\
            .eq('session_id', session_id)\
            .order('created_at')\
            .execute()

        # Filter out None values
        valid_contents = [
            f['file_content'] for f in remaining_files.data
            if f['file_content'] is not None and f['file_content'].strip()
        ]
        new_context = "\n\n--- FILE SEPARATOR ---\n\n".join(valid_contents) if valid_contents else ""

        # Update chat_sessions
        supabase_client.table('chat_sessions').update({
            'file_context': new_context or None
        }).eq('session_id', session_id).execute()

        # Update cache
        if new_context:
            session_file_context[session_id] = new_context
        else:
            session_file_context.pop(session_id, None)

        return {"status": "success", "message": "File deleted"}

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
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


async def stream_tts_audio(tts_engine, clean_text, websocket, message_id_ref):
    async for audio_chunk in tts_engine.stream_audio(clean_text):
        await websocket.send_json({
            "type": "tts_audio_url",
            "message_id": message_id_ref,
            "audio": audio_chunk
        })


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = Query(...)):

    user_id = get_user_from_token(token)
    
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("WebSocket connection rejected: Invalid Token")
        return 

    await websocket.accept()
    logger.info(f"WebSocket connected successfully for User ID: {user_id}")
    
    
    dynamic_system_instruction = {"text":""}
    asyncio.create_task(refresh_system_instructions(dynamic_system_instruction, user_id))
    try: 

        supabase_client = get_supabase_client()
    except Exception as e:
        print("Some error occured initiating supabase connection", e)
        raise

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
                user_message_id = data.get("reply_to_message_id")
                
                if not message_id_ref or not user_message_id or not raw_text:
                    print("Can't read aloud, important information is missing....")
                    continue
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
                        if res.audio_file:
                            print("Audio url", res.audio_file)

                            supabase_client.table('chat_messages').update({
                                'audio_url': res.audio_file
                            }).eq('message_id', message_id_ref).execute()
                            
                            print(f"✅ Audio URL saved to database for message {message_id_ref}")

                            
                            await websocket.send_json({
                                "type": "tts_audio_url",
                                "message_id": message_id_ref,
                                "user_id": user_message_id,
                                "audio_url": res.audio_file
                            })
                            
                    except Exception as e:
                        print("Some error occured while generating audio for text", e)
                        continue

                continue

            # ========== SESsION CODE START ==========
            # SESSION INIT
            if data.get("type") == "session-init":
                    requested_session_id = data.get("session_id", "").strip()
                    
                    if requested_session_id:
                        session_id = requested_session_id
                    else:
                        session_id = generate_session_id()

                    logger.info(f"Processing session: {session_id}")

                    # 2. Check DB securely
                    try:
                        response = supabase_client.table('chat_sessions')\
                            .select('user_id', 'file_context')\
                            .eq('session_id', session_id)\
                            .execute()
                        
                        existing_session = response.data[0] if response.data and len(response.data) > 0 else None

                        if existing_session:
                            # Session Exists: Check Ownership
                            if existing_session.get('user_id') == user_id:
                                if existing_session.get('file_context'):
                                    session_file_context[session_id] = existing_session['file_context']
                                
                                # Load Messages
                                msgs = supabase_client.table('chat_messages').select('message_id').eq('session_id', session_id).execute()
                                unique_message_ids = [m['message_id'] for m in msgs.data] if msgs.data else []
                                
                                await websocket.send_json({
                                    "type": "session_id", "status": "acknowledged", 
                                    "session_id": session_id, "message_ids": unique_message_ids
                                })
                            else:
                                await websocket.send_json({"type": "session_id", "status": "error", "error": "Unauthorized"})
                                continue
                        else:
                            logger.info(f"🆕 Generated ID for potential new session: {session_id}")
                            
                            conversation_history = []
                            unique_message_ids = []
                            
                            await websocket.send_json({
                                "type": "session_id", "status": "acknowledged",
                                "session_id": session_id, "current_agent": current_agent_name,
                                "message_ids": []
                            })

                    except Exception as e:
                        logger.error(f"Session Init Error: {e}")
                        await websocket.send_json({"type": "session_id", "status": "error", "error": str(e)})
                    
                    continue
            
            # Handle CHAT HISTORY request
            if data.get("type") == "chat_history":
                try:
                    chat_sessions = supabase_client.table('chat_sessions')\
                        .select('session_id', 'title', 'description', 'created_at')\
                        .eq('user_id', user_id)\
                        .order('created_at', desc=True)\
                        .execute().data

                    await websocket.send_json({
                        "type": "chat_history",
                        "status":"acknowledged",
                        "chat_history": chat_sessions
                    })
                    logger.info(f"Sent {len(chat_sessions)} sessions to frontend for user {user_id}")
                except Exception as e:
                    logger.error(f"Error fetching chat history: {e}")
                    await websocket.send_json({
                        "type": "chat_history",
                        "status": "error",
                        "error": str(e)
                    })
                continue

            if data.get("type") == "get_chat":
                requested_session_id = data.get("session_id", "")
                try:
                    chat_history = get_chat_messages(requested_session_id, user_id, supabase_client)

                    try:
                        combined_file_content = ''
                        files_response = supabase_client.table('session_files')\
                            .select('file_id, file_name, file_type, message_id')\
                            .eq("user_id", user_id).eq('session_id', requested_session_id)\
                            .order('created_at')\
                            .execute().data
                        
                        files_by_message = defaultdict(list)
                        
                        if files_response:
                            for f in files_response or []:
                                file_content = f.get("file_content", "")
                                file_name = f.get("file_name", "")
                                if file_content and file_name:
                                    combined_file_content += (f"\n\n --- File Name: {file_name} ---\n\n File Content: {file_content}")
                                files_by_message[f["message_id"]].append({
                                    "attachmentType": f.get("file_type", ""),
                                    "attachmentName": f.get("file_name", "")
                                })
                    except Exception as e:
                        logger.error(f"Error fetching or processing files: {e}")
                    
                    if combined_file_content:
                        session_file_context[requested_session_id] = combined_file_content
                    for msg in chat_history:
                        msg["attachments"] = files_by_message.get(msg["message_id"], [])                    
                    # Update local state
                    session_id = requested_session_id
                    conversation_history = chat_history or []
                    unique_message_ids = [msg['message_id'] for msg in conversation_history]

                    await websocket.send_json({
                        "type": "get_chat",
                        "status": "acknowledged",
                        "session_id": session_id,
                        "user_id": user_id,
                        "chat_history": chat_history,
                        "unique_message_ids": unique_message_ids,
                    })
                except Exception as e:
                    logger.error(f"Error loading chat: {e}")
                continue

            # Handle DELETE SESSION request
            if data.get("type") == "delete_session":
                session_id_to_delete = data.get("session_id", "")

                if not session_id_to_delete:
                    await websocket.send_json({
                        "type": "delete_session",
                        "status": "error",
                        "error": "session_id is required"
                    })
                    continue

                try:
                    success = await delete_user_session(user_id, session_id_to_delete)
                    if success:
                        await websocket.send_json({
                            "type": "delete_session",
                            "status": "success",
                            "session_id": session_id_to_delete
                        })
                        logger.info(f"Deleted session {session_id_to_delete} for user {user_id}")
                    else:
                        await websocket.send_json({
                            "type": "delete_session",
                            "status": "error",
                            "error": "Session not found or access denied"
                        })
                except Exception as e:
                    logger.error(f"Error deleting session: {e}")
                    await websocket.send_json({
                        "type": "delete_session",
                        "status": "error",
                        "error": str(e)
                    })
                continue

            # Handle DELETE ALL SESSIONS request
            if data.get("type") == "delete_all_sessions":
                try:
                    success = await delete_all_user_sessions(user_id)
                    if success:
                        await websocket.send_json({
                            "type": "delete_all_sessions",
                            "status": "success"
                        })
                    else:
                        await websocket.send_json({
                            "type": "delete_all_sessions",
                            "status": "error",
                            "error": "Failed to delete sessions"
                        })
                except Exception as e:
                    logger.error(f"Error deleting all sessions: {e}")
                    await websocket.send_json({
                        "type": "delete_all_sessions",
                        "status": "error",
                        "error": str(e)
                    })
                continue

            # === AGENT SWITCH ===
            if data.get("type") == "agent":
                agent_name = data.get("agent")
                if agent_name:
                    if agent_name == "story-telling":
                        print("Main agent set to story")
                        active_agent = story_agent        
                    else:
                        active_agent = agent_module.main_agent
                        print("Main agent sent to main agent")
                continue
            # ============================= MODEL SELECTION HANDLER =============================
            if data.get("type") == "model-selection":
                requested_model = data.get("model")
                
                is_valid = (requested_model in agent_module.SUPPORTED_CHAT_MODELS or 
                            requested_model in agent_module.SUPPORTED_CHAT_MODELS.values())

                if is_valid:
                    session_model_key = requested_model
                    
                    display_name = requested_model
                    if requested_model in agent_module.SUPPORTED_CHAT_MODELS:
                        display_name = requested_model 
                    
                    if current_agent_name == "QuranTadabburAgent":
                        print(f"🔄 Hot-swapping Main Agent to model: {session_model_key}")
                        active_agent = agent_module.get_agent_by_user_age(
                            age=25, 
                            username="DefaultUser", 
                            model_key=session_model_key
                        )
                    else:
                        print(f"⚠️ Model pref saved as {session_model_key}, but not applied immediately because user is in {current_agent_name} mode.")

                    await websocket.send_json({
                        "type": "model-selection",
                        "status": "acknowledged",
                        "model": requested_model,
                        "display_name": display_name
                    })
                    
                    await websocket.send_json({
                        "type": "loading_message",
                        "content": f"Switched to **{display_name}**"
                    })
                    
                    logger.info(f"Model preference updated to: {display_name}")
                
                else:
                    await websocket.send_json({
                        "type": "model-selection",
                        "status": "not-acknowledged",
                        "model": requested_model,
                        "error": "This model is not supported.",
                        "available": list(agent_module.SUPPORTED_CHAT_MODELS.keys())
                    })
                continue  
            

            if data.get("type") == "undo-report":
                print("Undo request")
                message_id = data.get("message_id")
                if not message_id: 
                    print("No message ID found for reported message")
                    continue
                try:
                    # delete hard rule in a different thread for optimization
                    await asyncio.to_thread(delete_report_rule, supabase_client, message_id, user_id)
                    await websocket.send_json({
                        "type": "undo-report",
                        "status": "acknowledged",
                        "message_id": message_id,
                        "user_id": user_id
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
                            print("Reported assistant message", reported_assistant_message['content'] )
                            response = await asyncio.to_thread(insert_report_rule, supabase_client, message_id, feedback, user_id)

                            print("Report response", response)
                            if not response:
                                await websocket.send_json({
                                    "type": "report",
                                    "user_id": user_id,
                                    "message_id": message_id,
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
                    print(f"An error occured while reporting the assistant's response {message_id}")    
                    if not ack_sent:
                        await websocket.send_json({
                        "type": "report",
                        "status": "not-acknowledged"
                    })
                continue

            if data.get("type") in ["liked", "disliked"]:
                type = data.get("type")
                session_id = data.get('session_id')
                message_id = data.get('message_id')
                message = data.get("message")
                if not session_id or not message_id or not message:
                    print("No message or session ID, can't proceed to feedback submission")
                    continue
                asyncio.create_task(asyncio.to_thread(handle_feedback, type, message, message_id, user_id))
                continue

            # === MAIN CHAT MESSAGE ===
            if data.get("type") == "user_message":
                role = data.get("role", "user")
                message = data.get("content", "")
                user_message_id = data.get("message_id")
                additional_instructions = data.get("system_instructions")
                resend_flag = data.get("resend_flag")
                resend_message_id = data.get("resend_message_id")
                new_file_text = data.get("new_file_context")
                
                if new_file_text:
                    logger.info(f"💾 Committing new file context to session {session_id}")
                    existing_context = session_file_context.get(session_id, "")
                    updated_context = existing_context + "\n\n--- FILE CONTENT ---\n" + new_file_text
                    session_file_context[session_id] = updated_context
                    try:
                        await asyncio.to_thread(
                            lambda: supabase_client.table('chat_sessions').update({
                                'file_context': updated_context
                            }).eq('session_id', session_id).execute()
                        )
                    except Exception as db_e:
                        logger.error(f"Failed to save file context to DB: {db_e}")
                if user_message_id not in unique_message_ids:
                    unique_message_ids.append(user_message_id)

                message_string = message + (f"\n\n {additional_instructions}" if additional_instructions else "")

                if not resend_flag:
                    try:
                        # Check if session exists in DB before inserting message
                        sess_check = supabase_client.table('chat_sessions').select('session_id').eq('session_id', session_id).execute()
                        if not sess_check.data:
                            logger.info(f"📝 First message detected. Persisting session {session_id} to DB.")
                            supabase_client.table("chat_sessions").insert({
                                'session_id': session_id, 
                                'user_id': user_id,   
                            }).execute()
                    except Exception as sess_e:
                        logger.error(f"Failed to lazy-create session: {sess_e}")

                if not resend_flag:
                    try:
                        supabase_client.table('chat_messages').insert({
                            "message_id": user_message_id,
                            "user_id": user_id, 
                            "session_id": session_id,
                            "role": role,
                            "content": message_string,
                        }).execute()
                        print("✅ User message saved successfully!")
                    except Exception as e:
                        print("Some error occured while inserting user messages", e)
                        raise
                
                if not resend_flag:
                    file_name = data.get("file_name")
                    file_type = data.get("file_type")
                    
                    if file_name and new_file_text:
                        try:
                            supabase_client.table('session_files').insert({
                                "file_id": generate_uuid(),
                                "file_name": file_name,
                                "file_type": file_type,
                                "file_content": new_file_text, 
                                "message_id": user_message_id,
                                "session_id": session_id,
                                "user_id": user_id
                            }).execute()
                            print(f"✅ File record '{file_name}' saved to session_files")
                        except Exception as e:
                            print("Error saving to session_files:", e)

                logger.info(f"[{current_agent_name}] Session: {session_id} | Message: {message_string} ...")
                # File Feature - Check current session first, then fallback to default_session
                 
                if new_file_text:
                    new_file_text = "\n\n--- FILE CONTENT ---\n" + new_file_text
                    logger.info(f"📚 Found context for session {session_id}: {len(new_file_text)} chars")
                    safe_context = (new_file_text[:8000] + '... [TRUNCATED]') if len(new_file_text) > 8000 else new_file_text
                    message_string = (
                        f"The user has attached a file. Use the following content to answer the user's question:\n"
                        f"========================================\n"
                        f"{safe_context}\n"
                        f"========================================\n\n"
                        f"USER QUESTION: {message_string}"
                    )

                    logger.info(f"✅ Injected file context into prompt for {session_id}")
                # print("Dynamic system instructions", dynamic_system_instruction["text"])
                try:
                    # Prepare messages
                    base_messages = (
                        [{"role": "system", "content": dynamic_system_instruction["text"]}]
                        if dynamic_system_instruction["text"] else []
                    )
                    print("Message string", message_string)
                    if not resend_flag:
                        # append user message to conversation history
                        conversation_history.append({"role": "user", "content": message_string, "id": user_message_id})
                        messages = base_messages + conversation_history
                    else:
                        messages = base_messages + conversation_history + [{"role": "user", "content": message_string}]
                        
                    agent_response = active_agent.invoke(
                        {"messages": messages},
                    )

                    structured_output = agent_response['structured_response']
                    
                    # generate a message id for response message
                    response_message_id = generate_uuid()
                    while response_message_id in unique_message_ids:
                        response_message_id = generate_uuid()
                    unique_message_ids.append(response_message_id)

                    user_message_id = user_message_id if not resend_flag else resend_message_id

                    response = structured_output.response or ""
                    has_verse_audio = structured_output.has_verse_audio or False
                    has_verse_image = structured_output.has_verse_image or False


                    audio_data = [a.model_dump() for a in (structured_output.audio_data or [])]
                    verse_images = [v.model_dump() for v in (structured_output.verse_images or [])]

                    # append assistant message to conversation history
                    conversation_history.append({"role": "assistant", "content": response , "id": response_message_id, "reply_to_message_id": user_message_id})
                    
                    try:
                        supabase_client.table('chat_messages').insert({
                            "message_id": response_message_id,
                            "session_id": session_id,
                            "user_id": user_id,
                            "role": "assistant",
                            "content": response,
                            "reply_to_message_id": user_message_id,
                            "has_verse_audio": has_verse_audio,
                            "audio_data": audio_data,
                            "has_verse_image": has_verse_image,
                            "verse_images": verse_images 
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

                    if structured_output:
                        await websocket.send_json({
                            "type": "assistance_response",
                            "message_id": response_message_id,
                            "content": structured_output.model_dump() or "",
                            "resend_flag": resend_flag,
                            "reply_to_message_id": user_message_id,
                            "final": True
                        })

                    # # tool logic

                    await websocket.send_json({"type": "streaming_end"})
                    await websocket.send_json({"type": "run_complete"})


                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                    print("Closing websocket...")
                    await websocket.close()
                    break


                except Exception as e:
                    await websocket.send_json({"type": "assistance_response", "content": "Sorry, something went wrong."})
                    await websocket.send_json({"type": "streaming_end"})
                    await websocket.send_json({"type": "run_complete"})
                    raise


    except WebSocketDisconnect:
        logger.info(f"WebSocket closed for user {user_id}")

    except RuntimeError as e:
        if "websocket.close" in str(e) or "response already completed" in str(e):
            logger.info(f"WebSocket disconnected during send operation for user {user_id}")
        else:
            logger.exception("RuntimeError in WebSocket")

    except Exception as e:
        logger.exception("WebSocket error")


# ------------------- APP RUNNER -------------------


if __name__ == "__main__":
    import uvicorn
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
    uvicorn.run("main:app", host="0.0.0.0", port=8000)