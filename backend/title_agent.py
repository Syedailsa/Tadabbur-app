# title_agent.py
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from agents import Agent
from pydantic import BaseModel, Field
from prompts.title_agent_instructions import system_prompt
from langchain_groq import ChatGroq

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')


if not GROQ_API_KEY:
    raise ValueError("GROQ Api key is missing")
model = ChatGroq(
    model = "openai/gpt-oss-120b",
    temperature = 0,
    api_key = GROQ_API_KEY
)


class OutputSchema(BaseModel):
    """Title and Description for a chat session"""
    title: str = Field(description="The title of the chat session (3-4 words maximum)")
    description: str = Field(description="The description of the chat session (concise summary)")


title_agent = create_agent(
    name="Title and Description Generator",
    model = model,
    system_prompt=system_prompt,
    response_format = OutputSchema
)
