import os
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner, AsyncOpenAI, GuardrailFunctionOutput, RunContextWrapper, TResponseInputItem, input_guardrail, output_guardrail
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
# from story_agent import story_agent
# from tafseer_agent import Tafsir_Agent
# from context_agent import contextAgent
from tools.search_Quran_By_Filters import Search_Quran_By_filters
from tools.searchAsbabNuzul import searchAsbabNuzul
from data.data import QuranMetaData, surah_name_english_array,surah_name_english_translation_array
import pandas as pd
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_fireworks import ChatFireworks
from langchain.agents import create_agent
from openai import OpenAI

load_dotenv()

embed_client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1"
)

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')
# FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY')
COLLECTION_NAME = "Quran-Dataset-Collection"
EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

external_client = AsyncOpenAI(
    api_key=FIREWORKS_API_KEY,
    base_url="https://api.fireworks.ai/inference/v1"
)

SUPPORTED_MODELS = {
    "kimi-k2-instruct-0905": {
        "model_id": "accounts/fireworks/models/kimi-k2-instruct-0905",
        "provider": external_client,
        "name": "Kimi K2 Instruct 0905"
    },
    "deepseek-v3p1-terminus": {
        "model_id": "accounts/fireworks/models/deepseek-v3p1-terminus",
        "provider": external_client,
        "name": "DeepSeek V3.1 Terminus"
    },
    "gpt-oss-120b": {
        "model_id": "accounts/fireworks/models/gpt-oss-120b",
        "provider": external_client,
        "name": "OpenAI GPT-OSS 120B"
    },
    "gpt-oss-20b": {  # your current default
        "model_id": "accounts/fireworks/models/gpt-oss-20b",
        "provider": external_client,
        "name": "OpenAI GPT-OSS 20B"
    },
    "qwen3-235b-a22b-instruct": {  # your current default
        "model_id": "accounts/fireworks/models/qwen3-235b-a22b-instruct",
        "provider": external_client,
        "name": "Qwen3 235B a22B Instruct"
    }
}

def get_model_config(model_key: Optional[str] = None) -> RunConfig:
    """
    Returns a RunConfig with the selected model.
    Falls back to default 'gpt-oss-20b' if invalid or None.
    """
    if not model_key or model_key not in SUPPORTED_MODELS:
        model_key = "gpt-oss-20b"  # fallback

    info = SUPPORTED_MODELS[model_key]

    selected_model = OpenAIChatCompletionsModel(
        model=info["model_id"],
        openai_client=info.get("provider") or external_client
    )

    return RunConfig(
        model=selected_model,
        model_provider=info.get("provider") or external_client,
        tracing_disabled=True
    )

# config as default (for backward compatibility)
config = get_model_config("gpt-oss-20b") 

# model = OpenAIChatCompletionsModel(
#     model="accounts/fireworks/models/gpt-oss-20b", 
#     openai_client=external_client
# )

# config = RunConfig(
#     model=model,
#     model_provider=external_client,
#     tracing_disabled=True
# )

# # # Quran dataset
# # df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")
# # ct1 = "\n".join(df["ayah_en"].astype(str))
# # ct2 = "\n".join(df["ayah_ar"].astype(str))
# # ct3 = "\n".join(df["surah_no"].astype(str))
# # ct4= "\n".join(df["surah_name_en"].astype(str))
# # context = [ct1, ct2, ct3, ct4]





# --- CONTEXT FOR INPUT GUARDRAIL AGENT ---
quran_topics = """
The Quran discusses faith, worship, moral values, patience, guidance, repentance,
justice, stories of prophets, creation, the afterlife, and reflections on life, islamic history and
spiritual growth. It does not cover math, technology, or unrelated worldly knowledge.
"""

guardrail_agent = Agent( 
    name="Guardrail check",
    # instructions=f'Check if the user is asking you about data related to the {context} you are provided with.'
    # f"If its unrelated to the Quranic {context} meaningfully, respond with 'UNRELATED'."
    # "Otherwise, respond with 'RELATED'.",
    instructions=(
        "Your task is to decide whether the user’s question is related to Quranic knowledge. "
        "If it’s about verses, tafsir, meaning, translation, reflection, or anything spiritually relevant, "
        "respond only with 'RELATED'. "
        "If it’s about unrelated topics such as math, science, entertainment, coding, or general trivia, "
        "respond only with 'UNRELATED'. "
        f"Context summary:\n{quran_topics}" 
        )
)

fallback_agent = Agent(
    name="FallbackResponder",
    instructions=(
        "You are Tadabbur your friendly Quran companion. "
        f"If a user says something unrelated to the Quran topics like {quran_topics} reply politely and warmly that you cant reply to topics related to maths, technology etc but if you are greeted then greet back and tell who you are and what can the user ask you, "
        "'Hi there! Im Tadabbur — I specialize in Quranic insights. What would you like to explore today?'"
    )
)

