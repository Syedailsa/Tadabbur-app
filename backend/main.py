# ----------------------------------------WEBSOCKET PROTOCOL------------------------------------------------

import os
import json
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from agents import Runner
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
import agent as agent_module
import story_agent as story_module
import logging
from agents import ItemHelpers  # used to extract message text from items (STREAMING)

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
    # try common fallback modules
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
    logger.info("Connected to websocket successfully!")

    # default agent
    active_agent = agent_module.agent
    active_config = getattr(agent_module, "config", None)
    current_agent_name = getattr(active_agent, "name", "QuranTadabburAgent")
    current_agent_normalized = _normalize_name(current_agent_name)

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            # ---------- AGENT SWITCH ----------
            if data.get("type") == "agent":
                agent_name = data.get("agent")
                logger.info(f"Agent switch request: {agent_name}")

                mapped = _map_name_to_agent(agent_name)
                if mapped:
                    active_agent = mapped
                    active_config = getattr(mapped, "config", active_config)
                    current_agent_name = getattr(mapped, "name", agent_name)
                else:
                    # fallback mapping (story-telling button)
                    if agent_name == "story-telling":
                        active_agent = story_module.story_agent
                        active_config = getattr(story_module, "config", None)
                        current_agent_name = getattr(story_module.story_agent, "name", "QuranStoryTeller")
                    else:
                        active_agent = agent_module.agent
                        active_config = getattr(agent_module, "config", None)
                        current_agent_name = getattr(agent_module.agent, "name", "QuranTadabburAgent")

                current_agent_normalized = _normalize_name(current_agent_name)

                await websocket.send_json({
                    "type": "loading_message",
                    "content": f"Switched to **{current_agent_name}** mode."
                })
                continue

            # ---------- NORMAL CHAT ----------
            messages = data.get("messages", [])
            conversation = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            logger.info(f"[{current_agent_name}] conversation: {conversation}")

            run_result = None
            try:
                run_result = Runner.run_streamed(
                    active_agent,
                    conversation,
                    run_config=active_config
                )

                async for event in run_result.stream_events():
                    # ---- TOKEN BY TOKEN ----
                    if event.type == "raw_response_event":
                        delta = None
                        try:
                            delta = getattr(event.data, "delta", None) or getattr(event.data, "text", None)
                        except Exception:
                            pass
                        if delta:
                            await websocket.send_json({
                                "type": "loading_message",
                                "content": delta
                            })
                        continue

                    # ---- AGENT HAND-OFF ----
                    elif event.type == "agent_updated_stream_event":
                        new_name = None
                        try:
                            obj = getattr(event, "new_agent", None)
                            new_name = getattr(obj, "name", None) if obj else getattr(event, "new_agent_name", None)
                        except Exception:
                            pass

                        new_norm = _normalize_name(new_name)
                        if new_norm and new_norm != current_agent_normalized:
                            mapped = _map_name_to_agent(new_name)
                            if mapped:
                                active_agent = mapped
                                active_config = getattr(mapped, "config", active_config)
                                current_agent_name = getattr(mapped, "name", new_name)
                            else:
                                current_agent_name = new_name or current_agent_name
                            current_agent_normalized = new_norm

                            await websocket.send_json({
                                "type": "loading_message",
                                "content": f"Hand-off to **{current_agent_name}**"
                            })
                        continue

                    # ---- RUN ITEM ----
                    elif event.type == "run_item_stream_event":
                        item = event.item
                        itype = getattr(item, "type", None)

                        # TOOL CALL START
                        if itype == "tool_call_item":
                            tool_name = getattr(item, "tool_name", "unknown")
                            await websocket.send_json({
                                "type": "loading_message",
                                "content": f"Fetching story via **{tool_name}**..."
                            })

                        # TOOL OUTPUT 
                        elif itype == "tool_call_output_item":
                            tool_name = getattr(item, "tool_name", "unknown")
                            out = getattr(item, "output", "")
                            if not isinstance(out, str):
                                out = str(out)
                            await websocket.send_json({
                                "type": "loading_message",
                                "content": out,
                                "final": True
                            })

                        # FINAL MESSAGE (fallback)
                        elif itype == "message_output_item":
                            try:
                                text = ItemHelpers.text_message_output(item)
                            except Exception:
                                text = getattr(item, "output", None) or str(item)
                            await websocket.send_json({
                                "type": "loading_message",
                                "content": text,
                                "final": True
                            })

                        # PROGRESS
                        else:
                            await websocket.send_json({
                                "type": "loading_message",
                                "content": f"[thinking] {itype or 'step'}"
                            })
                        continue

                    # ---- UNKNOWN EVENT ----
                    else:
                        await websocket.send_json({
                            "type": "loading_message",
                            "content": f"[debug] {event.type}"
                        })
                        continue

                # ---- SEND FINAL OUTPUT ----
                final_text = None
                try:
                    final_text = getattr(run_result, "final_output", None) \
                            or getattr(run_result, "output_text", None)
                except:
                    final_text = None

                if final_text:
                    await websocket.send_json({
                        "type": "final_output",
                        "content": final_text,
                        "final": True
                    })

                # End packet
                await websocket.send_json({
                    "type": "run_complete"
                })

            # ---------- GUARDRAILS ----------
            except InputGuardrailTripwireTriggered as e:
                msg = getattr(e.guardrail_result, "output_info", None)

                if not msg:
                    # choose fallback based on current agent
                    if getattr(active_agent, "name", "") == "QuranTadabburAgent":
                        fallback_agent = getattr(agent_module, "fallback_agent", None)
                    elif getattr(active_agent, "name", "") == "QuranStoryTeller":
                        fallback_agent = getattr(story_module, "fallback_agent", None)
                    else:
                        fallback_agent = getattr(agent_module, "fallback_agent", None)

                    fallback_result = await Runner.run(
                        fallback_agent,
                        conversation,
                        run_config=active_config
                    )

                    msg = getattr(fallback_result, "final_output", 
                        "Sorry, I can only respond within Quranic context.")

                await websocket.send_json({
                    "type": "message_output",
                    "stream_event": "message_output",
                    "text": msg,
                    "role": "assistant",
                    "final": True
                })

                await websocket.send_json({"type": "run_complete"})


            except OutputGuardrailTripwireTriggered as e:
                msg = getattr(e.guardrail_result, "output_info",
                    "Sorry, I can only respond within Quranic context.")

                await websocket.send_json({
                    "type": "message_output",
                    "stream_event": "message_output",
                    "text": msg,
                    "role": "assistant",
                    "final": True
                })

                await websocket.send_json({"type": "run_complete"})
            except WebSocketDisconnect:
                logger.info("Client disconnected during stream")
                break

            except Exception as e:
                logger.exception("Streaming error")
                await websocket.send_json({
                    "type": "loading_message",
                    "content": f"Error: {str(e)}",
                    "final": True
                })

            finally:
                try:
                    if run_result and getattr(run_result, "aclose", None):
                        await run_result.aclose()
                except Exception:
                    pass

    except WebSocketDisconnect:
        logger.info("Client disconnected (outer)")
    except Exception as e:
        logger.exception("WebSocket outer error")
        try:
            await websocket.close()
        except Exception:
            pass

