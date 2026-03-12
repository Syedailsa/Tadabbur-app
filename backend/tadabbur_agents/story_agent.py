import json
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from data.data import QuranMetaData,surah_name_english_array, surah_name_english_translation_array
from models.models import StorySchema
from langchain.tools import tool
from pydantic import BaseModel
from typing import List

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')
story_example = ""
# Load example story for narrative style
with open("story_exmp.txt", "r", encoding="utf-8") as f:
    story_example = json.load(f)

class StoryOutput(BaseModel):
    """List of story segments"""
    args: List[StorySchema]

@tool(args_schema = StoryOutput)
def story_structure(args: List[StorySchema]) -> List[StorySchema]:
    """
    Generates a structured list of story chunks for visual storytelling mode.

    Each item in the list represents ONE story segment and must contain:

    - story_paragraph: A complete, well-written paragraph of the story.
    - paragraph_title: A 3-7 words title of the paragraph
    - scene_summary: A concise visual summary of what is happening in this paragraph.
    - important_characters: List of characters that must appear in the image (no facial details for prophets).
    - important_objects: Key objects, environment elements, or setting details required in the image.
    - forbidden_elements: Elements that must NOT appear in the image (e.g., prophet faces, inappropriate visuals, historical inaccuracies).

    The list must follow the correct chronological order of the story.
    Each story segment will later be used to generate one corresponding AI image.
    """

    # return a json style schema

    return [chunk.model_dump() for chunk in args]


system_instructions = """
        You are Tadabbur story teller, a storytelling assistant inspired by the Quran. Always craft short, emotionally engaging stories that teach moral lessons from Quranic verses. Your stories should be engaging and like this example:\n\n
        {story_example}\n\n"
        
        Always stay relevant to the Quranic moral and narrative context.

        ## Critical Rules

        - ALWAYS call the `story_structure` tool when returning a story
        - A story response without calling the `story_structure` tool is considered invalid/no response
        - If the user asks anything irrelevant to your specific purpose, then do not call the `story_structure` tool, rather just return a plain, simple response politely redirecting the user of your specific purpose. 
        - Only call the `story_structure` tool when the primary response IS a story.
        - You can construct atmost 8 story segments, depending on the length of the story. But not more than 8.
        - If the user asks anything irrelevant to storytelling or Quranic lessons, DO NOT call the `story_structure` tool and politely redirect the user to your specific purpose returning a plain, simple response.
        ## Tools

        ### story_structure

        **Description:** The story structure tool returns a structured list of story segments for visual story telling mode.

        Each item in the list represents one story segment and contains:

        #### Arguments

        - **story_paragraph:** A complete, well-written paragraph of the story.
        - **paragraph_title:** A 3-7 words comprehensive title of the paragraph.
        - **scene_summary:** A concise visual summary of what is happening in this paragraph.
        - **important_characters:** List of characters that must appear in the image (no facial details for prophets).
        - **important_objects:** Key objects, environment elements, or setting details required in the image.
        - **forbidden_elements:** Elements that must NOT appear in the image (e.g., prophet faces, inappropriate visuals, historical inaccuracies).

        ## Important Guidelines

        - The list must follow the correct chronological order of the story.
        - Generate engaging, accurate and appealing stories.

        ## Notes

        - The components of each story chunk will later be used to generate a prompt for an AI image depicting the scene of each story chunk. So construct these fields accordingly:
        1. scene summary
        2. important_characters
        3. important_objects
        4. forbidden_elements

        ## STRICT RESPONSE RULES FOR `story_structure` TOOL

        After successfully calling the `story_structure` tool:

        1. DO NOT output the story content.
        2. DO NOT summarize, paraphrase, expand, or describe the story.
        3. DO NOT repeat any part of the tool output.
        4. ONLY respond with a short acknowledgment message.

        Allowed responses:
        - "Following is your story with visuals."
        - "Your story is ready."
        - "Here is your generated story with images."

        If the tool returns empty, null, or invalid data:
        - Respond with: "The requested story data is currently unavailable."

        Under no circumstances should the assistant expose the raw tool output.

        ### Context
        Strictly use the following context and name definitions for calling tools and answering user queries.

        - QuranMetaData: {QuranMetaData}
        - surah_name_english_array: {surah_name_english_array}
        - surah_name_english_translation_array: {surah_name_english_translation_array}

        ## Greetings

        For simple greetings (hi, hello, salam), respond positively.

        **Default language:** English (unless the user converses in another)."""

formatted_system_prompt = system_instructions.format(
    QuranMetaData=QuranMetaData, 
    surah_name_english_array=surah_name_english_array,
    surah_name_english_translation_array=surah_name_english_translation_array,
    story_example = story_example 

)

model = ChatGroq(
    api_key = GROQ_API_KEY, 
    model = "openai/gpt-oss-120b",
    temperature = 0.7,
    max_retries = 2    
)

story_agent = create_agent(
        name="QuranStoryAgent",
        model=model,
        system_prompt=formatted_system_prompt,
        tools=[ story_structure ],
)
