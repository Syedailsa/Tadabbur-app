import json
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from data.data import QuranMetaData,surah_name_english_array, surah_name_english_translation_array
from models.models import StorySchema, StoryParagraph
from langchain.tools import tool
from pydantic import BaseModel
from langchain.messages import HumanMessage, SystemMessage
from builders.prompt_builder import prompt_builder
from generators.image_generator import generate_image, pil_to_img_url
from prompts.prompt_builder_instructions import prompt_builder_instructions
from typing import Dict, List, Union
import logging


load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')
story_example = ""
# Load example story for narrative style
with open("examples/story_exmp.txt", "r", encoding="utf-8") as f:
    story_example = json.load(f)

    
# Production logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StoryOutput(BaseModel):
    """List of story segments"""
    args: List[StorySchema]


@tool(args_schema = StoryOutput)
def generate_ai_images_story(args: List[StorySchema]) -> Dict[str, Union[bool, List[StoryParagraph], str]]:
    """
    Generates a structured list of story chunks for visual storytelling mode.
    
    Returns a dictionary with:
    - success: bool indicating if generation was successful
    - story_data: List[StoryParagraph] containing the generated story segments with images
    - error: error message if any

    The list must follow the correct chronological order of the story.
    """

    story_data: List[StoryParagraph] = []
    if not args:
        logger.info("No story chunks provided to generate_ai_images_story")
        response_object = {
            "success": False,
            "story_data": [],
            "error": "No story details provided to generate a story with AI images"
        }

        return response_object

    data = [chunk.model_dump() for chunk in args] or []

    
    try:
        for i, story_chunk in enumerate(data, start = 1):
            story_paragraph = story_chunk.get("story_paragraph")
            paragraph_title = story_chunk.get("paragraph_title")
            scene_summary = story_chunk.get("scene_summary")
            important_characters = story_chunk.get("important_characters")
            important_objects = story_chunk.get("important_objects")
            forbidden_elements = story_chunk.get("forbidden_elements")

            if None in (scene_summary, important_characters, important_objects, forbidden_elements, paragraph_title, story_paragraph):
                continue
            # build the pipeline

            for try_number in range(8):
                try:
                    # build the AI Prompt builder's prompt                                       
                    prompt_builder_prompt = [
                        SystemMessage(content = prompt_builder_instructions),
                        HumanMessage(content=f"""
                        Scene Summary: {scene_summary} \n\n 
                        Important Characters: {important_characters}\n\n 
                        Important Objects: {important_objects} \n\n 
                        Forbidden Elements: {forbidden_elements}
                        """)
                    ]        
                    response = prompt_builder.invoke(prompt_builder_prompt)
                    image_prompt = response.image_prompt
                    break
                except Exception as e:
                    print(f"Prompt generation failed for image {i}, error: {e},Try number {try_number + 1}, retrying...")
            else:
                print(f"Prompt generation after 8 retries for image {i}")
                continue

            # print(f"Image prompt for image {i}: {image_prompt}")
            # pass the image prompt to the AI image generator
            if not image_prompt:
                continue
            for try_number in range(8):
                try:
                    image = generate_image(image_prompt)
                    image_url = pil_to_img_url(image)
                    story_data.append(StoryParagraph(story_paragraph = story_paragraph, paragraph_title = paragraph_title, image = image_url))
                    # print(f"Image pipeline successfully completed for image {i}")
                    break
                except Exception as e:
                    print(f"Image generation pipeline failed for image {i}, error: {e},Try number {try_number + 1}, retrying...")
            else:
                print(f"Image pipeline failed after 8 retries for image {i}")
                continue

        if story_data:
            logger.info("✅ Successfully generated user story!")
            # print("Story data", story_data)
            response_object = {
                "success": True,
                "story_data": [story_seg.model_dump() for story_seg in story_data],
                "error": ""
            }

            return response_object
        else:
            response_object = {
                "success": False,
                "story_data": [],
                "error": "No Story data is available to return"
            }

            return response_object
    except Exception as e:
        logger.info("Some error occured while generating a story")
        response_object = {
            "success": False,
            "story_data": [],
            "error": f"Error: {e}"
        }
        return response_object

system_instructions = """
        You are Tadabbur story teller, a storytelling assistant inspired by the Quran. You can generate beautiful, engaging and appealing stories along with creative AI generated images using the `generate_ai_images_story` Always craft short, emotionally engaging stories that teach moral lessons from Quranic verses. Your stories should be engaging and similar to these example:\n\n
        {story_example}\n\n"
        
        Always stay relevant to the Quranic moral and narrative context.

        ## Critical Rules

        - ALWAYS call the `generate_ai_images_story` tool when returning a story
        - A story response without calling the `generate_ai_images_story` tool is considered invalid/no response
        - If the user asks anything irrelevant to your specific purpose, then do not call the `generate_ai_images_story` tool, rather just return a plain, simple response politely redirecting the user of your specific purpose. 
        - Only call the `generate_ai_images_story` tool when the primary response IS a story.
        - You can construct atmost 8 story segments, depending on the length of the story. But not more than 8.
        - If the user asks anything irrelevant to storytelling or Quranic lessons, DO NOT call the `generate_ai_images_story` tool and politely redirect the user to your specific purpose returning a plain, simple response.
        ## Tools

        ### generate_ai_images_story

        **Description:** The `generate_ai_images_story` returns a structured list of story segments for visual story telling mode.

        Each item in the list represents one story segment and contains:

        #### Arguments

        - **story_paragraph:** A complete, well-written paragraph of the story. This should not exceed a maximum of 4 sentences.
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

        ## STRICT RESPONSE RULES FOR `generate_ai_images_story` TOOL

        After successfully calling the `generate_ai_images_story` tool:

        1. DO NOT output the story content.
        2. DO NOT summarize, paraphrase, expand, or describe the story.
        3. DO NOT repeat any part of the tool output.
        4. ONLY respond with a short acknowledgment message.

        Allowed responses:
        - <A contextual, brief response acknowledging the generation of story with visuals>

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
        tools=[ generate_ai_images_story ],
)
