# main.py
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from agents import Runner
import agent as agent_module 

app = FastAPI(title="Tadabbur Agent API")

# Allow your Next.js origin (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

# simple API key for the endpoint for security
API_KEY = os.getenv("CHAT_API_KEY")

@app.post("/api/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(None)):
    if API_KEY:
        if authorization is None or authorization != f"Bearer {API_KEY}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        conversation = "\n".join(
            [f"{m.role}: {m.content}" for m in req.messages]
        )

        result = await Runner.run(
            agent_module.agent,
            conversation,
            run_config=getattr(agent_module, "config", None)
        )

        # Extracting reply
        reply_text = None
        if hasattr(result, "final_output") and result.final_output:
            reply_text = result.final_output
        elif hasattr(result, "output_text") and result.output_text:
            reply_text = result.output_text
        else:
            reply_text = str(result)

        return {"reply": reply_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
