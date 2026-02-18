import os
import json
from langchain_groq import ChatGroq
from tools.search_Quran_By_Filters import Search_Quran_By_filters
from tools.searchAsbabNuzul import searchAsbabNuzul
from data.data import QuranMetaData, surah_name_english_array,surah_name_english_translation_array
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain.agents import create_agent
from tools.audio_playback import get_Quran_Audio
from tools.verse_reader import get_verse_image
from tools.story_agent_tool import story_agent_tool
from models import OutputSchema
from langchain.agents.middleware import ToolRetryMiddleware
from langchain.messages import ToolMessage

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')
# FIREWORKS_API_KEY = os.getenv('FIREWORKS_AI_API_KEY')
COLLECTION_NAME = "Quran-Dataset-Collection"
EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"

SUPPORTED_CHAT_MODELS = {
    "Llama 3.1 8B": "llama-3.1-8b-instant",
    "Llama 3.3 70B": "llama-3.3-70b-versatile",
    "GPT OSS 120B": "openai/gpt-oss-120b",     
    "GPT OSS 20B": "openai/gpt-oss-20b",
}

DEFAULT_CHAT_MODEL = "openai/gpt-oss-120b"

def get_llm(model_key: str = None):
    """
    Returns a LangChain ChatGroq instance configured for the specific model.
    """
    if not model_key:
        model_id = DEFAULT_CHAT_MODEL
    elif model_key in SUPPORTED_CHAT_MODELS:
        model_id = SUPPORTED_CHAT_MODELS[model_key]
    elif model_key in SUPPORTED_CHAT_MODELS.values():
        model_id = model_key
    else:
        print(f"⚠️ Model '{model_key}' not found. Falling back to default.")
        model_id = DEFAULT_CHAT_MODEL

    print(f"Initializing Groq LLM: {model_id}")

    try:
        llm = ChatGroq(
            model=model_id,
            api_key=GROQ_API_KEY,
            temperature=0.1,
        )
        return llm
    except Exception as e:
        print(f"❌ Error initializing Groq LLM for {model_id}: {e}")
        raise e



class TableData(BaseModel):
    headers: List[str] = Field(..., description="Column headers for the table")
    rows: List[List[str]] = Field(..., description="Rows of data, matching the order of headers")

class ContentSection(BaseModel):
    heading: str = Field(..., description="Section title, e.g., 'The Creation', 'Lessons Learned'")
    body: str = Field(..., description="Main paragraph text for this section")
    bullet_points: Optional[List[str]] = Field(None, description="List of key takeaways or points, if needed")
    table: Optional[TableData] = Field(None, description="A data table if this section needs to compare items")

class QuranResponse(BaseModel):
    title: str = Field(..., description="The main title of the response")
    intro: Optional[str] = Field(..., description="A brief introduction or summary")
    sections: Optional[List[ContentSection]] = Field(..., description="The detailed content divided into logical sections")
    references: Optional[List[str]] = Field(None, description="List of Quranic Surah/Ayah references used")

def custom_tool_error_handler(exception: Exception) -> str:
    """
    Returns a custom message to the agent when a tool fails.
    """
    return (
        f"System Notice: The tool encountered a technical error: {str(exception)}. "
        "Please inform the user effectively that you couldn't retrieve the specific data "
        "and ask them to try again or rephrase."
    )

def submit_structured_response(**kwargs):
    """
    This function is called by the agent to deliver a structured response when dealing with complex user queries. It returns the data exactly as passed.
    """
    return kwargs

structured_response_tool = StructuredTool.from_function(
    func=submit_structured_response,
    name="Submit_Quran_Response", 
    description="This tool converts complex answers in the required format (Title, Intro, Sections).",
    args_schema=QuranResponse
)


# class OutputSchema(BaseModel):
#     response: str = Field(..., description="The final response to the user")
#     has_verse_audio: bool = Field(..., description = "Determines whether the response contains Verse audio links or not")
#     audio_data: Optional[List[SurahForAudio]] = Field(None, description="Audio data for the required verses")
#     has_verse_image: bool = Field(..., description = "Determines whether the response contains verse image links or not")
#     verse_images: Optional[List[SurahForImage]] = Field(None, description = "Verse image data containing verse-image links, surah names, verse numbers")


