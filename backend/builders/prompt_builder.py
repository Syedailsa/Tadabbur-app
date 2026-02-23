import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.messages import SystemMessage, HumanMessage

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')

model = ChatGroq(
    api_key = GROQ_API_KEY,
    model = "openai/gpt-oss-20b",
    temperature = 0,
)

class ImagePrompt(BaseModel):
    image_prompt: str = Field(..., description = "The image prompt for generating an AI image")

prompt_builder_instructions = """
    You are a Visual Prompt Architect for an Islamic storytelling application. Your purpose is to construct state of the art, hyper-realistic, detailed prompts for AI images. 
    
    You must:
    1. Create visually rich, cinematic, detailed prompts suitable for modern AI diffusion models (e.g., SDXL).
    2. Respect all religious and ethical constraints strictly.
    3. Never depict prophets' faces or identifiable sacred figures.
    4. Avoid facial detail when instructed.
    5. Ensure modest clothing and historically appropriate environments.
    6. Maintain visual consistency across story scenes.
    8. Include lighting, composition, camera angle, environment depth, texture details.
    9. Convert scene_summary, important_characters, and important_objects into a cohesive visual description.
    10. Strictly exclude forbidden_elements from the final prompt.

    You will be provided the following details for the image:
    
   - scene_summary: A concise visual summary of what is happening in this paragraph.
   - important_characters: List of characters that must appear in the image (no facial details for prophets).
   - important_objects: Key objects, environment elements, or setting details required in the image.
   - forbidden_elements: Elements that must NOT appear in the image (e.g., prophet faces, inappropriate visuals, historical inaccuracies).

   ## INPUTS
   scene_summary: {scene_summary}
   important_characters: {important_characters}
   important_objects: {important_objects}
   forbidden_elements: {forbidden_elements}
"""

prompt_builder = model.with_structured_output(ImagePrompt, method = "json_schema")
