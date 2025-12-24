import os
import json
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from supabase import create_client, Client
from supabase.client import ClientOptions
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio # --- ADDED: Required for background tasks
from langchain.messages import HumanMessage, AIMessage
from agents import Runner
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from title_agent import title_agent
import agent as agent_module
import story_agent as story_module
import logging
import secrets
from agents import ItemHelpers  # used to extract message text from items (STREAMING)
load_dotenv()
# --- IMPORT NEW STT CLASS ---
from speech_to_text import SpeechToTextEngine

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


# def get_all_sessions_from_db():
#     """Fetch all sessions from database with metadata"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
   
#     # Get all sessions with their first message as title
#     cursor.execute("""
#         SELECT
#             s.session_id,
#             s.created_at,
#             s.updated_at,
#             s.content,
#             (
#                 SELECT message_data
#                 FROM agent_messages
#                 WHERE session_id = s.session_id
#                 AND json_extract(message_data, '$.role') = 'user'
#                 ORDER BY created_at ASC
#                 LIMIT 1
#             ) as first_message,
#             (
#                 SELECT COUNT(*)
#                 FROM agent_messages
#                 WHERE session_id = s.session_id
#             ) as message_count
#         FROM agent_sessions s
#         ORDER BY s.updated_at DESC
#     """)
   
#     sessions = []
#     for row in cursor.fetchall():
#         session_id, content, created_at, updated_at, first_message_json, message_count = row
       
#         print(content)
#         # Extract title from first user message
#         title = "New Chat"
#         if first_message_json:
#             try:
#                 first_msg = json.loads(first_message_json)
#                 content = first_msg.get("content", "")
#                 # Use first 50 chars as title
#                 title = content[:50] + "..." if len(content) > 50 else content
#             except:
#                 pass
       
#         # Generate description
#         description = f"{message_count} messages"
       
#         sessions.append({
#             "session_id": session_id,
#             "title": title,
#             "description": description,
#             "content": content,
#             "date": updated_at,
#             "language": "english"  # Default, can be enhanced later
#         })
   
#     conn.close()
#     return sessions


# def get_chat_messages(session_id: str):
#     """Get all messages for a specific session"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
   
#     cursor.execute("""
#         SELECT message_data
#         FROM agent_messages
#         WHERE session_id = ?
#         ORDER BY created_at ASC
#     """, (session_id, ))
   
#     messages = []
#     for (message_data,) in cursor.fetchall():
#         try:
#             msg = json.loads(message_data)
#             messages.append({
#                 "role": msg.get("role", "user"),
#                 "content": msg.get("content", "")
#             })
#         except:
#             continue
   
