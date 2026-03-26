import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.messages import SystemMessage, HumanMessage
from prompts.prompt_builder_instructions import prompt_builder_instructions
load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')

model = ChatGroq(
    api_key = GROQ_API_KEY,
    model = "openai/gpt-oss-20b",
    temperature = 0,
)

class ImagePrompt(BaseModel):
    image_prompt: str = Field(..., description = "The image prompt for generating an AI image")


prompt_builder = model.with_structured_output(ImagePrompt, method = "json_schema")
