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

import os
import json
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from agents import Runner
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
import agent as agent_module
import logging

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
    # """Fallback HTTP chat route (non-WebSocket)."""
    # if API_KEY:
    #     if authorization is None or authorization != f"Bearer {API_KEY}":
    #         raise HTTPException(status_code=401, detail="Unauthorized")

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
    # except InputGuardrailTripwireTriggered as e:
    #     # Use fallback output generated inside the guardrail
    #     msg = getattr(e.guardrail_result, "output_info", None)
    #     if not msg:
    #         # If somehow no fallback output was generated
    #         msg = await Runner.run(
    #             agent_module.fallback_agent, 
    #             conversation, 
    #             run_config=getattr(agent_module, "config", None)
    #         )
    #         msg = getattr(msg, "final_output", "Sorry, I can only respond within Quranic context.")
    #     return {"reply": msg}

    except OutputGuardrailTripwireTriggered as e:
        msg = getattr(e.guardrail_result, "output_info",
                      "Sorry, I can only respond within Quranic context.")
        return {"reply": msg}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------- WEBSOCKET ENDPOINT -------------------


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Handles Quran AI chat via WebSocket."""
    await websocket.accept()
    logger.info("Connected to websocket successfully!")
    try:
        # # Expect the first message to contain API key
        # init_msg = await websocket.receive_text()
        # init_data = json.loads(init_msg)
        # token = init_data.get("authorization")

        # # # Security check
        # # if API_KEY and token != f"Bearer {API_KEY}":
        # #     await websocket.send_json({
        # #         "type": "error",
        # #         "content": "Unauthorized WebSocket connection."
        # #     })
        # #     await websocket.close()
        # #     return

        # # Acknowledge connection
        # await websocket.send_json({
        #     "type": "connection_ack",
        #     "content": "WebSocket connected successfully."
        # })

        # Main message loop
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            
            messages = data.get("messages", [])

            conversation = "\n".join(
                [f"{m['role']}: {m['content']}" for m in messages]
            )

            logger.info(f"conversation: {conversation}")

            try:
                result =await Runner.run(
                    agent_module.agent,
                    conversation,
                    run_config=getattr(agent_module, "config", None)
                )

                logger.info(f"result: {result}")
                reply_text = getattr(result, "final_output", None) or getattr(result, "output_text", None) or str(result)

                logger.info(f"reply_text: {reply_text}")
                await websocket.send_json({
                    "type": "assistance_response",
                    "content": reply_text
                })

            except InputGuardrailTripwireTriggered as e:
                # Use the fallback agent's response if it exists
                msg = getattr(e.guardrail_result, "output_info", None)
                if not msg:
                    # If guardrail didn’t produce fallback
                    fallback_result = await Runner.run(
                        agent_module.fallback_agent,
                        conversation,
                        run_config=getattr(agent_module, "config", None)
                    )
                    msg = getattr(fallback_result, "final_output", "Sorry, I can only respond within Quranic context.")
                
                await websocket.send_json({
                    "type": "assistance_response",
                    "content": msg
                })

            except OutputGuardrailTripwireTriggered as e:
                msg = getattr(e.guardrail_result, "output_info",
                              "Sorry, I can only respond within Quranic context.")
                await websocket.send_json({
                    "type": "assistance_response",
                    "content": msg
                })

            except Exception as e:
                logger.info(f"⚠️ WebSocket internal error: {e}")
                import traceback
                traceback.print_exc()  # 👈 will show full stack trace in terminal
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })
                # await websocket.send_json({
                #     "type": "error",
                #     "content": str(e)
                # })

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected")

    except Exception as e:
        logger.info(f"⚠️ WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


# ------------------- APP RUNNER -------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