#     conn.close()
#     return messages




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
        msg = getattr(e.guardrail_result, "output_info",
                      "Sorry, your question seems unrelated to the Quranic context.")
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
        print("Connecting to Database for saving user messages")
        supabase_client: Client = create_client(
            TADABBUR_PROJECT_URL,
            TADABBUR_API_KEY,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10,
                schema="public",
            )
        )
        print("✅ Supabase Client connected successfully!")
    except Exception as e:
        print("Some error occured while connecting to supabase", e)

    # STT State
    stt_engine: Optional[SpeechToTextEngine] = None
    stt_task: Optional[asyncio.Task] = None

    # ====== SESSION CODE START ======
    current_session = None
    session_id = None
    # ========== SESSION END  ======
    session_model_key: str = "gpt-oss-20b"
    active_agent = agent_module.main_agent
    current_agent_name = active_agent.name

    # await websocket.send_json({
    #     "type": "session_init",
    #     "session_id": session_id,
    #     "current_model": session_model_key,
    #     "current_agent": current_agent_name
    # })
    
    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                if stt_engine: # Only feed if we started the mic
                    await stt_engine.process_audio(message["bytes"])
                continue
            # -----------------------------------------------------------------


            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue
                # --- ADDED: LIFECYCLE MANAGEMENT FOR STT ---
                # creates a engine every time 'start_mic' is sent
               
                if data.get("type") == "start_mic":
                    logger.info("🎙️ Received Start Mic command")
                    # 1. Cleanup old if exists
                    if stt_engine:
                        await stt_engine.stop()
                        print("Cancelling task")
                        if stt_task: stt_task.cancel()
                   
                    # 2. Start FRESH engine
                    stt_engine = SpeechToTextEngine()
                    await stt_engine.start()
                   
                    # 3. Start Streaming Task for THIS engine
                    async def stream_stt():
                        try:
                            # unpack text AND is_final flag
                            async for text, is_final in stt_engine.get_text_stream():
                                response_type = "stt_final" if is_final else "stt_chunk"
                                await websocket.send_json({"type": response_type, "text": text})
                        except Exception:
                            pass
                    stt_task = asyncio.create_task(stream_stt())
                    continue


                if data.get("type") == "stop_mic":
                    logger.info("🛑 Received Stop Mic command")
                    # Stop engine to clear buffers
                    if stt_engine:
                        await stt_engine.stop()
                        stt_engine = None
                    if stt_task:
                        stt_task.cancel()
                        stt_task = None
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
                # add a record in chat_sessions table
                try:    
                    print("🔃 Creating a new session record")
                    supabase_client.table("chat_sessions").insert({'session_id': session_id}).execute()
                    
                    print("✅ Successfully created a new session record!")
                except Exception as e:
                    print("Some error occured while adding a new session record", e)

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
            #         sessions_list = get_all_sessions_from_db()

            #         await websocket.send_json({
            #             "type": "chat_history",
            #             "status":"acknowledged",
            #             "chat_history": sessions_list
            #         })
            #         logger.info(f"Sent {len(sessions_list)} sessions to frontend")
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


            # if data.get("type") == "get_chat":
            #     requested_session_id = data.get("session_id", "")


            #     if not requested_session_id:
            #         await websocket.send_json({
            #             "type": "get_chat",
            #             "status": "non-acknowledged",
            #             "error": "session_id is required"
            #         })
            #         continue
            #     try:
            #         # get chat messages
            #         messages = get_chat_messages(requested_session_id)


            #         # switch to this session
            #         session_id = requested_session_id
            #         current_session = SQLiteSession(session_id, DB_PATH)


            #         await websocket.send_json({
            #             "type": "get_chat",
            #             "status": "acknowledged",
            #             "session_id": session_id,
            #             "chat_history": messages
            #         })
            #         logger.info(f"Loaded chat: {session_id} with {len(messages)} messages")
            #     except Exception as e:
            #         logger.error(f"Error loading chat: {e}")
            #         await websocket.send_json({
            #             "type": "get_chat",
            #             "status": "non-acknowledged",
            #             "session_id": requested_session_id,
            #             "error": str(e)
            #         })
            #     continue

            # ============================= MODEL SELECTION HANDLER =============================
            if data.get("type") == "model-selection":
                requested_model = data.get("model")  # e.g., "kimi-k2-instruct-0905", "deepseek-v3p1-terminus"

                # Validate against supported models
                if requested_model in agent_module.SUPPORTED_MODELS:
                    session_model_key = requested_model
                    model_info = agent_module.SUPPORTED_MODELS[requested_model]


                    await websocket.send_json({
                        "type": "model-selection",
                        "status": "acknowledged",
                        "model": requested_model,
                        "display_name": model_info["name"]
                    })
                    await websocket.send_json({
                        "type": "loading_message",
                        "content": f"Switched to **{model_info['name']}**"
                    })
                    logger.info(f"Model switched to: {requested_model} ({model_info['name']})")
                else:
                    await websocket.send_json({
                        "type": "model-selection",
                        "status": "not-acknowledged",
                        "model": requested_model,
                        "error": "This model is not supported.",
                        "available": list(agent_module.SUPPORTED_MODELS.keys())
                    })
                continue  # Skip to next message


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

            # === MAIN CHAT MESSAGE ===
            user_message = data.get("user_message", [])
            if user_message:
                print("Latest message", user_message)
                latest_message = user_message
            else:
                latest_message = {"role": "user", "content": ""}

            # initialize old messages
            old_messages = None
            try:
                print(f"🔃 Retrieving messages for chat with session-id {session_id}")
                old_messages = supabase_client.table('chat_messages').select('role', 'message').eq('session_id', session_id).execute().data
                
            except Exception as e:
                print('An error occured while retieving old messages', e)
            
            # save user message in db
            try:
                supabase_client.table('chat_messages').insert({
                    "session_id": session_id,
                    "role": "user",
                    "message": latest_message['content'],
                }).execute()
                print("✅ User message saved successfully!")
            except Exception as e:
                print("Some error occured while inserting user messages", e)

            logger.info(f"[{current_agent_name}] Session: {session_id} | Message: {latest_message} ...")
            # logger.info(f"[{current_agent_name}] Processing with model: {session_model_key}")
            try:
                conversation_history = []
                # build the conversation history
                if old_messages:
                    for record in old_messages:
                        if record['role'] == "user":
                            conversation_history.append(HumanMessage(record['message']))
                        else:
                            conversation_history.append(AIMessage(record['message']))
                
                latest_message_content = latest_message['content']


                # generate title and description for the current chat history if there are 2 user/assistant messages each
                
                if (len(conversation_history) == 4):
                    conversation_string = ""
                    # build a conversation string from user & assistant messages
                    for message in conversation_history:
                        if isinstance(message, HumanMessage):
                            conversation_string += f"User message: {record['message']} \n"
                        else:
                            conversation_string += f"Assistant message: {record['message']} \n"
                    if conversation_string:
                        try:
                            agent_response = title_agent.invoke(
                                {"messages": [HumanMessage(conversation_string)]}
                                )

                            print("Title agent response", agent_response)
                        except Exception as e:
                            print("Some error occured while generating title and description", e)
                    else:
                        print("No conversation string so not generating title and description.")

                # push the latest user message
                conversation_history.append(HumanMessage(latest_message_content))
                response = active_agent.invoke(
                    {"messages": conversation_history},
                )
                response = response['messages'][-1].content
                try:
                    supabase_client.table('chat_messages').insert({
                        "session_id": session_id,
                        "role": "assistant",
                        "message": response,
                    }).execute()
                    print("✅ Assistant message saved successfully!")
                except Exception as e:
                    print("Some error occured while inserting assistant messages", e)
                if response:
                    print("Assistant response", response)
                    await websocket.send_json({
                        "type": "assistance_response",
                        "content": response,
                        "final": True
                    })


                # === FINAL RESPONSE & CLEANUP ===
                # await websocket.send_json({
                #     "type": "assistance_response",
                #     "content": final_text.strip() if final_text.strip() else "I'm not sure how to respond to that."
                # })


                await websocket.send_json({"type": "streaming_end"})
                await websocket.send_json({"type": "run_complete"})


            # except InputGuardrailTripwireTriggered as e:
            #                 msg = getattr(e.guardrail_result, "output_info", None)


            #                 # If guardrail didn't provide a message → use fallback agent
            #                 if not msg or not msg.strip():
            #                     logger.info("Input guardrail triggered → trying fallback agent")


            #                     # Choose correct fallback agent based on current active agent
            #                     if getattr(active_agent, "name", "").startswith("QuranTadabburAgent"):
            #                         fallback_agent = getattr(agent_module, "fallback_agent", None)
            #                     elif "Story" in getattr(active_agent, "name", "") or getattr(active_agent, "name", "") == "QuranStoryTeller":
            #                         fallback_agent = getattr(story_module, "fallback_agent", None)
            #                     else:
            #                         fallback_agent = getattr(agent_module, "fallback_agent", None)


            #                     if fallback_agent:
            #                         try:
            #                             fallback_result = await Runner.run(
            #                                 fallback_agent,
            #                                 conversation,
            #                                 # run_config=active_config or dynamic_config
            #                             )
            #                             msg = getattr(fallback_result, "final_output", None) or \
            #                                 getattr(fallback_result, "output_text", None) or \
            #                                 "I'm sorry, I can't assist with that topic."
            #                         except Exception as fallback_err:
            #                             logger.error(f"Fallback agent failed: {fallback_err}")
            #                             msg = "I'm sorry, I can't assist with that topic."
            #                     else:
            #                         msg = "This question is outside my allowed scope."


            #                 # Send final response
            #                 await websocket.send_json({
            #                     "type": "assistance_response",
            #                     "content": msg.strip()
            #                 })
            #                 await websocket.send_json({"type": "streaming_end"})
            #                 await websocket.send_json({"type": "run_complete"})


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
    finally:
        # --- ADDED: CLEANUP STT ---
        if stt_engine:
            await stt_engine.stop()
            stt_task.cancel()
            # --------------------------


# ------------------- APP RUNNER -------------------


if __name__ == "__main__":
    import uvicorn
    # IMPORTANT: Run without --reload for Windows asyncio subprocess support
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) <-- REPLACED
    uvicorn.run("main:app", host="0.0.0.0", port=8000)