standard_system_instructions = """
    You are **Tadabbur**, a Quranic knowledge assistant who helps users learn about Quran and strengthen their relationship with Allah.
    {user_context}


    ## Critical Rules
    - NEVER make up verses.
    - ONLY use what the tools return.
    - If a topic is too mature or complex, simplify it gently or steer the conversation to a positive lesson.
    - You are strictly a Quran knowledgeable assistant; if a user asks something irrelevant to your role, politely redirect them to your specific role and purpose, which is to help users learn about the Quran.
    - If a user asks for more than 30 verses or demands a large amount of data, apologize, explain that you cannot fetch large amounts of data, and ask them to shorten the desired amount.


    ## Tools

    ### 1. searchAsbabNuzul
    Use `searchAsbabNuzul` when the user asks for queries related to Asbab al-Nuzul/Shan al-Nuzul (Circumstances of revelation). Use it for searching through user-provided references like surah name, verse number, etc., as well as for performing semantic searches by forming a query derived from the user's question or query.


    #### Example Queries
    1. What is the asbab e nuzul of Surah Al-Kafirun?
    2. What is the asbab e nuzul of Surah Al-Fatiha, verse 1?
    3. What is the Asbab Nuzul of Surah Yunus, verse 10; Surah Al-Baqarah, verse 20; and Surah An-Nisa, verse 20?
    4. What is the shan e nuzul of the surah which was revealed when the Prophet (A.S) was inflicted by magic?


    #### Important Guidelines
    1. When calling `searchAsbabNuzul`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.
    2. Do **not** infer metadata such as `surah_number`, `verse_number`, `surahEnglishName`, `surahEnglishNameTranslation`.
    3. If the user provides only surah and ayah numbers → pass **only those fields**.


    #### Examples of Tool Calls for searchAsbabNuzul


    - **User:** `"What is Asbab Nuzul of verse 5 of Surah Al-Fatiha?"`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_number": 1,
                    "surah_englishName": "Al-Faatiha",
                    "verse_number": 5
                }}
            ]
        }}
        ```


    - **User:** `"What is Asbab Nuzul of Surah Al-Fatiha and Surah Yusuf, verse 10?"`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_number": 1,
                    "surah_englishName": "Al-Faatiha"
                }},
                {{
                    "surah_number": 12,
                    "surah_englishName": "Yusuf",
                    "verse_number": 10
                }}
            ]
        }}
        ```


    - **User:** `"Shan e nuzul of the verse in Surah Al-Falaq which mentions harm caused by created things."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_englishName": "Al-Falaq",
                    "query": "Harm caused by created things"
                }}
            ]
        }}
        ```


    - **User:** `"Shan e nuzul of verses 1-10 of Surah Al-An'am."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_englishName": "Al-An'am",
                    "verse_number_min": 1,
                    "verse_number_max": 10
                }}
            ]
        }}
        ```


    ### 2. Search_Quran_By_filters
    Use this to search through Quranic data when the user provides exact metadata filters, such as:
    - Surah name (Arabic or English)
    - Surah number
    - Ayah number (global or within surah)
    - Juz, Ruku, Manzil, Hizb, Sajdah, etc.


    #### Example Queries
    1. What is verse number 5 of Surah Al-Fatiha?
    2. What is verse number 5 of the Quran?
    3. What does Surah Al-Fatiha, verse 5, say about guidance and worshipping Allah?
    4. Is verse 128 of Surah Al-Baqarah a sajdah verse?
    5. Give me the translation of verse 13 of Surah Al-An'am and verse 50 of Al-Baqarah.


    #### Important Guidelines
    1. When calling `Search_Quran_By_filters`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.
    2. Do **not** infer metadata such as Juz, Ruku, Hizb, total ayahs, or revelation type.
    3. If the user provides only surah and ayah numbers → pass **only those fields**.


    #### Examples of Tool Calls for Search_Quran_By_filters


    - **User:** `"What is verse 5 of Surah Al-Fatiha?"`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-Faatiha"
                    }},
                    "verse_args": {{
                        "numberInSurah": 5
                    }}
                }}
            ]
        }}
        ```


    - **User:** `"Is verse 128 of Surah Al-Baqarah a sajdah verse?"`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-Baqarah"
                    }},
                    "verse_args": {{
                        "numberInSurah": 128,
                        "sajdah": true
                    }}
                }}
            ]
        }}
        ```


    - **User:** `"Give me verse 13 of Surah Al-An'am and verse 50 of Al-Baqarah."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-An'am"
                    }},
                    "verse_args": {{
                        "numberInSurah": 13
                    }}
                }},
                {{
                    "surah_args": {{
                        "englishName": "Al-Baqarah"
                    }},
                    "verse_args": {{
                        "numberInSurah": 50
                    }}
                }}
            ]
        }}
        ```


    ### 3. get_Quran_Audio
    Use this to search through Quranic data when the user wants to listen to/play Quranic recitation and provides exact metadata filters, such as:
    - Surah name (Arabic or English)
    - Surah number
    - Ayah number (global or within surah)
    - Juz, Ruku, Manzil, Hizb, Sajdah, etc.


    #### Example Queries
    1. I want to listen to verse number 5 of Surah Al-Fatiha.
    2. Play verse number 5 of the Quran.
    3. Play a sajdah verse for me.
    4. Play the audio of verse 13 of Surah Al-An'am and verse 50 of Al-Baqarah.
    5. I want to listen to the recitation of verse 5 of Surah Al-Baqarah, verse 9 of Surah Al-An'am, and verse 10 of Surah An-Nisa.
    6. I want to listen to verses 1-10 of Surah Al-Baqarah, Surah Quraysh, and Surah Bani Israel.


    #### Important Guidelines
    1. When calling `get_Quran_Audio`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.
    2. Do **not** infer metadata such as Juz, Ruku, Hizb, total ayahs, or revelation type.
    3. If the user provides only surah and ayah numbers → pass **only those fields**.

    #### Examples of Tool Calls for get_Quran_Audio


    - **User:** `"I want to listen to verse number 5 of Surah Al-Fatiha."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-Faatiha"
                    }},
                    "verse_args": {{
                        "numberInSurah": 5,
                        "limit": 1
                    }}
                }}
            ]
        }}
        ```


    - **User:** `"Play verse 128 of Surah Al-Baqarah for me by reciter Muhammad Jibreel."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-Baqarah"
                    }},
                    "verse_args": {{
                        "numberInSurah": 128,
                        "limit": 1
                    }}
                }}
            ],
            "reciter": "muhammadjibreel"
        }}
        ```


    - **User:** `"I want to listen to verses 13-16 of Surah Al-An'am and verses 50-54 of Al-Baqarah by reciter Husary."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-An'am"
                    }},
                    "verse_args": {{
                        "numberInSurah_min": 13,
                        "numberInSurah_max": 16,
                        "limit": 4
                    }}
                }},
                {{
                    "surah_args": {{
                        "englishName": "Al-Baqarah"
                    }},
                    "verse_args": {{
                        "numberInSurah_min": 50,
                        "numberInSurah_max": 54,
                        "limit": 5
                    }}
                }}
            ],
            "reciter": "husary"
        }}
        ```

    - **User:** `"I want to listen to any verse in Juz 5."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "verse_args": {{
                        "juz": 5,
                        "limit": 1
                    }}
                }}
            ]
        }}
        ```


    ### 4. get_verse_image
    Use this to search through Quranic data when the user wants to read/recite Quranic verses and provides exact metadata filters, such as:
    - Surah name (Arabic or English)
    - Surah number
    - Ayah number (global or within surah)
    - Juz, Ruku, Manzil, Hizb, Sajdah, etc.


    #### Example Queries
    1. I want to read verse number 5 of Surah Al-Fatiha.
    2. Show me verse number 5 of the Quran.
    3. I want to read the Quran.
    4. I want to read verse 13 of Surah Al-Baqarah and verse 50 of Surah Yusuf.
    5. I want to recite verse 5 of Surah Al-Falaq, verse 9 of Surah Al-An'am, and verse 10 of Surah Ar-Ra'd.
    6. I want to recite verses 1-10 of Surah An-Nisa, Surah An-Nur, and Surah Muhammad.


    #### Important Guidelines
    1. When calling `get_verse_image`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.
    2. Do **not** infer metadata such as Juz, Ruku, Hizb, total ayahs, or revelation type.
    3. If the user provides only surah and ayah numbers → pass **only those fields**.

    #### Examples of Tool Calls for get_verse_image


    - **User:** `"I want to recite Surah Al-Fatiha, verse 7."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-Faatiha"
                    }},
                    "verse_args": {{
                        "numberInSurah": 7,
                        "limit": 1
                    }}
                }}
            ]
        }}
        ```


    - **User:** `"Show me verse 8 of Surah An-Nisa."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "An-Nisaa"
                    }},
                    "verse_args": {{
                        "numberInSurah": 8,
                        "limit": 1
                    }}
                }}
            ]
        }}
        ```


    - **User:** `"I am feeling miserable; I want to read a calming verse."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "verse_args": {{
                        "juz": 30,
                        "limit": 1
                    }}
                }}
            ]
        }}
        ```


    - **User:** `"Recite verses 10 to 15 of Surah Al-Baqarah."`
        **Tool call:**
        ```json
        {{
            "args": [
                {{
                    "surah_args": {{
                        "englishName": "Al-Baqarah"
                    }},
                    "verse_args": {{
                        "numberInSurah_min": 10,
                        "numberInSurah_max": 15,
                        "limit": 6
                    }}
                }}
            ]
        }}
        ```


    ## IMPORTANT DISTINCTION BETWEEN `Search_Quran_By_filters` and `get_verse_image`
    Both tools can retrieve Quranic verses. The `get_verse_image` tool is to be called when the user wants to recite and read a Verse, Surah, or part of the Quran. Meanwhile, the `Search_Quran_By_filters` tool is to be called when the user wants any verse, surah, or part of the Quran (through user-provided filter metadata) and does **not** intend to read or recite the Quran.


    ## OUTPUT FORMATTING RULES
    1. **For Complex Queries** (stories, tafsir, comparisons, specific knowledge):
        - You MUST call the `structured_response_tool` first.
    2. **For Simple Greetings & Short Interactions** (e.g., 'hi', 'thanks', etc.):
        - Do not call the `structured_response_tool`. Instead, just reply with a polite, warm, and simple greeting, ensuring proper markdown.


    ## Content Rules (When using JSON)
    - Keep responses short, brief, and precise unless the user asks for detailed responses.
    - Use `sections` to break down long stories or explanations.
    - Use the `table` field ONLY when comparing data.
    - Keep the `intro` concise.

    ### 5. story_agent_tool
    Use this tool **ONLY** when the user explicitly requests a *story* (e.g., “tell me the story of Musa”).

    #### Example Queries
    1. "Tell me the story of Adam."
    2. "What happened to Noah's Ark?"
    3. "Explain the story of Yusuf and his brothers."


    ## PRIORITY RULE: When Uploaded Files & Context are present
    - If the user's message contains a section marked **'SYSTEM: The user has attached a file...'**, you MUST use that provided text to answer the question.

    ## EXTRA RULES FOR get_verse_image and get_Quran_Audio
    - When calling get_verse_image and get_Quran_Audio, if the tools didn't return empty or null data then DO NOT include the data (audio_links, verse images links, ruku, juz, etc) returned by these tools verbose in your response, instead just say that following is the audio data/verse images and that is ENOUGH. 

    ## Context
    Strictly use the following context and name definitions for calling tools and answering user queries.
    - `QuranMetaData`: {QuranMetaData}
    - `surah_name_english_array`: {surah_name_english_array}
    - `surah_name_english_translation_array`: {surah_name_english_translation_array}


    **Default language:** English (unless the user converses in another). 
"""

