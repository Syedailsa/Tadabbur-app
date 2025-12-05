import os
import json
import re
from dotenv import load_dotenv
from pathlib import Path
import asyncpg
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from typing import List, Optional

from agents import Runner
from agents import Agent, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, SQLiteSession
import agent as agent_module
import story_agent as story_module
import sqlite3
import logging
import secrets
from agents import ItemHelpers
from api import (
    auth_router,
    notif_router,
    bookmark_router,
    profile_router,
    feedback_router
)
from quran_api import quran_router , parah_router, story_router
from database import init_db_pool, close_db_pool, create_tables
from fastapi.security import HTTPBearer
# =========== Title Agent ============
from title_agent import title_agent

import pprint
pp = pprint.PrettyPrinter(indent=2)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------- APP CONFIG -------------------

app = FastAPI(title="Tadabbur Agent API",
              description= "Backend API for Quranic Tadabbur Agent Application",
              version="1.0.0")

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
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = custom_openapi


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


# ================= Routes =================
app.include_router(auth_router)
app.include_router(notif_router)
app.include_router(bookmark_router)
app.include_router(profile_router)
app.include_router(feedback_router)
app.include_router(quran_router)
app.include_router(parah_router)
app.include_router(story_router)



API_KEY = os.getenv("CHAT_API_KEY")



# ------------------- SESSION CODE -------------------

DB_PATH = "message_data.db"

