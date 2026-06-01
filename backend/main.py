import sys
import os
import json
import asyncio
from datetime import datetime, timezone
import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from fastapi.responses import RedirectResponse, Response
import httpx
from fastapi.websockets import WebSocketState
from pydantic import BaseModel
from typing import List
import asyncio 
from generators.image_generator import generate_image
from models.models import NormalOutputSchema, SurahForAudio, SurahForImage, StoryOutputSchema, StoryParagraph
from langchain.messages import ToolMessage, SystemMessage, HumanMessage
from collections import defaultdict
from huggingface_hub.utils import HfHubHTTPError
from contextlib import asynccontextmanager
import tadabbur_agents.agent as agent_module
from tadabbur_agents.story_agent import story_agent
from utils.handle_feedback import handle_feedback
from utils.generate_title_description import generate_title_description
from utils.generate_uuid import generate_uuid
from utils.report_rule import insert_report_rule
from utils.refresh_instructions import refresh_system_instructions
from utils.authentication import generate_session_id, get_user_from_token
from utils.Clean_text import clean_text_with_groq
import logging
from utils.speech_to_text import SpeechToTextEngine
from murf import Murf
from api.reset_password_api import password_reset_router
from fastapi import UploadFile, File, Form, HTTPException
from tools.file_service import process_uploaded_file
from api.api import (
    auth_router,
    notif_router,
    bookmark_router,
    profile_router,
    feedback_router,
    personalization_router,
    file_router,
    transcribe_audio_router
)
from api.quran_api import quran_router , parah_router, story_router
from api.reflection_api import reflection_router
from data.database import init_db_pool, close_db_pool, delete_all_user_sessions, delete_user_session, get_db_connection
from fastapi.openapi.utils import get_openapi
from config.db import get_supabase_client
from utils.db_retry import db_retry, DBRetryError
from utils.ws_retry import ws_send, WSDisconnectedError
from typing import Literal

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
async def lifespan(app:FastAPI):                
    for attempt in range(5):
        try:
            db_pool_instance = await init_db_pool()
            app.state.db_pool = db_pool_instance
            break
        except Exception as e:  
            print(f"DB pool init attempt {attempt + 1} failed: {e}")
            if attempt < 4:     
                await asyncio.sleep(5)
            else:
                # prevent server from starting if all attempts fail
                raise  
    yield
    await close_db_pool() 
    
# ------------------- APP CONFIG -------------------
app = FastAPI(title="Tadabbur Agent API", lifespan=lifespan)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
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
app.include_router(file_router)
app.include_router(transcribe_audio_router)

FRONTEND_URL = os.getenv("FRONTEND_URL")  

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === SESSION CODE START ===

session_file_context = {}
session_agent_running = {}
supabase_client = None
TADABBUR_PROJECT_URL = os.getenv("TADABBUR_PROJECT_URL") 
TADABBUR_API_KEY = os.getenv("TADABBUR_API_KEY")

try: 
    supabase_client = get_supabase_client()
except Exception as e:
    print("Some error occured initiating supabase connection", e)
    raise

TOOL_MESSAGES = {
    "searchAsbabNuzul": {
        "start": "Searching Asbab al-Nuzul",
        "end": "Narrations found"
    },
    "Search_Quran_By_filters": {
        "start": "Searching Quran verses",
        "end": "Verses retrieved"
    },
    "get_Quran_Audio": {
        "start": "Fetching Quran recitation",
        "end": "Audio ready"
    },
    "get_verse_image": {
        "start": "Loading verse images",
        "end": "Images loaded"
    },
    "story_agent_tool": {
        "start": "Structuring your story",
        "end": "Story structure ready"
    },
    "Submit_Quran_Response": {
        "start": "Composing response",
        "end": "Response ready"
    },
    "generate_ai_images_story": {
        "start": "Generating your story",
        "end": "Processing your results"
    }
}

async def dismiss_user_request(websocket: WebSocket, type:str, error:str, label: str, extra_payload: dict = None) -> bool:
    "Returns True if should break, False otherwise"
    try:
        await ws_send(websocket, {
            "type": type,
            "status": "not-acknowledged",
            "error": error,
            **(extra_payload or {})
        }, label = label)
        return False
    except WSDisconnectedError:
        return True
    except Exception:
        logger.info("Critical error, can't proceed.")
        await safe_close_websocket(websocket)
        return True


async def safe_close_websocket(websocket: WebSocket):
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code = 1011, reason = "Internal server error")
    except Exception:
        pass

async def cleanup_on_error(websocket, user_message_saved_to_db: bool, assistant_message_saved_to_db: bool, user_message_id: str, response_message_id: str) -> bool:
    if user_message_saved_to_db:
        logger.info("Cleaning up errorenous messages.")
        to_be_deleted_messages_array = []
        old_messages = await db_retry(
            lambda: supabase_client.table('chat_messages').select('*').eq("role", "assistant").eq("reply_to_message_id", user_message_id).execute(), label = "get_saved_assistant_responses"
        )
        old_messages = old_messages.data if old_messages else []
        if (len(old_messages) <= 1):
            to_be_deleted_messages_array.append(user_message_id)
            to_be_deleted_messages_array.append(response_message_id)
        elif (len(old_messages) > 1) and assistant_message_saved_to_db:
            to_be_deleted_messages_array.append(response_message_id)
        # delete both assistant and user message
        if to_be_deleted_messages_array:
            await db_retry(
            lambda: supabase_client.table('chat_messages').delete().in_("message_id", to_be_deleted_messages_array).execute(), label = "delete_user_assistant_messages"
            )
            return True
    return False


async def run_agent_with_progress(active_agent, messages, context: agent_module.UserContext, websocket) -> dict | None:
    final_messages = []
    tools_called = set()

    async for event in active_agent.astream_events(
        {"messages": messages},
        context=context,
        version="v2"
    ):
        event_type = event["event"]
        tool_name = event.get("name", "")

        if event_type == "on_tool_start" and tool_name in TOOL_MESSAGES:
            if tool_name not in tools_called:
                tools_called.add(tool_name)
                try:
                    await ws_send(websocket, {
                        "type": "loading_message",
                        "content": TOOL_MESSAGES[tool_name]["start"]
                    }, label="tool_start")
                except WSDisconnectedError:
                    raise

        elif event_type == "on_tool_end" and tool_name in TOOL_MESSAGES:
            if tool_name in tools_called:
                end_msg = TOOL_MESSAGES[tool_name].get("end")
                if end_msg:
                    try:
                        await ws_send(websocket, {
                            "type": "loading_message",
                            "content": end_msg
                        }, label="tool_end")
                    except WSDisconnectedError:
                        raise

        elif event_type == "on_chain_end":
            output = event.get("data", {}).get("output")
            if isinstance(output, dict) and "messages" in output:
                final_messages = output["messages"]

    return {"messages": final_messages}