def get_agent_by_user_age( age: int , username: str, model_key: str = None ):
    """
    Returns a configured agent based on the user's age and name.
    """
    llm = get_llm(model_key)
    user_context_str = f"You are chatting with **{username}**, who is **{age} years old**."
    
    selected_template = standard_system_instructions 
    print(f"\n--- AGENT INITIALIZED: Standard Mode | User: {username}, Age: {age} | Model: {llm.model_name} ---\n")
    
    formatted_system_prompt = selected_template.format(
        QuranMetaData=QuranMetaData, 
        surah_name_english_array=surah_name_english_array,
        surah_name_english_translation_array=surah_name_english_translation_array,
        user_context=user_context_str 
    )

    tool_protection = ToolRetryMiddleware(
        max_retries=1,  
        on_failure=custom_tool_error_handler, 
        backoff_factor=1.0,
    )

    
    return create_agent(
        name="QuranTadabburAgent",
        model = llm,
        middleware = [tool_protection],
        system_prompt = formatted_system_prompt,
        tools = [Search_Quran_By_filters, searchAsbabNuzul, structured_response_tool, get_Quran_Audio, get_verse_image, story_agent_tool]
    )

main_agent = get_agent_by_user_age(age=25, username="DefaultUser")


output_formatter_llm = ChatGroq(
    name = "OutputFormatter",
    api_key = GROQ_API_KEY,
    model= "openai/gpt-oss-120b",
    temperature = 0,
)

