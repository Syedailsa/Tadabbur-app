import os
import json
import asyncio
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Any, Any, List, Optional
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
from utils.generate_uuid import generate_uuid
from utils.report_rule import insert_report_rule, delete_report_rule
import story_agent as story_module
import logging
import secrets
from config.db import get_supabase_client
from agents import ItemHelpers  # used to extract message text from items (STREAMING)
from data.data import comprehensive_surah_metadata
from tools.verse_reader import SURAH_METADATA
load_dotenv()
from data.data import comprehensive_surah_metadata
# --- IMPORT NEW STT CLASS ---
# from speech_to_text import SpeechToTextEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
supabase_client = None

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

    try:

        supabase_client = get_supabase_client()
    except Exception as e:
        print("Some error occured initiating supabase connection", e)

    # initialize the conversation history and message_IDs set
    conversation_history = []
    unique_message_ids = []
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
                ack_sent = False
                try:
                    variant = data.get("variant", "")
                    message_id = data.get("message_id", "")
                    feedback = data.get("feedback", "")
                    
                    if not variant or not message_id or not feedback:
                        print("No variant/message ID/feedback, can't proceed to report content")
                        await websocket.send_json({
                        "type": "report",
                        "status": "not-acknowledged"
                    })
                        ack_sent = True
                        continue

                    if variant == "custom":
                        reported_assistant_message = next(
                        (msg for msg in conversation_history if msg["id"] == message_id),
                        None
                        )
                        if reported_assistant_message:
                            # first fetch existing rules
                            print("Fetching all existing hard rules....")
                            existing_rules = supabase_client.table('chat_rules').select("rule_id", "rule").eq("hard_rule", True).execute().data

                            print("All existing hard rules", existing_rules)
                            
                            response = report_rule_generator.invoke({"existing_rules": existing_rules,"assistant_response": reported_assistant_message, "report_reason": feedback})

                            existing_rule = response.existing_rule
                            if existing_rule:
                                print("Similar in intent rule already exists, returning...")
                                continue
                            else:
                                report_relevance = response.report_relevance
                                if report_relevance == "relevant":
                                    rule = response.report_rule
                                    rule_id = response.rule_id

                                    if not rule:
                                        print("No rule, continuing...")
                                        continue
                                    if rule_id:
                                        # first delete the conflicting rule
                                        supabase_client.table('chat_rules').delete().eq("rule_id", rule_id).execute()
                                    
                                    # insert the new rule
                                    try:
                                        # insert hard rule in a different thread for optimization
                                        await asyncio.to_thread(insert_report_rule,rule, supabase_client, message_id)
                                        await websocket.send_json({
                                            "type": "report",
                                            "message_id": message_id,
                                            "status": "acknowledged"
                                        })
                                        ack_sent = True
                                        print(f"Message with {message_id} is successfully reported!")
                                    except Exception as e:
                                        await websocket.send_json({
                                        "type": "report",
                                        "status": "not-acknowledged"
                                        })
                                        ack_sent = True
                                    continue
                                else:
                                    print("Nor valid response reason")
                                    continue
                        else:
                            print(f"No assistant message found for message_id {message_id}, can't report message. Proceeding...")
                                
                            
                    elif variant == "normal":
                        rule = data.get("rule")
                        if not rule:
                            print("No rule reported content, Can't Report message. Proceeding...")
                            continue
                        try:
                            # insert rule in the feedback system
                            await asyncio.to_thread(insert_report_rule, rule, supabase_client, message_id)
                            await websocket.send_json({
                                "type": "report",
                                "message_id": message_id,
                                "status": "acknowledged"
                            })
                            ack_sent = True
                            print(f"Message with {message_id} is successfully reported!")
                        except Exception as e:
                            await websocket.send_json({
                                "type": "report",
                                "status": "not-acknowledged"
                            })
                            ack_sent = True
                            continue
                except Exception as e:
                    print(f"Some exception occured while reporting message with message ID {message_id}")    
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
                    asyncio.create_task(asyncio.to_thread(submit_feedback, type, message, message_id))
                    
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
    # finally:
    #     # --- ADDED: CLEANUP STT ---
    #     if stt_engine:
    #         await stt_engine.stop()
    #         stt_task.cancel()
            # --------------------------