@input_guardrail
async def quran_input_guardrail( 
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    print("Running Quran input guardrail...")
    """Checks if the input question is Quranic-related"""

    # Extract the model selected by the user (passed via context from main.py)
    current_model_key = getattr(ctx.context, "model_key", "gpt-oss-20b")

    # Build a RunConfig with the SAME model the user chose
    guardrail_config = get_model_config(current_model_key)

    result = await Runner.run(guardrail_agent, input,run_config=guardrail_config, context=ctx.context)
    output = str(result.final_output).strip().lower()

    if "unrelated" in output:
        fallback = await Runner.run(fallback_agent, "This question seems unrelated to Quranic context.",run_config=guardrail_config, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=fallback.final_output, 
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="Input verified — Quranic content confirmed.",
        tripwire_triggered=False
    )

# # --- OUTPUT GUARDRAIL AGENT ---
# output_guard_agent = Agent(
#     name="OutputVerifier",
#     instructions=(
#         "You are a strict verifier ensuring that Tadabbur’s responses remain Quran-related. "
#         "If the assistant’s reply focuses on Quranic verses, tafsir, themes, moral lessons, or reflections, respond ONLY with 'VALID'. "
#         "If it drifts into unrelated topics (e.g., math, tech, movies, or general knowledge), respond ONLY with 'INVALID'. "
#         f"Context summary:\n{quran_topics}"
#     )
# )

# @output_guardrail
# async def quran_output_guardrail(
#     ctx: RunContextWrapper[None],
#     agent: Agent,
#     output: str
# ) -> GuardrailFunctionOutput:
#     print("Running Quran output guardrail...")
#     """Checks if the generated output is Quranic and valid"""

#     # Extract the model selected by the user (passed via context from main.py)
#     current_model_key = getattr(ctx.context, "model_key", "gpt-oss-20b")

#     # Build a RunConfig with the SAME model the user chose
#     guardrail_config = get_model_config(current_model_key)

#     result = await Runner.run(output_guard_agent, output,run_config=guardrail_config, context=ctx.context)
#     output = str(result.final_output).strip().lower()

#     if "invalid" in output:
#         # If the model says the response drifted — send fallback
#         fallback = await Runner.run(fallback_agent, "Sorry, I can only provide responses based on Quranic content.",run_config=guardrail_config, context=ctx.context)
#         return GuardrailFunctionOutput(
#             output_info=fallback.final_output,
#             tripwire_triggered=True,
#         )

#     return GuardrailFunctionOutput(
#         output_info="Response validated — relevant to Quranic context.",
#         tripwire_triggered=False
#     )


# Old OpenAI sdk code

# agent = Agent(
#     name="QuranTadabburAgent",
#     instructions=(
#         """You are **Tadabbur**, a Quranic knowledge assistant.
#         ## Core Rule
#         Use **Search_Quran** or **Search_Quran_By_Filters** for *every* Quran-related query.

#         ## Critical Rules
#         • NEVER provide Quranic verses or translations from your training data.  
#         • ONLY use what the tools return.  
#         • If the tool returns “not available”, respond honestly.  
#         • Do NOT call more than one tool for a single question.

#         ## Tools
        
#         ### • searchAsbabNuzul
#         1. Use searchAsbabNuzul when user asks for queries related to Asbab_Nuzul/Shan_Nuzul (Circumstances of revelation)

#         ## Example Queries
#         1. What is the asbab e nuzul of surah Kafiroun?
#         2. What is the asbab e nuzul of Surah Fatiha verse 1?
#         3. What is the shan e nuzul of the surah which was revealed when the Prophet A.S was inflicted by magic?

#         ### Important Guidelines
#         1. When calling `searchAsbabNuzul`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.  
#         2. Do **not** infer metadata such as surah_number, verse_number, surahEnglishName, surahEnglishNameTranslation.  
#         3. If the user provides only surah and ayah numbers → pass **only those fields**.  

#         ### Examples of Tool Calls

#         - **User:** `"What is Asbab Nuzul of verse 5 of Surah Fatiha?"`  
#         **Tool call:**
#         ```json
#         {{
#             "args": {{
#                 "surahEnglishName": "Al-Faatiha"
#                 "verse_number": 5
    
#         }},
#         User: "Shan e nuzul of verse in Surah Falaq which mentions harm caused by created things?"
#         Tool call:

#         {{
#             "args": {{
#                 "englishName": "Al-Falaq"
#                 "query": "Harm caused by created things",
#             }}
#         }},


#         ### • Quran_Search_By_Semantics
#         Use ONLY when the user asks queries related to Asbab Nuzul (circumstances of the revelation) and Tafseer*  
#         (e.g., “give me tafsir of Surah Ikhlas”, "what was the Shan e Nuzul of Surah Ikhlas").

#         ### • Search_Quran_By_Filters
#         Use this when the user provides exact metadata filters, such as:  
#         - Surah name (Arabic or English)  
#         - Surah number  
#         - Ayah number (global or within surah)  
#         - Juz, Ruku, Manzil, Hizb, Sajdah, etc.

#         ### Example Queries
#         1. What is verse number 5 of Surah Fatiha?  
#         2. What is the verse number 5 of Al-Quran?  
#         3. What does Surah Fatiha verse 5 say about guidance and worshipping Allah?  
#         4. Is verse 128 of Surah Baqarah a sajdah verse?  
#         5. Give me the translation of verse 13 of Surah An’aam and verse 50 of Al-Baqarah.

#         ### Important Guidelines
#         1. When calling `Search_Quran_By_filters`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.  
#         2. Do **not** infer metadata such as Juz, Ruku, Hizb, total ayahs, or revelation type.  
#         3. If the user provides only surah and ayah numbers → pass **only those fields**.  

#         ### Examples of Tool Calls

#         - **User:** `"What is verse 5 of Surah Fatiha?"`  
#         **Tool call:**
#         ```json
#         {{
#             "surah_args": {{
#                 "englishName": "Al-Faatiha"
#             }},
#             "verse_args": {{
#                 "numberInSurah": 5
#             }}
#         }},
#         User: "Is verse 128 of Surah Baqarah a sajdah verse?"
#         Tool call:

#         {{
#             "surah_args": {{
#                 "englishName": "Al-Baqarah"
#             }}                                                      ,
#             "verse_args": {{
#                 "numberInSurah": 128,
#                 "sajdah": true
#             }}
#         }},
#         User: "Give me verse 13 of Surah An’aam and verse 50 of Al-Baqarah"
#         Tool call:

#         [
#             {{
#                 "surah_args": {{"englishName": "Al-An'am"}},
#                 "verse_args": {{"numberInSurah": 13}}
#             }},
#             {{
#                 "surah_args": {{"englishName": "Al-Baqarah"}},
#                 "verse_args": {{"numberInSurah": 50}}
#             }}
#         ]

#         ### • Quran_Story_Teller
#         Use ONLY when the user explicitly requests a *story*  
#         (e.g., “tell me the story of Musa”).

#         ## Tool Usage Constraint
#         You may call tools at most 2 times per user query. 
#         If you reach the limit, stop and respond: 
#         "I am unable to make further tool calls for this request."

#         ### • Context
#         Strictly use the following context and name definitions for calling tools and answering user queries.
#         - QuranMetaData: {QuranMetaData}
#         - surah_name_english_array: {surah_name_english_array}
#         - surah_name_english_translation_array: {surah_name_english_translation_array}
#         ## Greetings
#         For simple greetings (hi, hello, salam), respond warmly and naturally **without** calling any tools.

#         **Default language:** English (unless the user requests another)."""
#     ).format(
#         QuranMetaData=QuranMetaData, 
#         surah_name_english_array=surah_name_english_array, 
#         surah_name_english_translation_array = surah_name_english_translation_array),
#     model_settings=ModelSettings(
#         temperature=0.1,
#         parallel_tool_calls=False,
#         tool_choice="required",
#         max_tokens=1500 
#     ),
#     model=config.model,
#     # input_guardrails=[quran_input_guardrail],
#     # output_guardrails=[quran_output_guardrail],
#     tools=[
#         searchAsbabNuzul,
#         Search_Quran_By_filters,
#         Quran_Search_By_Semantics,
#         story_agent.as_tool(
#             tool_name="Quran_Story_Teller",
#             tool_description="Use when the user ask about stories related to Quran, Prophets and islam"
#         ),
#         Tafsir_Agent.as_tool(
#             tool_name="Quranic_Tafsir_Agent",
#             tool_description="Use when the user ask about tafseer related to Quranic ayah or verses"
#         )
#     ],
# )


system_instructions = """
You are **Tadabbur**, a Quranic knowledge assistant.
        ## Core Rule
        Use **Search_Quran** or **Search_Quran_By_Filters** for *every* Quran-related query.

        ## Critical Rules
        • NEVER provide Quranic verses or translations from your training data.  
        • ONLY use what the tools return.  
        • If the tool returns “not available”, respond honestly.  
        • Do NOT call more than one tool for a single question.
        • NEVER leave responses empty after tool calls. Whatever tool returns, format beautifully and respond to the user in proper natural language.

        ## Tools
        
        ### • searchAsbabNuzul
        1. Use searchAsbabNuzul when user asks for queries related to Asbab_Nuzul/Shan_Nuzul (Circumstances of revelation). Use it for searching through user provided references like surah name, verse number, etc as well as doing semantic searches by forming a query, dervied from user's question or query.

        ## Example Queries
        1. What is the asbab e nuzul of surah Kafiroun?
        2. What is the asbab e nuzul of Surah Fatiha verse 1?
        3. What is the shan e nuzul of the surah which was revealed when the Prophet A.S was inflicted by magic?

        ### Important Guidelines
        1. When calling `searchAsbabNuzul`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.  
        2. Do **not** infer metadata such as surah_number, verse_number, surahEnglishName, surahEnglishNameTranslation.  
        3. If the user provides only surah and ayah numbers → pass **only those fields**.  

        ### Examples of Tool Calls

        - **User:** `"What is Asbab Nuzul of verse 5 of Surah Fatiha?"`  
        **Tool call:**
        ```json
        {{
            "args": {{
                "surah_number": 1,
                "surah_englishName": "Al-Faatiha",
                "verse_number": 5
            }}
            
        }},

        User: "Shan e nuzul of verse in Surah Falaq which mentions harm caused by created things?"
        Tool call:

        {{
            "args": {{
                "surah_englishName": "Al-Falaq"
            }},
            "query": "Harm caused by created things",
        }},


        ### • Quran_Search_By_Semantics
        Use ONLY when the user asks queries related to Asbab Nuzul (circumstances of the revelation) and Tafseer*  
        (e.g., “give me tafsir of Surah Ikhlas”, "what was the Shan e Nuzul of Surah Ikhlas").

        ### • Search_Quran_By_filters
        Use this when the user provides exact metadata filters, such as:  
        - Surah name (Arabic or English)  
        - Surah number  
        - Ayah number (global or within surah)  
        - Juz, Ruku, Manzil, Hizb, Sajdah, etc.

        ### Example Queries
        1. What is verse number 5 of Surah Fatiha?  
        2. What is the verse number 5 of Al-Quran?  
        3. What does Surah Fatiha verse 5 say about guidance and worshipping Allah?  
        4. Is verse 128 of Surah Baqarah a sajdah verse?  
        5. Give me the translation of verse 13 of Surah An’aam and verse 50 of Al-Baqarah.

        ### Important Guidelines
        1. When calling `Search_Quran_By_filters`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.  
        2. Do **not** infer metadata such as Juz, Ruku, Hizb, total ayahs, or revelation type.  
        3. If the user provides only surah and ayah numbers → pass **only those fields**.  

        ### Examples of Tool Calls

        - **User:** `"What is verse 5 of Surah Fatiha?"`  
        **Tool call:**
        ```json
        {{
            "surah_args": {{
                "englishName": "Al-Faatiha"
            }},
            "verse_args": {{
                "numberInSurah": 5
            }}
        }},
        User: "Is verse 128 of Surah Baqarah a sajdah verse?"
        Tool call:

        {{
            "surah_args": {{
                "englishName": "Al-Baqarah"
            }}                                                      ,
            "verse_args": {{
                "numberInSurah": 128,
                "sajdah": true
            }}
        }},
        User: "Give me verse 13 of Surah An’aam and verse 50 of Al-Baqarah"
        Tool call:

        [
            {{
                "surah_args": {{"englishName": "Al-An'am"}},
                "verse_args": {{"numberInSurah": 13}}
            }},
            {{
                "surah_args": {{"englishName": "Al-Baqarah"}},
                "verse_args": {{"numberInSurah": 50}}
            }}
        ]

        ### • Quran_Story_Teller
        Use ONLY when the user explicitly requests a *story*  
        (e.g., “tell me the story of Musa”).

        ## Tool Usage Constraint
        You may call tools at most 2 times per user query. 
        If you reach the limit, stop and respond: 
        "I am unable to make further tool calls for this request."

        ### • Context
        Strictly use the following context and name definitions for calling tools and answering user queries.
        - QuranMetaData: {QuranMetaData}
        - surah_name_english_array: {surah_name_english_array}
        - surah_name_english_translation_array: {surah_name_english_translation_array}
        ## Greetings
        For simple greetings (hi, hello, salam), respond warmly and naturally **without** calling any tools.

        **Default language:** English (unless the user requests another).""".format(
        QuranMetaData=QuranMetaData, 
        surah_name_english_array=surah_name_english_array, 
        surah_name_english_translation_array = surah_name_english_translation_array
)


model = ChatGroq(
    api_key = GROQ_API_KEY, 
    model = "openai/gpt-oss-120b",
    temperature = 0,
    
)

main_agent = create_agent(
    name = "QuranTadabburAgent",
    model = model,
    system_prompt = system_instructions,
    tools = [Search_Quran_By_filters, searchAsbabNuzul],
)