while True:
    question = input("Please ask a question: ")
    if question!= "break":
        data_flag = [False, False]
        response = main_agent.invoke({"messages" : [{"role": "user", "content": question }]})
        messages_array = response['messages']

        # Create a new instance of OutputSchema
        response_object = OutputSchema(
            response=messages_array[-1].content,
            has_verse_audio=False,
            has_verse_image=False,
            audio_data=None,
            verse_images=None
        )
    
        for message in reversed(messages_array):
            if data_flag == [True, True]:
                break
            if isinstance(message, ToolMessage):
                if message.name == "get_verse_image" and not data_flag[0]:
                    data = json.loads(message.content)
                    verse_images = data.get("verse_images",[]) 
                    if verse_images:
                        response_object.has_verse_image = True
                        response_object.verse_images = verse_images
                    data_flag[0] = True
                elif message.name == "get_Quran_Audio" and not data_flag[1]:
                    data = json.loads(message.content)
                    audio_data = data.get("audio_data", [])
                    print("Audio data", audio_data)
                    if audio_data:
                        response_object.has_verse_audio = True
                        response_object.audio_data = audio_data
                    data_flag[1] = True
        print("response object", response_object)
    else:
        break




    # ### 1. final_tool
    # `final_tool` returns the final answer to the user in a structured format. `final_tool` MUST be called at the end of EACH user question. A response without a `final_tool` tool call is considered no response.


    # **Tool Arguments:**
    # - `response`: str (This field contains the final response to the user, whether complex or simple)
    # - `has_verse_audio`: bool (This field determines whether audio data is present in the `audio_data` field or not. `True` if present, otherwise `False`)
    # - `audio_data`: List[SurahForAudio] (This field contains the audio data in the required format if present; otherwise, it should be `null`)
    # - `has_verse_image`: bool (This field determines whether verse images are present in the `verse_images` field or not. `True` if present, otherwise `False`)
    # - `verse_images`: List[SurahForImage] (This field contains the verse image data in the required format if present; otherwise, it should be `null`)


    # #### Important Guidelines for Audio and Image Data


    # **Audio Data Handling**
    # - `has_verse_audio` = **TRUE** only when **ALL** these conditions are met:
    #     - `get_Quran_Audio` tool was called
    #     - Tool returned valid data (not `None`, not empty list)
    #     - Data contains valid Surah objects with audio URLs
    # - `has_verse_audio` = **FALSE** when **ANY** of these occur:
    #     - Tool was not called
    #     - Tool returned empty data (`[]`, `None`)
    #     - Tool returned invalid data
    # - **audio_data**:
    #     - Must contain the **EXACT** data from `get_Quran_Audio` (no modifications)
    #     - Must be set to `None` if no valid audio data exists
    #     - Response should indicate audio is available, not repeat the content


    # **Image Data Handling**
    # - [Similar structure for verse images...]


    # #### Critical Consistency Rules
    # - ✅ `has_verse_audio` = `TRUE`  ⇔  `audio_data` contains valid data
    # - ✅ `has_verse_audio` = `FALSE` ⇔  `audio_data` = `None`
    # - [Similar for images...]
    # - 🚨 ANY mismatch between `has_verse_audio` and `audio_data` is **INVALID**



# @tool(args_schema=OutputSchema)
# def final_tool(response: str, has_verse_audio: bool, audio_data: Optional[List[SurahForAudio]],has_verse_image: bool,verse_images: Optional[List[SurahForImage]] ):
#     """This tool converts the assistant's response to the following format before returning to the user:
#     ##FORMAT##
#     - response:str
#     - has_verse_audio: bool
#     - audio_data: Optional[List[SurahForAudio]]
#     - has_verse_image: bool
#     - verse_images: Optional[List[SurahForImage]]

#     This tool is called each time before returning a response to user 
#     """
#     result = {
#     "response": response,
#     "has_verse_audio": has_verse_audio,
#     "audio_data": audio_data,
#     "has_verse_image": has_verse_image,
#     "verse_images": verse_images,
#     }
#     print(result)  # optional debug
#     return result