# ------------------- APP RUNNER -------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



#  ------------------- HTTP protocol  -------------------

# import os
# from dotenv import load_dotenv
# load_dotenv()

# from fastapi import FastAPI, HTTPException, Header
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List

# from agents import Runner
# # Import tripwire exceptions so we can catch them
# from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered  

# import agent as agent_module 

# app = FastAPI(title="Tadabbur Agent API")

# # Allow your Next.js origin (dev)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class Message(BaseModel):
#     role: str
#     content: str

# class ChatRequest(BaseModel):
#     messages: List[Message]

# # simple API key for the endpoint for security
# API_KEY = os.getenv("CHAT_API_KEY")

# @app.post("/api/chat")
# async def chat(req: ChatRequest, authorization: str | None = Header(None)):
#     if API_KEY:
#         if authorization is None or authorization != f"Bearer {API_KEY}":
#             raise HTTPException(status_code=401, detail="Unauthorized")

#     try:
#         conversation = "\n".join(
#             [f"{m.role}: {m.content}" for m in req.messages]
#         )

#         result = await Runner.run(
#             agent_module.agent,
#             conversation,
#             run_config=getattr(agent_module, "config", None)
#         )

#         # Extracting reply
#         reply_text = None
#         if hasattr(result, "final_output") and result.final_output:
#             reply_text = result.final_output
#         elif hasattr(result, "output_text") and result.output_text:
#             reply_text = result.output_text
#         else:
#             reply_text = str(result)

#         return {"reply": reply_text}

#     except InputGuardrailTripwireTriggered as e:
#         # Input was unrelated → return polite fallback message
#         msg = getattr(e.guardrail_result, "output_info", "Sorry, your question seems unrelated to the Quranic context.")
#         return {"reply": msg}

#     except OutputGuardrailTripwireTriggered as e:
#         # Output drifted → return polite fallback message
#         msg = getattr(e.guardrail_result, "output_info", "Sorry, I can only respond within Quranic context.")
#         return {"reply": msg}

#     # Catch any other errors normally
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# ------------------------------------------------------------------------------