@app.get("/api/story-image/{filename}")
async def get_story_image(filename: str, token: str = Query(...)):
    user_id = get_user_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    signed = supabase_client.storage.from_(
        os.getenv("GENERATED_IMAGES_BUCKET", "generated-images")
    ).create_signed_url(path=filename, expires_in=60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        img_response = await client.get(signed["signedURL"])
    
    return Response(
        content=img_response.content,
        media_type="image/png"
    )

def get_chat_messages(session_id: str, user_id: str, supabase_client) -> List[str]:
    """Get all messages of a specific session"""
    if not session_id or not supabase_client:
        print("Session id or supabase client none, so returning...")
        return []

    chat_messages = supabase_client.table('chat_messages').select('message_id', 'user_id', 'role', 'content', 'reply_to_message_id', 'feedback', 'audio_url', 'has_verse_audio', 'audio_data', 'has_verse_image', 'verse_images', 'is_error','story_data').in_("role", ["user", "assistant"]).eq('session_id', session_id).order('created_at').execute().data

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



class UnsavedFileContext(BaseModel):
    has_unsaved_file_context:bool = False
    file_id: str | None


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = Query(...)):

    user_id = get_user_from_token(token)
    
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("WebSocket connection rejected: Invalid Token")
        return 

    await websocket.accept()
    logger.info(f"WebSocket connected successfully for User ID: {user_id}")

    user_age = 25
    user_name = 'User'
    try:
        async with get_db_connection() as conn:
            result = await conn.fetchrow("""
                SELECT username, age 
                FROM users 
                WHERE user_id = $1 AND is_personalized = TRUE
            """, user_id)
            
            if result:
                user_age = result['age'] or 25
                user_name = result['username'] or 'User'
                logger.info(f"Personalization loaded: {user_name}, age={user_age}")
            else:
                logger.info(f"No personalization found for {user_id}, using defaults")
    except Exception as e:
        logger.warning(f"Could not load personalization for {user_id}, using defaults: {e}")

    dynamic_system_instruction = {"text":""}
    asyncio.create_task(refresh_system_instructions(dynamic_system_instruction, user_id))

    # fetch all unique session_ids and message_ids
    unique_session_ids = [item['session_id'] for item in (supabase_client.table("chat_sessions").select("session_id").execute().data or [])]

    unique_message_ids = [item['message_id'] for item in (supabase_client.table("chat_messages").select("message_id").execute().data or [])]
    # initialize important variables
    conversation_history = []
    is_new_session = False
    unsaved_file_context = UnsavedFileContext(has_unsaved_file_context=False, file_id = None)
    current_mode = "normal"
    # ====== SESSION CODE START ======
    session_id = None
    session_model_key: str = agent_module.DEFAULT_CHAT_MODEL
    active_agent = agent_module.get_agent(session_model_key)
    current_agent_name = active_agent.name
    try:
        while True:
            if websocket.client_state == WebSocketState.DISCONNECTED:
               break
            message = await websocket.receive()
            if "text" not in message:
                continue
            try:
                data = json.loads(message["text"])
            except json.JSONDecodeError:
                continue
            
            if data.get("type") == "ping":
                if websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json({"type": "pong"})
                    except Exception:
                        pass # Socket might have closed just now
                continue

            if data.get("type") == "tts_audio_url":
                try:
                    raw_text = data.get("text")
                    message_id_ref = data.get("message_id")
                    user_message_id = data.get("reply_to_message_id")
                    if not message_id_ref or not user_message_id or not raw_text:
                        logger.info("""Can't process TTS Request, one of the following may be missing: 
                            \n 1. Message ID 
                            \n 2. User Message ID
                            \n 3. Text for TTS"""
                        )
                        if await dismiss_user_request(websocket, f"tts_audio_url_{user_message_id}_{message_id_ref}", "not-acknowledged", "Some error occured while processing TTS Request. Please try again.", "tts_request_error"):
                            break
                        continue
                    logger.info(f"≡ƒº╣ Cleaning text with Groq Agent...")
                    
                    clean_text = await clean_text_with_groq(raw_text)
                    
                    logger.info(f"≡ƒÄñ Stream audio for: {clean_text[:50]}...")
                    client = Murf(
                        api_key=os.getenv("MURF_AI_API_KEY") 
                    )
                    res = client.text_to_speech.generate(
                        text=clean_text,
                        voice_id ="Finley",
                        style ="Promo",
                        rate = 0,
                        pitch = 0,
                        variation = 1
                    )
                    if res.audio_file:
                        await db_retry(
                            lambda: supabase_client.table('chat_messages').update({
                                'audio_url': res.audio_file
                            }).eq('message_id', message_id_ref).execute(),
                            label = "update_tts_audio_url"
                        )
                        logger.info(f"✅ Updated message {message_id_ref} with TTS audio URL in DB")
                    
                        await ws_send(websocket, {
                            "type": f"tts_audio_url_{user_message_id}_{message_id_ref}",
                            "status": "acknowledged",
                            "message_id": message_id_ref,
                            "user_id": user_message_id,
                            "audio_url": res.audio_file
                        }, label="tts_audio_url")
                except Exception as e:
                    logger.info(f"Some error occured while processing request for TTS generation: {e}")
                    if await dismiss_user_request(websocket, f"tts_audio_url_{user_message_id}_{message_id_ref}", "not-acknowledged", "Some error occured while processing TTS Request. Please try again.", "tts_request_error"):
                        break
                continue

            if data.get("type") == "stop_generation":
                try:
                    partial_content = data.get("partial_content", "")
                    message_id = data.get("message_id", "")
                    if not partial_content or not message_id:
                        logger.info("""
                        **Can't process stop generation request, one of the following may be missing:** 
                            1. Partial Content
                            2. Message ID
                        """)
                        if await dismiss_user_request(websocket, "stop_generation", "not-acknowledged", "Some unexpected error occured while stopping response generation.", "stop_generation_error"):
                            break 
                        continue

                    await db_retry(
                        lambda: supabase_client.table('chat_messages')
                            .update({"content": partial_content})
                            .eq("message_id", message_id)
                            .execute(),
                        label="stop_generation_save"
                    )
                    await ws_send(websocket, {
                        "type": "stop_generation",
                        "status": "acknowledged",
                        "message_id": message_id
                    }, label="stop_generation_acknowledged")
                    
                except Exception as e:
                    logger.info(f"Some error occured while processing request for stop generation, Error: {e}")
                    if await dismiss_user_request(websocket, "stop_generation", "not-acknowledged", "Some unexpected error occured while stopping response generation.", "stop_generation_error"):
                        break
                continue

            # ========== SESsION CODE START ==========
            # SESSION INIT
            if data.get("type") == "session-init":
                try:
                    requested_session_id = data.get("session_id", "").strip()
                    mode = data.get("mode", "normal")
                    current_mode = mode
                    if current_mode == "story":
                        if user_id not in ["8672cbf6-7df6-4714-8d34-a43d65c378db", "f27c0d6c-f35a-4352-8410-777a72b3e6b3", "37d6d8f9-a5e0-49cf-a315-5fadfd46253f"]:
                            # only allow myself in story mode
                            continue
                    active_agent = agent_module.get_agent(session_model_key) if current_mode == "normal" else story_agent
                    logger.info(f"Session mode: {mode}")

                    # generate session id in case it's missing
                    if not requested_session_id:
                        requested_session_id = generate_session_id()
                    # ensures session id uniqueness
                    while requested_session_id in unique_session_ids:
                        requested_session_id = generate_session_id()

                    # add to the list of unique session ids
                    unique_session_ids.append(requested_session_id)
                    # clear conversation history array - new session
                    conversation_history.clear()
                    session_id = requested_session_id
                    # set is new session to true
                    is_new_session = True
                    # reset unsaved_file_context
                    unsaved_file_context = UnsavedFileContext(has_unsaved_file_context= False, file_id = None)
                    logger.info(f"Processing session: {session_id}")
                    # remove exisiting session logic because session-init is meant to create a new session so checking old session existence is unpurposeful
                    logger.info(f"🆕 Generated ID for new session: {session_id}")
                    try:
                        await ws_send(websocket, {
                            "type": "session-init", "status": "acknowledged",
                            "session_id": session_id, "current_agent": current_agent_name,
                            "message_ids": [],
                            "mode": mode
                        }, label="session_init")
                    except WSDisconnectedError:
                        break
                    except Exception:
                        # critical error, can't proceed
                        logger.info("☣️ Critical error, safe closing websocket...")
                        safe_close_websocket(websocket)
                        break
                except Exception as e:
                    logger.error(f"Session Init Error: {e}")
                    # have to see how this status error reflects on frontend
                    try:
                        await ws_send(websocket, {"type": "session-init", "status": "not_acknowledged", "error": "Session initialization failed"}, label="session_init_error")
                    except WSDisconnectedError:
                        break
                    except:
                        # critical error, can't proceed
                        logger.info("☣️ Critical error, safe closing websocket...")
                        await safe_close_websocket(websocket)
                        break
                continue
            # Handle CHAT HISTORY request
            if data.get("type") == "chat_history":
                try:
                    chat_sessions = await db_retry(
                        lambda: supabase_client.table('chat_sessions')
                        .select('session_id', 'title', 'description', 'created_at')
                        .eq('user_id', user_id)
                        .order('created_at', desc=True)
                        .execute(), label="fetch_chat_sessions"
                    )
                    
                    await ws_send(websocket, {
                        "type": "chat_history",
                        "status": "acknowledged",
                        "chat_history": chat_sessions.data if chat_sessions else []
                    }, label="chat_history_response")
                    
                    logger.info(f"Sent {len(chat_sessions.data if chat_sessions else [])} sessions")
                except WSDisconnectedError:
                    break
                except (DBRetryError, Exception) as e:
                    logger.error(f"Chat history error: {e}")
                    try:
                        await ws_send(websocket, {
                            "type": "chat_history",
                            "status": "not-acknowledged",
                            "error": "Some unexpected error occurred while fetching chat_history, Please try again later."
                        }, label="chat_history_error")
                    except WSDisconnectedError:
                        break
                    except Exception:
                        await safe_close_websocket(websocket)
                        break
                continue    
            
            if data.get("type") == "get_images":
                try:
                    if not user_id:
                        logger.info("Missing User ID")
                        if await dismiss_user_request(websocket, "get_images", "Can't process request for images, please try again.", "image_fetching_error"):
                            break
                        continue
                    res = await db_retry(
                        lambda: supabase_client.table("chat_messages").select("message_id, story_data").eq("user_id", user_id).execute(), label ="fetch_images")
                    rows = res.data
                    images = []
                    for row in rows:
                        for obj in row.get("story_data") or []:
                            img = obj.get("image")
                            if img:
                                images.append({"image_url":img})
                    await ws_send(websocket, {
                        "type":"get_images",
                        "status":"acknowledged",
                        "images": images,
                    }, label = "get_images_response")
                    continue
                    
                except Exception as e:
                    logger.info(f"Some error occured while fetching images for user with user_id {user_id}, Error: {e}")
                    if await dismiss_user_request(websocket, "get_images", "Can't process request for images, please try again.", "image_fetching_error"):
                        break
                    continue
                
            if data.get("type") == "get_chat":
                try:
                    requested_session_id = data.get("session_id", "")
                    if not requested_session_id:
                        logger.info("No session id present, can't proceed")
                        if await dismiss_user_request(websocket, "get_chat", "Some error occured while fetching chat session. Please try again", "get_chat_failed"):
                            break
                        continue
                    logger.info(f"📥 get_chat request for session: {requested_session_id}")
                    # set the current session_id
                    session_id = requested_session_id
                    chat_history = await asyncio.to_thread(get_chat_messages, session_id, user_id, supabase_client)
                    files_response = await asyncio.to_thread(
                        lambda: supabase_client.table('session_files')
                        .select('file_id, file_name, file_type, message_id, file_content')
                        .eq("user_id", user_id).eq('session_id', requested_session_id)
                        .order('created_at').execute()
                    )
                    session_response = supabase_client.table("chat_sessions").select("mode").eq("session_id", requested_session_id).limit(1).maybe_single().execute()
                    session = session_response.data if session_response else None
                    # reset unsaved_file_context
                    unsaved_file_context = UnsavedFileContext(has_unsaved_file_context= False, file_id = None)
                    # Then handle the None case
                    if not session:
                        logger.info("No session exists...")
                        # no session exists, assign normal mode and set is new session to true
                        current_mode = "normal"  # or handle appropriately
                        is_new_session = True
                    else:
                        logger.info("Session already exists...")
                        current_mode = session.get("mode") or "normal"
                        is_new_session = False
                    # set the active agent
                    active_agent = agent_module.get_agent(session_model_key) if current_mode == "normal" else story_agent
                    logger.info(f"Session mode: {current_mode}")
                    
                    files_response = files_response.data
                    combined_file_content = ""
                    files_by_message = defaultdict(list)
                    for f in (files_response or []):
                        f_name = f.get("file_name")
                        f_content = f.get("file_content")
                        if f_name and f_content:
                            combined_file_content += f"\n\n --- File Name: {f_name} ---\n Content: {f_content}"
                        files_by_message[f["message_id"]].append({
                            "attachmentType": f.get("file_type", ""),
                            "attachmentName": f_name
                        })

                    session_file_context[session_id] = combined_file_content
                    for msg in chat_history:
                        msg["attachments"] = files_by_message.get(msg["message_id"], [])
                    # have to see what is being assigned to conversation history because chat history also contains other irrelevant fields
                    conversation_history = chat_history
                    # add a print here
                    # print("Conversation history", conversation_history)
                    # have to review logic here, the exception blocks
                    try:
                        await ws_send(websocket,{
                            "type": "get_chat", 
                            "status": "acknowledged",
                            "session_id": session_id, 
                            "chat_history": chat_history,
                            "mode": current_mode
                        })
                    except Exception as e:
                        logger.error(f"Some error occured while processing chat session history,please try again, Error: {e}")
                        if await dismiss_user_request(websocket, "get_chat", "Some error occured while fetching chat session. Please try again", "get_chat_failed"):
                            break
                        continue
                    
                    if chat_history:
                        last_msg = chat_history[-1]
                        # the idea is that an assistant message can't be saved before a user message, so if the last mesasge is a user message, its assistant response is not present for sure.
                        if last_msg.get("role") == "user":

                            # what if a user message which is not certainly the last mesasge does not have a corresponding assistant response - have to see whether it's possible or not
                            # a user message exists with no corresponding assistant response
                            # have to review logic here

                            # session_agent[requested_session_id] => True when "user_message" block runs

                            # we are currently in the `get_chat` block, how can session_agent[requested_session_id] => True when `get_chat` block hasn't completed execution
                            
                            orphan_user_message_id = last_msg.get("message_id")
                            # Agent not running and no response saved — signal frontend
                            logger.info(f"🔄 No response and no agent running — signaling frontend to regenerate")
                            try:
                                await ws_send(websocket, {
                                    "type": "regenerate_required",
                                    "message_id": orphan_user_message_id,
                                    "content": last_msg.get("content", ""),
                                }, label="regenerate_required")
                            except Exception as e:
                                logger.info("Some error occured while sending regenerate", e)
                                if await dismiss_user_request(websocket, "get_chat", "Some error occured while fetching chat session. Please try again", "get_chat_failed"):
                                    break
                                continue
                except Exception as e:
                    logger.error(f"Some error occured while processing chat: {e}")
                    # send a not-acknowledged message to frontend
                    # error would be shown to the user
                    if await dismiss_user_request(websocket, "get_chat", "Some error occured while fetching chat session. Please try again", "get_chat_failed"):
                        break
                    continue
                
                continue

            # Handle DELETE SESSION request
            if data.get("type") == "delete_session":
                try:
                    session_id_to_delete = data.get("session_id", "")
                    if not session_id_to_delete or not user_id:
                        logger.info("Missing required data: Session ID or User ID")
                        if await dismiss_user_request(websocket, f"delete_session_{session_id_to_delete}", "Some error occurred while deleting session.", "session_delete_failed_response"):
                            break
                        continue

                    success = await delete_user_session(user_id, session_id_to_delete)
                    if success:
                        await ws_send(websocket, {
                            "type": f"delete_session_{session_id_to_delete}",
                            "status": "acknowledged",
                            "session_id": session_id_to_delete
                        })
                    else:
                        if await dismiss_user_request(websocket, f"delete_session_{session_id_to_delete}", "Some error occurred while deleting session.", "session_delete_failed_response"):
                            break
                
                except Exception as e:
                    logger.error(f"Error deleting session: {e}")
                    if await dismiss_user_request(websocket, f"delete_session_{session_id_to_delete}", "Some error occurred while deleting session.", "session_delete_failed_response"):
                        break
                continue 

            # Handle DELETE ALL SESSIONS request
            # have to review, maybe it has to go
            if data.get("type") == "delete_all_sessions":
                try:
                    success = await delete_all_user_sessions(user_id)
                    if success:
                        await ws_send(websocket, {
                        "type": "delete_all_sessions",
                        "status": "acknowledged"})
                    else:
                        if await dismiss_user_request(websocket, "delete_all_sessions", "Some error occured while deleting all sessions. Please try again.", "all_sessions_delete_failed_response"):
                            break
                        continue
                except Exception as e:
                    logger.error(f"Some error occured while deleting all sessions, Error: {e}")
                    if await dismiss_user_request(websocket, "delete_all_sessions", "Some error occured while deleting all sessions. Please try again.", "all_sessions_delete_failed_response"):
                            break
                continue

            # ============================= MODEL SELECTION HANDLER =============================
            # this might have to go
            if data.get("type") == "model-selection":
                requested_model = data.get("model")
                
                is_valid = (requested_model in agent_module.SUPPORTED_CHAT_MODELS or 
                            requested_model in agent_module.SUPPORTED_CHAT_MODELS.values())

                if is_valid:
                    session_model_key = requested_model
                    
                    display_name = requested_model
                    if requested_model in agent_module.SUPPORTED_CHAT_MODELS:
                        display_name = requested_model 
                        logger.info("Model Name: ",display_name)
                    
                    if current_agent_name == "QuranTadabburAgent":
                        print(f"🔄 Hot-swapping Main Agent to model: {session_model_key}")
                        active_agent = agent_module.get_agent(session_model_key)
                    else:
                        print(f"⚠️ Model pref saved as {session_model_key}, but not applied immediately because user is in {current_agent_name} mode.")
                    
                    try:
                        await ws_send(websocket, {
                        "type": "model-selection",
                        "status": "acknowledged",
                        "model": requested_model,
                        "display_name": display_name
                    })
                    except WSDisconnectedError:
                        logger.error("Failed to send model-selection acknowledgment (Socket closed?)")
                        break
                    
                    try:
                        await ws_send(websocket, {
                        "type": "loading_message",
                        "content": f"Switched to **{display_name}**"
                    })
                    except WSDisconnectedError:
                        logger.error("Failed to send loading message after model selection (Socket closed?)")
                        break
                    
                    logger.info(f"Model preference updated to: {display_name}")
                
                else:
                    try:
                        await ws_send(websocket, {
                        "type": "model-selection",
                        "status": "not-acknowledged",
                        "model": requested_model,
                        "error": "This model is not supported.",
                        "available": list(agent_module.SUPPORTED_CHAT_MODELS.keys())
                    })
                    except WSDisconnectedError:
                        logger.error("Failed to send model-selection error response (Socket closed?)")
                        break
                continue   
            

            if data.get("type") == "undo-report":
                try:
                    message_id = data.get("message_id")
                    if not message_id: 
                        logger.info(""" **Can't reverse report - missing data:**
                        1. Message ID
                        """)
                        if await dismiss_user_request(websocket, f"undo-report-{message_id}", "Some error occured while reporting message. Please try again.", "revert_report_failed"):
                            break
                        continue
                    # delete hard rule in a different thread for optimization
                    # have to review the thread logic here
                    await db_retry(
                        lambda: supabase_client.table('chat_rules').delete().eq("message_id", message_id).execute(), label = "revert-report"
                    )
                    logger.info("✅ Reverted report successfully!")
                    await ws_send(websocket, {
                        "type": f"undo-report-{message_id}",
                        "status": "acknowledged",
                        "message_id": message_id,
                    }, label="undo_report_acknowledged")
                except Exception as e:
                    logger.info(f"Some error occured while reverting report, Error: {e}")
                    if await dismiss_user_request(websocket, f"undo-report-{message_id}", "Some error occured while reporting message. Please try again.", "revert_report_failed"):
                        break 
                continue


            if data.get("type") == "report":
                try:
                    message_id = data.get("message_id", "")
                    feedback = data.get("feedback", "")
                    reported_assistant_message = next(
                    (msg for msg in conversation_history if msg["id"] == message_id),
                    None
                    )
                    if not message_id or not feedback or not reported_assistant_message:
                        logger.info(""" 
                            **Can't report message - missing required data:**
                            1. Message ID
                            2. Feedback
                            3. Assistant Message to be reported.
                        """)
                        if await dismiss_user_request(websocket, f"report-{message_id}", "Some error occured while reporting message. Please try again.", "report_failed"):
                            break
                        continue
                    # insert hard rule in a different thread for optimization
                    response = await asyncio.to_thread(insert_report_rule, supabase_client, message_id, feedback, user_id)
                    if response:
                        await ws_send(websocket, response, label="report_acknowledged")
                        continue
                    else:
                        if await dismiss_user_request(websocket, f"report-{message_id}", "Some error occured while reporting message. Please try again.", "report_failed"):
                            break
                        continue
                                
                except Exception as e:
                    logger.info(f"Some error occured while reporting the message, Error: {e}")    
                    if await dismiss_user_request(websocket, "report", "Some error occured while reporting message. Please try again.", "report_failed"):
                        break
                    continue
                
            if data.get("type") in ["liked", "disliked"]:
                try:
                    feedback_type  = data.get("type")
                    message_id = data.get('message_id')
                    user_message_id = data.get("user_message_id")
                    message = data.get("message")
                    if not message_id or not message or not user_id or not user_message_id:
                        logger.info("""
                        **Can't proceed - missing required data:
                        1. Message ID
                        2. User Message ID
                        3. User ID
                        4. Message
                        **
                        """)
                        if await dismiss_user_request(websocket, f"feedback-{user_message_id}-{message_id}-{feedback_type}", "Some error ocurred while submitting feedback. Please try again.", "feedback_submission_failed"):
                            break
                        continue
                    await asyncio.to_thread(handle_feedback, feedback_type , message, message_id, user_id)
                    
                    await ws_send(websocket, {
                        "type": f"feedback-{user_message_id}-{message_id}-{feedback_type}",
                        "status": "acknowledged",
                        "message_id": message_id,
                        "reply_to_message_id": user_message_id,
                        "feedback_type": feedback_type
                    }, label = "feedback_submission_acknowledgement")
                    continue
                except Exception as e:
                    logger.info(f"Some error occured while submitting feedback, Error: {e}")
                    if await dismiss_user_request(websocket, f"feedback-{user_message_id}-{message_id}-{feedback_type}", "Some error ocurred while submitting feedback. Please try again.", "feedback_submission_failed"):
                        break
                    continue
                
            # === MAIN CHAT MESSAGE ===
            if data.get("type") == "user_message":
                try:
                    
                    user_message_id = data.get("message_id")
                    role = data.get("role", "user")
                    additional_instructions = data.get("system_instructions")
                    message = data.get("content", "")
                    resend_flag = data.get("resend_flag")
                    resend_message_id = data.get("resend_message_id")
                    new_file_text = data.get("new_file_context")

                    # initialize a flag to deterime whether user message has been saved or not
                    user_message_saved_to_db = False
                    assistant_message_saved_to_db = False
                    # have to handle unsaved_file_context for a scenario where user refreshes, goes to a new chat, or navigates to an older session. In that case unsaved_file_context gets lost.

                    # Remove the unused file context - if any, before proceeding
                    if unsaved_file_context.has_unsaved_file_context and unsaved_file_context.file_id:
                        file_id = unsaved_file_context.file_id 
                        try:
                            await db_retry(
                            lambda: supabase_client.table('session_files').delete().eq("file_id", file_id).execute(),
                            label="delete_session_file"
                            )
                            logger.info(f"Successfully Rolled back file {file_id} due to previous errors")
                            unsaved_file_context.has_unsaved_file_context = False
                            unsaved_file_context.file_id = None
                        except (DBRetryError, Exception) as e:
                            logger.info(f"Failed to rollback file: {e}")
                            if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                                break
                            continue
                            

                    user_message_id = (user_message_id if not resend_flag else resend_message_id) or generate_uuid()                
                    # generate a message id for response message
                    response_message_id = generate_uuid()
                    # add a check for uniqueness
                    while response_message_id in unique_message_ids:
                        response_message_id = generate_uuid()
                    unique_message_ids.append(response_message_id)
                    
                    if not resend_flag:
                        # add a check for uniqueness
                        while user_message_id in unique_message_ids:
                            user_message_id = generate_uuid()
                        unique_message_ids.append(user_message_id)

                    if not user_message_id or not response_message_id or not session_id:
                        logger.info("""
                            **Missing required data - cannot proceed:**
                            1. User Message ID
                            2. Response Message ID  
                            3. Session ID
                        """)
                        if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                            break
                        # have to send an error message to frontend from here
                        continue
                    
                    if not resend_flag:
                        try:
                            existing_response = supabase_client.table('chat_messages')\
                                .select('message_id', 'content', 'has_verse_audio', 'has_verse_image', 
                                        'audio_data', 'verse_images', 'story_data')\
                                .eq('reply_to_message_id', user_message_id)\
                                .eq('role', 'assistant')\
                                .eq('session_id', session_id)\
                                .order('created_at', desc=True).limit(1).execute()
                            existing_response_data = existing_response.data
                            if existing_response_data and len(existing_response_data) > 0:
                                existing_msg = existing_response_data[0]
                                logger.info(f"⚠️ Response already exists for message {user_message_id}, returning cached response")
                                try:
                                    await ws_send(websocket, {
                                        "type": "assistance_response",
                                        "status": "acknowledged",
                                        "message_id": existing_msg['message_id'],
                                        "content": {
                                            "response": existing_msg['content'],
                                            "has_verse_audio": existing_msg.get('has_verse_audio') or False,
                                            "has_verse_image": existing_msg.get('has_verse_image') or False,
                                            "audio_data": existing_msg.get('audio_data') or [],
                                            "verse_images": existing_msg.get('verse_images') or [],
                                            "story_segments": existing_msg.get('story_data') or [],
                                            "is_error": existing_msg.get('is_error') or False
                                        },
                                        "reply_to_message_id": user_message_id,
                                        "resend_flag": False,
                                        "final": True,
                                    }, label="assistance_response_cached")
                                    continue
                                except WSDisconnectedError:
                                    logger.info("Websocket Disconnected, can't proceed")
                                    # have to see what break means here
                                    break
                                except Exception:
                                    logger.info("Some error occured while sending payload, can't proceed")
                                    # it should be raised because some error has occured while sending assistant response meanwhile its continue
                                    if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                                        break
                                    continue
                        except Exception as e:
                            logger.warning(f"⚠️ Could not check for existing response: {e}, proceeding with agent call")        
                        
                    message_string = message + (f"\n\n {additional_instructions}" if (resend_flag and additional_instructions) else "")
                    # the user messages that are resent won't be saved
                    if not resend_flag:
                        try:
                            # insert user's message 
                            await db_retry(
                                lambda:supabase_client.table('chat_messages').upsert({
                                    "message_id": user_message_id,
                                    "user_id": user_id, 
                                    "session_id": session_id,
                                    "role": role,
                                    "content": message_string,
                                }, on_conflict="message_id").execute(),
                                label="insert_user_message"
                            )
                            logger.info("✅ User message saved successfully!")
                            user_message_saved_to_db = True
                        except (DBRetryError, Exception) as e:
                            logger.error(f"❌ Failed to save user message: {e}")
                            # don't delete session even if new, just add a check and fetch only those sessions with a title and description while fetching sessions
                            if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                                break
                            continue

                    # raise Exception("Some error occured while processing assistant message!")
                    if not resend_flag:
                        file_name = data.get("file_name")
                        file_type = data.get("file_type")
                        file_saved_in_db = False
                        new_file_id = None
                        if file_name and file_type and new_file_text:                       
                            # Save files, contexts in database, both save operations should be atomic, if one fails the other too, later wrap inside a function and call here
                            try:
                                new_file_id = generate_uuid()
                                await db_retry(
                                    lambda: supabase_client.table('session_files').insert({    
                                        "file_id": new_file_id,
                                        "file_name": file_name,
                                        "file_type": file_type,
                                        "file_content": new_file_text, 
                                        "message_id": user_message_id,
                                        "session_id": session_id,
                                        "user_id": user_id
                                    }).execute(),
                                    label="insert_session_file"
                                )
                                logger.info(f"✅ File record '{file_name}' saved to session_files")
                                # set the file save flag to true
                                file_saved_in_db = True
                                logger.info(f"💾 Committing new file context to session {session_id}")
                                existing_context = session_file_context.get(session_id) or ""
                                updated_context = existing_context + "\n\n--- FILE CONTENT ---\n" + new_file_text
                                session_file_context[session_id] = updated_context
                                await db_retry(
                                    lambda: supabase_client.table('chat_sessions').update({
                                        'file_context': updated_context,
                                    }).eq('session_id', session_id).execute(),
                                    label="save_file_context"
                                )

                                # Both db operations successfull, safely build the message string here.
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
                                
                            except (DBRetryError, Exception) as e:
                                logger.error(f"❌ Failed to upload file: {e}")
                                # as operations are atomic, check file_saved_in_db flag to ensure atmoicity
                                # roll back if saved already
                                if file_saved_in_db and new_file_id:
                                    # if file present, then delete it
                                    try:
                                        await db_retry(
                                        lambda: supabase_client.table('session_files').delete().eq("file_id", new_file_id).execute(),
                                        label="delete_session_file"
                                        )
                                        logger.info(f"Rolled back file {new_file_id} due to error")
                                    except (DBRetryError, Exception) as rollback_error:
                                        logger.info(f"Failed to rollback file: {rollback_error}")
                                        # set the unsaved_file_context flag
                                        unsaved_file_context.has_unsaved_file_context = True
                                        unsaved_file_context.file_id = new_file_id
                                
                                if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                                    break
                                continue

                    logger.info(f"[{current_agent_name}] Session: {session_id} | Message: {message_string} ...")
                    # File Feature - Check current session first, then fallback to default_session

                    # Prepare messages
                    base_messages = (
                        [{"role": "system", "content": dynamic_system_instruction["text"]}]
                        if dynamic_system_instruction["text"] else []
                    )
                    
                    # append user message to conversation history
                    conversation_history.append({"role": "user", "content": message_string, "id": user_message_id})

                    messages = base_messages + conversation_history     
                    agent_response = None
                    session_agent_running[session_id] = True
                    try:
                        for attempt in range(3):
                            try:
                                # have to add user language here too
                                context = agent_module.UserContext(
                                    user_name=user_name,
                                    user_age=user_age,
                                    user_id=user_id,
                                    session_id=session_id
                                )
                                agent_response = await run_agent_with_progress(
                                    active_agent,
                                    messages,
                                    context,
                                    websocket
                                )
                                break
                            except Exception as e: 
                                logger.warning(f"⚠️ Agent invoke attempt {attempt+1}/3 failed: {e}")
                                if attempt < 2:
                                    await asyncio.sleep(1.5)
                                else:
                                    raise RuntimeError(f"Agent failed after 3 attempts: {e}")
                            # break early if disconnected
                            except WSDisconnectedError:
                                logger.info("Websocket disconnected, can't proceed.")
                                break
                    finally:
                        session_agent_running.pop(session_id, None) 

                    messages_array = (agent_response.get('messages') or []) if agent_response else []

                    logger.info(f"messages_array length: {len(messages_array)}")
                    logger.info(f"messages_array types: {[type(m).__name__ for m in messages_array]}")

                    # initialize a response object
                    response_object = None
                    ai_response = None
                    if active_agent.name == "QuranTadabburAgent":
                        # Create a new instance of OutputSchema
                        response_object = NormalOutputSchema(
                            response=messages_array[-1].content or "",
                            has_verse_audio=False,
                            has_verse_image=False,
                            # by default audio_data and verse_images are an empty list so no need to initialize explicitly
                        )

                        # Assign ai response to the response field
                        ai_response = response_object.response
                        # initialize a data array for flags
                        data_flag = [False, False]
                        for message in reversed(messages_array):
                            if data_flag == [True, True]:
                                break
                            if isinstance(message, ToolMessage):
                                if message.name == "get_verse_image" and not data_flag[0]:
                                    data = json.loads(message.content)
                                    verse_images = data.get("verse_images",[]) 
                                    if verse_images:
                                        response_object.has_verse_image = True
                                        response_object.verse_images = [
                                        SurahForImage.model_validate(v) for v in verse_images
                                        ]
                                    data_flag[0] = True
                                elif message.name == "get_Quran_Audio" and not data_flag[1]:
                                    data = json.loads(message.content)
                                    audio_data = data.get("audio_data", [])
                                    if audio_data:
                                        response_object.has_verse_audio = True
                                        response_object.audio_data = [SurahForAudio.model_validate(v) for v in audio_data]
                                    data_flag[1] = True

                        tool_calls_made = [m for m in messages_array if isinstance(m, ToolMessage)]
                        def is_tool_result_empty(tool_message: ToolMessage) -> bool:
                            try:
                                content = json.loads(tool_message.content) if isinstance(tool_message.content, str) else tool_message.content
                                # Handle searchAsbabNuzul structure: {'results': [{'points': [...]}]}
                                if 'results' in content:
                                    for result in content.get('results', []):
                                        points = result.get('points', [])
                                        if points: 
                                            return False
                                    return True 
                                if 'audio_data' in content:
                                    return not content.get('audio_data')
                                if 'verse_images' in content:
                                    return not content.get('verse_images')
                                return False  # unknown structure, don't skip
                            except Exception:
                                return False  # parse error, don't skip

                        all_tools_empty = bool(tool_calls_made) and all(
                            is_tool_result_empty(m) for m in tool_calls_made
                        )

                        if all_tools_empty:
                            logger.warning(f"⚠️ All tool calls returned empty results — skipping DB save")
                            try:
                                await ws_send(websocket, {
                                    "type": "assistance_response",
                                    "status": "acknowledged",
                                    "message_id": response_message_id,
                                    "content": response_object.model_dump(mode="json"),
                                    "resend_flag": resend_flag,
                                    "reply_to_message_id": user_message_id,
                                    "final": True,
                                }, label="assistance_response")
                            except WSDisconnectedError:
                                logger.info("Socket closed before sending empty-tool response")
                                break
                            except Exception:
                                # critical error, close websocket, break out
                                logger.info("☣️ Critical error, closing websocket...")
                                await websocket.close()
                                break
                            continue  
                        try:
                            await db_retry(
                                lambda:supabase_client.table('chat_messages').insert({
                                    "message_id": response_message_id,
                                    "session_id": session_id,
                                    "user_id": user_id,
                                    "role": "assistant",
                                    "content": ai_response,
                                    "reply_to_message_id": user_message_id,
                                    "has_verse_audio": response_object.has_verse_audio,
                                    "audio_data": [surah.model_dump() for surah in response_object.audio_data],
                                    "has_verse_image": response_object.has_verse_image,
                                    "verse_images": [surah.model_dump() for surah in response_object.verse_images]
                                }).execute(),
                                label="insert_assistant_message"
                            )
                            print("✅ Assistant message saved successfully!")
                            assistant_message_saved_to_db = True
                        except (DBRetryError, Exception) as e:
                            logger.error(f"❌ Some error occured while saving assistant message: {e}")
                            raise
                    elif active_agent == story_agent:
                        response_object = StoryOutputSchema(
                            response = messages_array[-1].content or ""
                        )
                        ai_response = response_object.response                   
                        data_flag = False
                        for message in reversed(messages_array):
                            if data_flag:
                                break
                            if isinstance(message, ToolMessage):
                                if message.name == "generate_ai_images_story":
                                    try:
                                        data = json.loads(message.content)
                                        story_dicts = data.get("story_data") or []         

                                        story_data: List[StoryParagraph] = []
                                        # Only process if it's a list of dicts
                                        if isinstance(story_dicts, list):
                                            story_data = [
                                                StoryParagraph(**item) 
                                                for item in story_dicts 
                                                if isinstance(item, dict)  # Filter out non-dict items
                                            ]
                                        else:
                                            logger.warning(f"Expected list for story_data, got {type(story_dicts)}")
                                            continue
                                        response_object.story_segments = story_data
                                        data_flag = True
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Invalid JSON in tool message: {e}")
                                        # shouldn't continue, raise error
                                        raise
                                    except Exception as e:  
                                        logger.error(f"Unexpected error parsing tool message: {e}")
                                        # shouldn't continue, raise error
                                        raise
                        try:
                            await db_retry(
                                lambda:supabase_client.table('chat_messages').insert({
                                    "message_id": response_message_id,
                                    "session_id": session_id,
                                    "user_id": user_id,
                                    "role": "assistant",
                                    "content": ai_response,
                                    "reply_to_message_id": user_message_id,
                                    "story_data": [segment.model_dump() for segment in response_object.story_segments],
                                }).execute(),
                                label="insert_assistant_message"
                            )
                            print("✅ Assistant message saved successfully!")
                            assistant_message_saved_to_db = True
                        except (DBRetryError, Exception) as e:
                            logger.error(f"❌ Some error occured while saving assistant message: {e}")
                            raise                  
                    else:
                        ai_response = ""
                

                    # append assistant message to conversation history
                    conversation_history.append({"role": "assistant", "content": ai_response , "id": response_message_id, "reply_to_message_id": user_message_id})
                    if is_new_session:
                        try:
                            logger.info(f"📝 First message detected. Persisting session {session_id} to DB. Generating title description")
                            await db_retry(
                                lambda: supabase_client.table("chat_sessions").insert({
                                    'session_id': session_id,
                                    'user_id': user_id,
                                    'mode': current_mode
                                }).execute(),
                                label="create_session"
                            )
                            is_new_session = False   
                            # generate title and description for the current chat history if there are 2 user/assistant messages each
                            # run the below logic in a seperate thread
                            if conversation_history and (len(conversation_history) == 2):  
                                await asyncio.to_thread(
                                    generate_title_description,
                                    conversation_history,
                                    session_id,
                                    supabase_client
                                ) 
                        except (DBRetryError, Exception):
                            logger.info(f"Some error occured while persisting session or generating title and description, can't proceed, Error: {e}")
                            if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                                break
                            continue
                    
                    send_result = await ws_send(websocket, {
                        "type": "assistance_response",
                        "status": "acknowledged",
                        "message_id": response_message_id,
                        "content": response_object.model_dump(mode = "json") if response_object else "No response from server",
                        "resend_flag": resend_flag,
                        "reply_to_message_id": user_message_id,
                        "db_saved" :True,
                        "final": True
                    }, label="assistance_response")

                    if not send_result:
                        # WebSocket was disconnected, message saved in DB will be loaded via get_chat
                        logger.info("⚠️ Assistance response saved but not sent (client disconnected). Will be retrieved once connection re-establishes.")
                        if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                            break
                        continue
                        
                except (WebSocketDisconnect, WSDisconnectedError):
                    logger.info("Client disconnected, closing websocket")
                    break
                except Exception as e:
                    logger.error(f"Error during agent execution: {e}")
                    if response_message_id:
                        # fetch older response if saved
                        try:
                            response_data = await db_retry(
                                lambda: supabase_client.table('chat_messages').select('role', 'content', 'reply_to_message_id', 'feedback', 'audio_url', 'has_verse_audio', 'audio_data', 'has_verse_image', 'verse_images', 'is_error','story_data').eq("role", "assistant").eq("message_id", response_message_id).limit(1).maybe_single().execute(), label = "get_saved_assistant_response"
                            )
                            saved_assistant_response = response_data.data if response_data else None
                            if saved_assistant_response and 'content' in saved_assistant_response:
                                saved_assistant_response['response'] = saved_assistant_response.pop('content')    
                                await ws_send(websocket, {
                                    "type": "assistance_response",
                                    "status": "acknowledged",
                                    "message_id": response_message_id,
                                    "content": saved_assistant_response,
                                    "resend_flag": resend_flag,
                                    "reply_to_message_id": user_message_id,
                                    "db_saved": True,
                                    "final": True,
                                    "is_error": False
                                }, label="assistant_response")
                                continue
                        except WSDisconnectedError:
                            break
                        except Exception as e:
                            logger.info(f"Some error occured while sending saved assistant response, Error: {e}")
                            logger.info(f"User message saved to db: {user_message_saved_to_db}")
                            await cleanup_on_error(websocket, user_message_saved_to_db, assistant_message_saved_to_db, user_message_id, response_message_id)
                            if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed", {"is_error": True}):
                                break
                            continue    
                    logger.info(f"User message saved to db: {user_message_saved_to_db}")
                    await cleanup_on_error(websocket, user_message_saved_to_db, assistant_message_saved_to_db, user_message_id, response_message_id)
                    if await dismiss_user_request(websocket, "assistance_response", "Some error occured while generating response. Please try again.", "assistance_response_failed"):
                        break
                    continue
                    
                continue
                                 
    except WebSocketDisconnect:
        logger.info(f"WebSocket closed for user {user_id}")

    except RuntimeError as e:
        if "websocket.close" in str(e) or "response already completed" in str(e):
            logger.info(f"WebSocket disconnected during send operation for user {user_id}")
        else:
            logger.exception("RuntimeError in WebSocket")
            await safe_close_websocket(websocket)

    except Exception as e:
        logger.exception("WebSocket error")
        await safe_close_websocket(websocket)
        

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv("APP_ENV", "production"),
    }


# ------------------- APP RUNNER -------------------


# if __name__ == "__main__":
#     import uvicorn
#     # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
#     uvicorn.run("main:app", host="0.0.0.0", port=8000)