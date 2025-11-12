from pydantic import BaseModel
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    RunConfig,
    
)

import os
from dotenv import load_dotenv
import asyncio
import pandas as pd

# Load .env
load_dotenv()
FIRE_WORKS_API = os.getenv("FIREWORKS_API_KEY")
if not FIRE_WORKS_API:
    raise ValueError("API_KEY not found in environment variables.")

# CSV path
CSV_PATH = "daily_duas.csv"


# Read CSV
df = pd.read_csv(CSV_PATH)

# Prepare a knowledge base from CSV
csv_context_list = []
for idx, row in df.iterrows():
    entry = (
        f"Context: {row['Context']}\n"
        f"Arabic: {row['Arabic_Text']}\n"
        f"Translation: {row['Translation']}\n"
        f"Reference: {row['Reference/Source']}"
    )
    csv_context_list.append(entry)

# Join first 100 entries (or fewer)
csv_context = "\n\n".join(csv_context_list[:100])

# Setup client
client = AsyncOpenAI(
    api_key=FIRE_WORKS_API,
    base_url="https://api.fireworks.ai/inference/v1"
)

# LLM model
llm_model = OpenAIChatCompletionsModel(
    model="accounts/fireworks/models/gpt-oss-20b",
    openai_client=client
)

config = RunConfig(
    model=llm_model,
    model_provider=client,
    tracing_disabled=True
)

# Define agent
ApplicationAgent = Agent(
    name="Daily Islamic Mentor",
    instructions=f"""
        You are a calm, humble, mentor-like Islamic guide.
        Use only the provided CSV knowledge base strictly:
        {csv_context}

        Always answer from it. Never invent or modify content.

        If no relevant dua or hadith is found, reply politely:
        "I’m sorry, I couldn’t find an authentic reference for this topic in my data."

        When providing a match:
        - Share Arabic text, English translation, short practical steps, and source.
        - Keep responses concise, spiritually meaningful, and teacher-like.
    """
)

   
