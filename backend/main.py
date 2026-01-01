import os
import json
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
# from supabase import create_client, Client  # type: ignore
# from supabase.client import ClientOptions  # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Any, Any, List, Optional
import asyncio # --- ADDED: Required for background tasks
from langchain_core.messages import HumanMessage, AIMessage
from agents import Runner
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from title_agent import title_agent
import agent as agent_module
import story_agent as story_module
import logging
import secrets 
import random
import string
from agents import ItemHelpers  # used to extract message text from items (STREAMING)
load_dotenv()
from data.data import comprehensive_surah_metadata
# --- IMPORT NEW STT CLASS ---
# from speech_to_text import SpeechToTextEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TADABBUR_PROJECT_URL = os.getenv('TADABBUR_PROJECT_URL')
TADABBUR_API_KEY = os.getenv('TADABBUR_API_KEY')

# ------------------- APP CONFIG -------------------
app = FastAPI(title="Tadabbur Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


API_KEY = os.getenv("CHAT_API_KEY")
# ------------------- OPTIONAL HTTP ENDPOINT -------------------
# === SESSION CODE START ===
DB_PATH = "chat.db"



def generate_short_id() -> str:
    # This is the closest equivalent to Math.random().toString(36)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

def generate_session_id() -> str:
    """Generate unique session ID: sess_ + 12 hex chars"""
    return f"sess_{secrets.token_hex(6)}"


# def ensure_db_exists():
#     """Force creation of sessions.db file"""
#     db_file = Path(DB_PATH)
#     if not db_file.exists():
#         temp_id = generate_session_id()
#         temp_session = SQLiteSession(temp_id, DB_PATH)


# ensure_db_exists()



def get_chat_messages(session_id: str, supabase_client) -> List[str]:
    """Get all messages of a specific session"""
    if not session_id:
        return []
    chat_messages = supabase_client.table('chat_messages').select('message_id','role','message').order('created_at').eq('session_id', session_id).execute().data
    chat_messages = [
    {'role': msg['role'], 'content': msg['message']}
    for msg in chat_messages
    ]
    return chat_messages


def get_message_ids(session_id: str, supabase_client) -> list[str | None]:
    """Get all message IDs for a specific session"""
    if not session_id:
        return []

    message_ids = supabase_client.table('chat_messages').select('message_id').order('created_at').eq('session_id', session_id).execute().data
    print(f"All message IDs for session {session_id}, {message_ids}")
    return message_ids

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


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected successfully")

    # try:
    #     print("Connecting to Database for saving user messages")
    #     supabase_client: Client = create_client(
    #         TADABBUR_PROJECT_URL,
    #         TADABBUR_API_KEY,
    #         options=ClientOptions(
    #             postgrest_client_timeout=10,
    #             storage_client_timeout=10,
    #             schema="public",
    #         )
    #     )
    #     print("✅ Supabase Client connected successfully!")
    # except Exception as e:
    #     print("Some error occured while connecting to supabase", e)

    # initialize the conversation history and message_IDs set
    conversation_history = []
    unique_message_ids = set()
    # STT State
    # stt_engine: Optional[SpeechToTextEngine] = None
    # stt_task: Optional[asyncio.Task] = None

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
            # if "bytes" in message and message["bytes"]:
            #     if stt_engine: # Only feed if we started the mic
            #         await stt_engine.process_audio(message["bytes"])
            #     continue
            # -----------------------------------------------------------------

            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue
                # --- ADDED: LIFECYCLE MANAGEMENT FOR STT ---
                # creates a engine every time 'start_mic' is sent
               
                # if data.get("type") == "start_mic":
                #     logger.info("🎙️ Received Start Mic command")
                #     # 1. Cleanup old if exists
                #     if stt_engine:
                #         await stt_engine.stop()
                #         print("Cancelling task")
                #         if stt_task: stt_task.cancel()
                   
                #     # 2. Start FRESH engine
                #     # stt_engine = SpeechToTextEngine()
                #     await stt_engine.start()
                   
                #     # 3. Start Streaming Task for THIS engine
                #     async def stream_stt():
                #         try:
                #             # unpack text AND is_final flag
                #             async for text, is_final in stt_engine.get_text_stream():
                #                 response_type = "stt_final" if is_final else "stt_chunk"
                #                 await websocket.send_json({"type": response_type, "text": text})
                #         except Exception:
                #             pass
                #     stt_task = asyncio.create_task(stream_stt())
                #     continue


                # if data.get("type") == "stop_mic":
                #     logger.info("🛑 Received Stop Mic command")
                #     # Stop engine to clear buffers
                #     if stt_engine:
                #         await stt_engine.stop()
                #         stt_engine = None
                #     if stt_task:
                #         stt_task.cancel()
                #         stt_task = None
                #     continue


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
                # add a record in chat_sessions table
                # try:    
                #     print("🔃 Creating a new session record")
                #     supabase_client.table("chat_sessions").insert({'session_id': session_id, "title": "Chat Title", "description":"Description for the chat session" }).execute()
                #     # reset the conversation history and unique message ids
                #     conversation_history = []
                #     unique_message_ids.clear()
                #     print("✅ Successfully created a new session record!")
                # except Exception as e:
                #     print("Some error occured while adding a new session record", e)

                # Send confirmation — this unblocks frontend
                await websocket.send_json({
                    "type": "session_id",
                    "status": "acknowledged",
                    "session_id": session_id,
                    "current_agent": current_agent_name,
                    "current_model": session_model_key
                })
                continue  

            # Handle CHAT HISTORY request
            # if data.get("type") == "chat_history":
            #     try:
            #         chat_sessions = supabase_client.table('chat_sessions').select('session_id', 'title', 'description', 'created_at').execute().data
            #         print("All sessions", chat_sessions)
            #         await websocket.send_json({
            #             "type": "chat_history",
            #             "status":"acknowledged",
            #             "chat_history": chat_sessions
            #         })
            #         logger.info(f"Sent {len(chat_sessions)} sessions to frontend")
            #     except Exception as e:
            #         logger.error(f"Error fetching chat history: {e}")

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
                # try:
                #     # switch to this session
                #     session_id = requested_session_id
                #     print(f"🔃 Retrieving messages for chat with session-id {session_id}")
                #     # get chat messages
                #     chat_history = get_chat_messages(session_id, supabase_client)
                #     # get message ids for this session
                #     message_ids = get_message_ids(session_id, supabase_client)
                #     unique_message_ids = set(message_ids)
                #     # override conversation_history with new_chat_history
                #     conversation_history = chat_history or []
                #     await websocket.send_json({
                #         "type": "get_chat",
                #         "status": "acknowledged",
                #         "session_id": session_id,
                #         "chat_history": chat_history
                #     })
                #     logger.info(f"Loaded chat: {session_id} with {len(chat_history)} messages")
                # except Exception as e:
                #     logger.error(f"Error loading chat: {e}")
                #     await websocket.send_json({
                #         "type": "get_chat",
                #         "status": "non-acknowledged",
                #         "session_id": requested_session_id,
                #         "error": str(e)
                #     })
                # continue

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

            # if data.get("type") == "like" or "dislike" or "report":
            #     type = data.get("type")
            #     session_id = data.get('session_id')
            #     message_id = data.get('message_id')
            #     if not session_id or message_id:
            #         continue
            #     try:
            #         print("Submitting user feedback")
            #         supabase_client.table("chat_messages").update({"feedback": type}).eq("session_id", session_id).eq("message_id", message_id).execute()
            #         print("✅ Successfully submitted user feedback!")
            #     except Exception as e:
            #         print("Failed to submit user feedback")
            #     # the main system injection flow here
                
            #     # Fetch the user prompt for the above assistant response
            #     try:
            #         supabase_client.table('chat_messages').select("")
            #     except Exception as e:
            #         print("Failed to fetch the user prompt for the assistant response", e)
            #     continue
            # Handle verse request
            if data.get("type") == "verse_request":
                surah = data.get("surah")
                ayah = data.get("ayah")
                arabic_edition = data.get("arabic_edition", "quran-uthmani")
                translation_edition = data.get("translation_edition", "en.sahih")
                include_audio = data.get("include_audio", False)

                from tools.verse_reader import _fetch_verse_data
                verse_data = await _fetch_verse_data(surah, ayah, arabic_edition, translation_edition, include_audio)

                await websocket.send_json({
                    "type": "verse_response",
                    "status": "success",
                    "data": verse_data
                })
                continue

            # === MAIN CHAT MESSAGE ===

            if data.get("type") == "user_message":
                role = data.get("role", "user")
                message = data.get("content", "")
                message_id = data.get("message_id")
                
                print("New message received", message)
                if message_id:
                    unique_message_ids.add(message_id)
                else:
                    message_id = generate_short_id()
                    while message_id in unique_message_ids:
                        message_id = generate_short_id()
                    unique_message_ids.add(message_id)
                # save user message in db
                # try:
                #     supabase_client.table('chat_messages').insert({
                #         "message_id": message_id,
                #         "session_id": session_id,
                #         "role": role,
                #         "message": message,
                #     }).execute()
                #     print("✅ User message saved successfully!")
                # except Exception as e:
                #     print("Some error occured while inserting user messages", e)

                logger.info(f"[{current_agent_name}] Session: {session_id} | Message: {message} ...")
                try:
                    # append user message to conversation history
                    conversation_history.append(HumanMessage(message))
                    response = active_agent.invoke(
                        {"messages": conversation_history},
                    )
                    response = response['messages'][-1].content
                    # append assistant message to conversation history
                    conversation_history.append(AIMessage(response or ""))
                    # generate a message id for response message
                    response_message_id = generate_short_id()
                    while response_message_id in unique_message_ids:
                        response_message_id = generate_short_id()

                    unique_message_ids.add(response_message_id)

                    # try:
                    #     supabase_client.table('chat_messages').insert({
                    #         "message_id": response_message_id,
                    #         "session_id": session_id,
                    #         "role": "assistant",
                    #         "message": response or "",
                    #     }).execute()
                    #     print("✅ Assistant message saved successfully!")
                    # except Exception as e:
                    #     print("Some error occured while inserting assistant messages", e)

                    # generate title and description for the current chat history if there are 2 user/assistant messages each
                    # run the below logic in a seperate thread
                    if (len(conversation_history) == 2):
                        conversation_string = ""
                        # build a conversation string from user & assistant messages
                        for message in conversation_history:
                            if isinstance(message, HumanMessage):
                                conversation_string += f"User message: {message.content} \n"
                            else:
                                conversation_string += f"Assistant message: {message.content} \n"
                        if conversation_string:
                            try:
                                agent_response = title_agent.invoke(conversation_string)
                                title = agent_response.title or "Title"
                                description = agent_response.description or "Description of chat session"
                                # insert title and description in session table
                                # try:
                                #     print("🔃 Inserting title and description in session record")
                                #     supabase_client.table('chat_sessions').update({"title": title, "description": description}).eq("session_id", session_id).execute()
                                #     print("✅ Successfully insert title and description")
                                # except Exception as e:
                                #     print("Some error occured while inserting title and description in session table", e)
                            except Exception as e:
                                print("Some error occured while generating title and description", e)
                        else:
                            print("No conversation string so not generating title and description.")
                    # Check for audio in response
                    logging.info(f"[WS] Agent response (truncated): {response[:500]}...")
                    audio_data = extract_audio_data(response)
                    logging.info(f"[WS] Audio data extracted: {audio_data is not None}")

                    if audio_data:
                        logging.info("[WS] Detected audio request - opening dialog cleanly")

                        
                        await websocket.send_json({
                            "type": "audio_response",
                            "message_id": response_message_id,
                            "audio_url": audio_data["audio_url"],
                            "all_urls": audio_data["all_urls"],
                            "surah_name": audio_data["surah_name"],
                            "ayah_number": audio_data["ayah_number"],
                            "text_response": ""  
                        })

                        
                        clean_message = f"**Surah {audio_data['surah_name']}**"
                        if audio_data["ayah_number"]:
                            clean_message += f" - Ayah {audio_data['ayah_number']}"
                        
                        clean_message += "\n\n🎧 Recitation is playing in the audio player above."

                        await websocket.send_json({
                            "type": "assistance_response",
                            "message_id": response_message_id,
                            "content": clean_message,
                            "final": True
                        })

                       
                        verse_data = None

                    else:
                        logging.info("[WS] Sending assistance_response")
                        if response:
                            await websocket.send_json({
                                "type": "assistance_response",
                                "message_id": response_message_id,
                                "content": response,
                                "final": True
                            })
                    
                    # if audio_data:
                    #     logging.info("[WS] Sending audio_response")
                    #     await websocket.send_json({
                    #         "type": "audio_response",
                    #         "message_id": response_message_id,
                    #         "audio_url": audio_data["audio_url"],
                    #         "all_urls": audio_data["all_urls"],
                    #         "surah_name": audio_data["surah_name"],
                    #         "ayah_number": audio_data["ayah_number"],
                    #         "text_response": audio_data["full_response"]
                    #     })
                    # else:
                    #     logging.info("[WS] Sending assistance_response")

                    #     if response:
                    #         await websocket.send_json({
                    #             "type": "assistance_response",
                    #             "message_id": response_message_id,
                    #             "content": response,
                    #             "final": True
                    #         })

                    # Check for verse in response
                    # Check for verse in response
                    verse_data = extract_verse_data(response)
                    if verse_data:
                        logging.info("[WS] Vers - opening Quran Verse ")

                        # Dialog kholne ke liye
                        await websocket.send_json({
                            "type": "open_verse_dialog",
                            "parsed_request": {
                                "surah": verse_data["surah_number"],
                                "ayah": verse_data["ayah_number"]
                            },
                            "original_message": "Quran Verse",
                            "note": None  
                        })

                       
                        clean_msg = f"**سورہ {verse_data['surah_name']} - آیت {verse_data['ayah_number']}**"
                        clean_msg += "\n\nاوپر والے Quran Reader میں کھل گیا ہے – پڑھو، سنو، شیئر کرو!"

                        await websocket.send_json({
                            "type": "assistance_response",
                            "message_id": response_message_id,
                            "content": clean_msg,
                            "final": True
                        })

                    # audio_data = None
                    # verse_data = extract_verse_data(response)
                    # if verse_data:
                    #     logging.info("[WS] Sending open_verse_dialog")
                    #     await websocket.send_json({
                    #         "type": "open_verse_dialog",
                    #         "parsed_request": {"surah": verse_data["surah_number"], "ayah": verse_data["ayah_number"]},
                    #         "original_message": "Verse reading request",
                    #         "note": "Verse loaded successfully"
                    #     })


                    # === FINAL RESPONSE & CLEANUP ===
                    # await websocket.send_json({
                    #     "type": "assistance_response",
                    #     "content": final_text.strip() if final_text.strip() else "I'm not sure how to respond to that."
                    # })


                    await websocket.send_json({"type": "streaming_end"})
                    await websocket.send_json({"type": "run_complete"})


                except OutputGuardrailTripwireTriggered as e:
                    msg = getattr(e.guardrail_result, "output_info",
                                "Sorry, I can only respond within the context of the Quran and authentic Islamic sources.")


                    await websocket.send_json({
                        "type": "assistance_response",
                        "content": msg.strip()
                    })
                    await websocket.send_json({"type": "streaming_end"})
                    await websocket.send_json({"type": "run_complete"})


                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                    break


                except Exception as e:
                    logger.exception("Streaming error")
                    await websocket.send_json({"type": "assistance_response", "content": "Sorry, something went wrong."})
                    await websocket.send_json({"type": "streaming_end"})
                    await websocket.send_json({"type": "run_complete"})


    except WebSocketDisconnect:
        logger.info("WebSocket closed")

    except Exception as e:
        logger.exception("WebSocket error")
    # finally:
    #     # --- ADDED: CLEANUP STT ---
    #     if stt_engine:
    #         await stt_engine.stop()
    #         stt_task.cancel()
            # --------------------------


# ------------------- APP RUNNER -------------------


if __name__ == "__main__":
    import uvicorn
    # IMPORTANT: Run without --reload for Windows asyncio subprocess support
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) <-- REPLACED
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)