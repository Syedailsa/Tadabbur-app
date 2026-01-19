import asyncio
import json
import os
from typing import Optional
# from tafseer_agent import Tafsir_Agent
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from agents import function_tool
from openai import OpenAI
from langchain_groq import ChatGroq
from langchain.agents import create_agent

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')
load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_AI_API_KEY")

with open("story_exmp.txt", "r", encoding="utf-8") as f:
    story_example = json.load(f)

system_instructions = f"""You are Tadabbur, a storytelling assistant inspired by the Quran. "
        f "Always craft short, emotionally engaging stories "
        "that teach moral lessons from Quranic verses. "
        "Your stories should be engaging and like this example:\n\n"
        {story_example}\n\n"
        "the final answer should be in a story format for users to read and not in json form. "
        "Always stay relevant to the Quranic moral and narrative context.
"""
model = ChatGroq(
    api_key = GROQ_API_KEY, 
    model = "openai/gpt-oss-120b",
    temperature = 0.7,
    max_retries = 2    
)

story_agent = create_agent(
    model = model,
    tools = [],
    system_prompt = system_instructions
)




        