def init_db():
    """Initialize clean database schema"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Drop old tables if they exist
        c.execute("DROP TABLE IF EXISTS agent_messages")
        c.execute("DROP TABLE IF EXISTS agent_sessions")
        
        # Create NEW clean schema
        c.execute('''
            CREATE TABLE agent_sessions (
                session_id TEXT PRIMARY KEY,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE agent_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id)
            )
        ''')
        
        c.execute('CREATE INDEX IF NOT EXISTS idx_session_time ON agent_messages(session_id, created_at)')
        conn.commit()
    
    logger.info("✅ Database initialized with clean schema")


def generate_session_id() -> str:
    """Generate unique session ID"""
    return f"sess_{secrets.token_hex(6)}"


def ensure_session_exists(session_id: str):
    """Ensure session exists in database"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO agent_sessions (session_id, created_at, updated_at)
            VALUES (?, datetime('now'), datetime('now'))
        """, (session_id,))
        conn.commit()
init_db()

def clean_message_content(content: str) -> str:
    """Clean message content from role prefixes and conversation format"""
    if not content:
        return ""
    
    content = content.strip()
    
    # Remove ALL role prefixes recursively
    prev_content = ""
    while prev_content != content:
        prev_content = content
        content = re.sub(r'^(user|assistant):\s*', '', content, flags=re.IGNORECASE | re.MULTILINE)
        content = content.strip()
    
    # If multi-line with conversation format, extract LAST user input only
    if '\n' in content:
        lines = content.split('\n')
        
        # Check if conversation format exists
        has_roles = any(
            re.match(r'^(user|assistant):\s*', line.strip(), re.IGNORECASE)
            for line in lines
        )
        
        if has_roles:
            # Find the LAST user message
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if re.match(r'^user:\s*', line, re.IGNORECASE):
                    clean_line = re.sub(r'^user:\s*', '', line, flags=re.IGNORECASE)
                    return clean_line.strip()
            
            # If no "user:" found, return first non-empty line without role prefix
            for line in lines:
                cleaned = re.sub(r'^(user|assistant):\s*', '', line.strip(), flags=re.IGNORECASE)
                if cleaned:
                    return cleaned
    
    return content.strip()

def save_message_to_db(session_id: str, role: str, content: str):
    """Save ONLY clean role + content"""
    content = content.strip()
    if not content or role not in ["user", "assistant"]:
        return

    # Clean content - remove any role prefixes
    clean_content = clean_message_content(content)
    if not clean_content:
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            
            # Check for duplicates
            c.execute("""
                SELECT 1 FROM agent_messages 
                WHERE session_id = ? AND role = ? AND content = ? 
                AND created_at > datetime('now', '-10 seconds')
            """, (session_id, role, clean_content))
            
            if c.fetchone():
                logger.info(f"⚠️ Duplicate {role} message skipped")
                return
            
            # Ensure session exists
            ensure_session_exists(session_id)
            
            # Insert clean message
            c.execute("""
                INSERT INTO agent_messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (session_id, role, clean_content))
            
            # Update session timestamp
            c.execute("""
                UPDATE agent_sessions 
                SET updated_at = datetime('now') 
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            
        logger.info(f"✅ Saved {role}: {clean_content[:50]}...")
    except Exception as e:
        logger.error(f"❌ DB Save failed: {e}")


def get_chat_messages(session_id: str):
    """Get clean chat messages - direct from columns"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT role, content 
            FROM agent_messages 
            WHERE session_id = ? 
            ORDER BY created_at ASC
        """, (session_id,))
        
        messages = []
        for role, content in c.fetchall():
            if role in ["user", "assistant"] and content.strip():
                messages.append({
                    "role": role,
                    "content": content.strip()
                })
        
        logger.info(f"✅ Loaded {len(messages)} messages for {session_id}")
        return messages


def get_all_sessions_from_db():
    """Get all sessions with clean data"""
    import datetime
    
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT s.session_id, s.created_at, s.updated_at 
            FROM agent_sessions s
            WHERE EXISTS (
                SELECT 1 FROM agent_messages m 
                WHERE m.session_id = s.session_id
            )
            ORDER BY s.updated_at DESC
        """)
        
        sessions = []
        today = datetime.date.today()
        
        for sid, created_at, updated_at in c.fetchall():
            # Get first user message for title
            c.execute("""
                SELECT content FROM agent_messages 
                WHERE session_id = ? AND role = 'user' 
                ORDER BY created_at ASC LIMIT 1
            """, (sid,))
            
            user_row = c.fetchone()
            if not user_row:
                continue
            
            user_msg = user_row[0]
            title = "Quranic Reflection"
            
            try:
                result = Runner.run_sync(
                    title_agent, 
                    f"Create a beautiful short title for: {user_msg[:80]}"
                )
                smart = result.final_output.strip().strip('"\'')
                if smart and 5 < len(smart) < 60:
                    title = smart
            except Exception as e:
                logger.error(f"Title generation failed: {e}")
                title = user_msg[:50] + "..." if len(user_msg) > 50 else user_msg
            
            # Get first assistant response for description
            c.execute("""
                SELECT content FROM agent_messages 
                WHERE session_id = ? AND role = 'assistant' 
                ORDER BY created_at ASC LIMIT 1
            """, (sid,))
            
            desc_row = c.fetchone()
            description = desc_row[0][:100] + "..." if desc_row else "New conversation"
            
            # Format date
            try:
                date_obj = datetime.datetime.fromisoformat(updated_at.replace('Z', '+00:00')).date()
                if date_obj == today:
                    display_date = "Today"
                elif date_obj == today - datetime.timedelta(days=1):
                    display_date = "Yesterday"
                else:
                    display_date = date_obj.strftime("%b %d")
            except:
                display_date = "Recently"
            
            # Get message count
            c.execute("""
                SELECT COUNT(*) FROM agent_messages WHERE session_id = ?
            """, (sid,))
            msg_count = c.fetchone()[0]
            
            sessions.append({
                "session_id": sid,
                "title": title,
                "description": description,
                "created_at": display_date,
                "date": display_date,
                "language": "english",
                "message_count": msg_count
            })
        
        logger.info(f"✅ Found {len(sessions)} sessions")
        return sessions
    

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

    # print(f"Data {data}")

    # ====== SESSION CODE START ======

    current_session = None
    session_id = None

    # ========== SESSION END  ======

    session_model_key: str = "gpt-oss-20b"
    active_agent = agent_module.agent
    active_config = getattr(agent_module, "config", None)
    current_agent_name = getattr(active_agent, "name", "QuranTadabburAgent")
    current_agent_normalized = _normalize_name(current_agent_name)


    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            print(f"received: {data}")

            # ========== SESsION CODE START ==========
            # SESSION INIT 
            if data.get("type") == "session-init":
                requested_session_id = data.get("session_id", "").strip()

                if not requested_session_id or requested_session_id == "new":
                    # Create brand new session
                    session_id = generate_session_id()
                    ensure_session_exists(session_id)
                    logger.info(f"New session created: {session_id}")
                else:
                    # Resume existing session
                    session_id = requested_session_id
                    ensure_session_exists(session_id)
                    logger.info(f"Session resumed: {session_id}")

                # Send confirmation — this unblocks frontend
                await websocket.send_json({
                    "type": "session_id",
                    "status": "acknowledged",
                    "session_id": session_id,
                    "current_agent": current_agent_name,
                    "current_model": session_model_key
                })

                continue  

            if data.get("type") == "session_id":
                # check if frontend sent empty session_id (new chat request)

                frontend_session_id = data.get("session_id", "").strip()

                if not frontend_session_id:
                    # generate new session ID 
                    session_id = generate_session_id()

                    ensure_session_exists(session_id)

                    await websocket.send_json({
                        "type": "session_id",
                        "status": "acknowledged",
                        "session_id": session_id
                    })
                    logger.info(f"New session created {session_id}")
                else:
                    # use existing session id from frontend

                    session_id = frontend_session_id
                    ensure_session_exists(session_id)

                    await websocket.send_json({
                        "type": "session_id",
                        "status": "acknowledged",
                        "session_id": session_id
                    })

                continue
            # Handle CHAT HISTORY request

            if data.get("type") in ["like", "dislike", "report_content"]:
                feedback_type = data["type"]                    # "like" / "dislike" / "report_content"
                index = data.get("index")
                sess_id = data.get("session_id") or session_id  # Use provided session_id or current session_id

                # Validation
                if not sess_id:
                    await websocket.send_json({"type": "error", "message": "session_id missing"})
                    continue
                if not isinstance(index, int) or index < 0:
                    await websocket.send_json({"type": "error", "message": "invalid index"})
                    continue

                # Save to PostgreSQL (Supabase)
                try:
                    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
                    await conn.execute(
                        """
                        INSERT INTO content_feedback (session_id, item_index, feedback_type)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (session_id, item_index, feedback_type) DO NOTHING
                        """,
                        sess_id, index, feedback_type
                    )
                    await conn.close()

                    # Success response
                    await websocket.send_json({
                        "type": "feedback_ack",
                        "status": "success",
                        "action": feedback_type,
                        "index": index
                    })

                    # Optional: 10+ reports pe alert
                    if feedback_type == "report_content":
                        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
                        reports = await conn.fetchval(
                            "SELECT COUNT(*) FROM content_feedback WHERE item_index = $1 AND feedback_type = 'report_content'",
                            index
                        )
                        await conn.close()
                        if reports and reports > 10:
                            await websocket.send_json({
                                "type": "content_reported",
                                "index": index,
                                "reports": reports
                            })

                except Exception as e:
                    logger.error(f"Feedback save failed: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "feedback save failed"
                    })

                continue  



            if data.get("type") == "chat_history":
                try:
                    sessions_list = get_all_sessions_from_db()

                    await websocket.send_json({
                        "type": "chat_history",
                        "status":"acknowledged",
                        "chat_history": sessions_list
                    })
                    logger.info(f"Sent {len(sessions_list)} sessions to frontend")
                except Exception as e:
                    logger.error(f"Error fetching chat history: {e}")

                    await websocket.send_json({
                        "type": "chat_history",
                        "status": "non-acknowledged",
                        "chat_history": [],
                        "error": str(e)
                    })
                continue

            # Handle Get SPECIFIC REQUEST

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
                    # Get chat messages
                    messages = get_chat_messages(requested_session_id)
                    
                    # DEBUG: Log what we're sending
                    logger.info(f"📤 Sending chat history for {requested_session_id}:")
                    for i, msg in enumerate(messages):
                        logger.info(f"  {i+1}. [{msg['role']}]: {msg['content'][:50]}...")
                    
                    #  VALIDATE: Check for role errors
                    for msg in messages:
                        if msg['role'] not in ['user', 'assistant']:
                            logger.error(f"❌ Invalid role detected: {msg['role']}")
                    
                    # switch to this session
                    session_id = requested_session_id
                    ensure_session_exists(session_id)
                    
                    await websocket.send_json({
                        "type": "get_chat",
                        "status": "acknowledged",
                        "session_id": session_id,
                        "chat_history": messages
                    })
                    logger.info(f"✅ Loaded chat: {session_id} with {len(messages)} messages")
                    
                except Exception as e:
                    logger.exception(f"❌ Error loading chat: {e}")
                    await websocket.send_json({
                        "type": "get_chat",
                        "status": "non-acknowledged",
                        "session_id": requested_session_id,
                        "error": str(e)
                    })
                continue

            if data.get("type") == "message":
                if not current_session:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Session not initialized!"
                    })
                    continue

                messages = data.get("messages", [])
                if not messages:
                    continue

            # ======= SESSION CODE END ============

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
                    active_config = getattr(story_module, "config", None)
                    current_agent_name = "Quran Storyteller"
                else:
                    active_agent = agent_module.agent
                    active_config = getattr(agent_module, "config", None)
                    current_agent_name = "Quran Tadabbur Agent"

                current_agent_normalized = _normalize_name(current_agent_name)
                await websocket.send_json({
                    "type": "loading_message",
                    "content": f"Switched to **{current_agent_name}** mode"
                })
                continue

            # === MAIN CHAT MESSAGE ===
            messages = data.get("messages", [])
            if messages:
                latest_message = messages[-1]["content"]

                if latest_message.strip() and session_id:

                    latest_role = messages[-1].get("role", "user")

                    if latest_role == 'user':
                        cleaned_content = clean_message_content(latest_message.strip())
                        if cleaned_content:
                            save_message_to_db(session_id, "user", cleaned_content)
                            logger.info(f"💾 User message saved: '{cleaned_content[:30]}...'")
                        
                else:
                    logger.warning(f"⚠️ Skipping non-user message from frontend: {latest_role}")


                # if latest_message.strip() and session_id:
               
            if len(messages) == 1 and messages[0]["role"] == "user":
                try:
                    temp_config = agent_module.get_model_config(session_model_key)
                    result = await Runner.run(
                        title_agent,
                        f"Generate a short title for this first message: {messages[0]['content']}",
                        run_config=temp_config
                    )
                    smart_title = result.final_output.strip()
                    if smart_title and len(smart_title) > 3:
                        await websocket.send_json({
                            "type": "chat_title",
                            "title": smart_title
                        })
                    else:
                        await websocket.send_json({"type": "chat_title", "title": "Quranic Reflection"})
                        logger.info(f"Live title sent: {smart_title}")
                except:
                    await websocket.send_json({"type": "chat_title", "title": "Quranic Reflection"})
              
            else:
                latest_message = ""

            logger.info(f"[{current_agent_name}] Session: {session_id} | Message: {latest_message[:50]} ...")

            run_result = None


            conversation = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            logger.info(f"[{current_agent_name}] Processing with model: {session_model_key}")

            try:
                dynamic_config = agent_module.get_model_config(session_model_key)
                base_config = getattr(active_agent, "config", None) or agent_module.config
                if base_config and hasattr(base_config, "model_settings"):
                    dynamic_config.model_settings = base_config.model_settings

                # Show initial thinking
                # await websocket.send_json({
                #     "type": "loading_message",
                #     "content": "Thinking deeply about your question..."
                # })

                run_result = Runner.run_streamed(
                    active_agent,
                    conversation,
                    run_config=dynamic_config,
                    session= None
                )

                final_text = ""  # Will collect all visible text

                async for event in run_result.stream_events():

                    # # === LLM TOKEN STREAMING ====
                    if event.type == "raw_response_event":
                        delta = getattr(event.data, "delta", None) or getattr(event.data, "text", None)
                        if delta and delta.strip():
                            # Block raw tool call JSON
                            if not (delta.strip().startswith("{") and ("name" in delta or "arguments" in delta)):
                                # await websocket.send_json({
                                #     "type": "assistance_response_chunk",
                                #     "content": delta
                                # })
                               
                                final_text += delta
                        continue

                    # === AGENT HAND-OFF ===
                    elif event.type == "agent_updated_stream_event":
                        new_name = None
                        try:
                            obj = getattr(event, "new_agent", None)
                            new_name = getattr(obj, "name", None) if obj else getattr(event.data, "new_agent_name", None)
                        except:
                            pass
                        if new_name and _normalize_name(new_name) != current_agent_normalized:
                            mapped = _map_name_to_agent(new_name)
                            if mapped:
                                active_agent = mapped
                                active_config = getattr(mapped, "config", active_config)
                                current_agent_name = getattr(mapped, "name", new_name)
                            else:
                                current_agent_name = new_name
                            current_agent_normalized = _normalize_name(current_agent_name)

                            await websocket.send_json({
                                "type": "loading_message",
                                "content": f"Handing to expert..**"
                            })
                        continue

                    # === TOOL CALL & OUTPUT ===
                    elif event.type == "run_item_stream_event":
                        item = event.item
                        itype = getattr(item, "type", None)

                    elif event.type == "tool_call_item":
                        await websocket.send_json({
                            "type": "loading_message",
                            "content": "Searching authentic Quranic sources..."
                        })

                    elif event.type == "tool_call_output_item":
                        output = getattr(event.item, "output", "")
                        if isinstance(output, str) and output.strip():
                            await websocket.send_json({
                                "type": "assistance_response_chunk",
                                "content": output
                            })

                    elif event.type == "message_output_item":
                        try:
                            text = ItemHelpers.text_message_output(event.item)
                        except:
                            text = str(event.item)
                        if text and text.strip():
                            await websocket.send_json({
                                "type": "assistance_response_chunk",
                                "content": text
                            })
                        

                final_output = (
                    getattr(run_result, "final_output", None) or
                    getattr(run_result, "output_text", None) or
                    getattr(run_result, "assistance_response", None) or
                    ""
                )
                if final_output and isinstance(final_output, str) and final_output.strip():
                    if session_id:
                        cleaned_output = clean_message_content(final_output.strip())
                        if cleaned_output:
                            # BAS ITNA — SIRF EK LINE!
                            save_message_to_db(session_id, "assistant", cleaned_output)
                            logger.info(f"Assistant response saved: '{cleaned_output[:50]}...'")

                    await websocket.send_json({
                        "type": "assistance_response",
                        "content": final_output.strip(),
                        "final": True
                    })

                await websocket.send_json({"type": "streaming_end"})
                await websocket.send_json({"type": "run_complete"}) 

            except InputGuardrailTripwireTriggered as e:
                            msg = getattr(e.guardrail_result, "output_info", None)

                            # If guardrail didn't provide a message → use fallback agent
                            if not msg or not msg.strip():
                                logger.info("Input guardrail triggered → trying fallback agent")

                                # Choose correct fallback agent based on current active agent
                                if getattr(active_agent, "name", "").startswith("QuranTadabburAgent"):
                                    fallback_agent = getattr(agent_module, "fallback_agent", None)
                                elif "Story" in getattr(active_agent, "name", "") or getattr(active_agent, "name", "") == "QuranStoryTeller":
                                    fallback_agent = getattr(story_module, "fallback_agent", None)
                                else:
                                    fallback_agent = getattr(agent_module, "fallback_agent", None)

                                if fallback_agent:
                                    try:
                                        fallback_result = await Runner.run(
                                            fallback_agent,
                                            conversation,
                                            run_config=active_config or dynamic_config
                                        )
                                        msg = getattr(fallback_result, "final_output", None) or \
                                            getattr(fallback_result, "output_text", None) or \
                                            "I'm sorry, I can't assist with that topic."
                                    except Exception as fallback_err:
                                        logger.error(f"Fallback agent failed: {fallback_err}")
                                        msg = "I'm sorry, I can't assist with that topic."
                                else:
                                    msg = "This question is outside my allowed scope."
                            if msg and msg.strip() and session_id:
                                save_message_to_db(session_id, "assistant", msg.strip())
                                logger.info(f"Guardrail/Fallback response saved")

                            # Send final response 
                            await websocket.send_json({
                                "type": "assistance_response",
                                "content": msg.strip()
                            })
                            await websocket.send_json({"type": "streaming_end"})
                            await websocket.send_json({"type": "run_complete"})

            except OutputGuardrailTripwireTriggered as e:
                msg = getattr(e.guardrail_result, "output_info",
                              "Sorry, I can only respond within the context of the Quran and authentic Islamic sources.")
                if msg and msg.strip() and session_id:
                    save_message_to_db(session_id, "assistant", msg.strip())
                    logger.info(f"💾 Output guardrail response saved")

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
# ------------------- APP RUNNER -------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)