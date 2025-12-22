import asyncio
import json
import os
from agents import (
    Agent, ModelSettings, OpenAIChatCompletionsModel, 
    RunConfig, Runner, GuardrailFunctionOutput,
    RunContextWrapper, TResponseInputItem, function_tool, input_guardrail
)
from agents import output_guardrail, GuardrailFunctionOutput
from openai import AsyncOpenAI
from typing import Optional
# from tafseer_agent import Tafsir_Agent
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from agents import function_tool
from openai import OpenAI
from langchain_groq import ChatGroq
from langchain.agents import create_agent
# Load environment variables

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')
load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

# Initialize Fireworks client
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

# # Load Quran dataset context
# df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")
# context = [
#     "\n".join(df["ayah_en"].astype(str)),
#     "\n".join(df["ayah_ar"].astype(str)),
#     "\n".join(df["surah_no"].astype(str)),
#     "\n".join(df["surah_name_en"].astype(str)),
# ]

# Load example story for narrative style
with open("story_exmp.txt", "r", encoding="utf-8") as f:
    story_example = json.load(f)

# # ===================== SEMANTIC SEARCH TOOL =====================
# @function_tool
# async def Get_Specific_Verse(
#     surah_number: int,
#     verse_number: int
# ) -> str:
#     """
#     Get a specific verse by exact surah and verse number.
    
#     Use this when user asks for a specific verse like:
#     - "Show me verse 2:90"
#     - "What is Surah Baqarah ayah 255?"
#     - "Get me 18:10"
    
#     Args:
#         surah_number: Surah number (1-114)
#         verse_number: Verse number within that surah
    
#     Returns:
#         The exact verse with Arabic and English translation
#     """
#     try:
#         print(f"🎯 Fetching exact verse: {surah_number}:{verse_number}")
        
#         # Scroll through all points to find exact match
#         all_points = []
#         offset = None
        
#         while True:
#             scroll_result = qdrant.scroll(
#                 collection_name=COLLECTION_NAME,
#                 limit=100,
#                 offset=offset,
#                 with_payload=True,
#                 with_vectors=False  
#             )
#             points, next_offset = scroll_result
#             all_points.extend(points)
            
#             if next_offset is None:
#                 break
#             offset = next_offset
        
#         # Find exact match
#         for point in all_points:
#             p = point.payload
#             if p.get('surah_no') == surah_number and p.get('ayah_no_surah') == verse_number:
#                 verse_key = p.get('verse_key', f"{surah_number}:{verse_number}")
#                 surah_name = p.get('surah_name_en', 'Unknown Surah')
                
#                 result = (
#                     f"**Surah {surah_name} ({verse_key})**\n\n"
#                     f"🕌 **Arabic:**\n{p['ayah_ar']}\n\n"
#                     f"📖 **English Translation:**\n{p['ayah_en']}\n\n"
#                     f"📍 **Details:**\n"
#                     f"- Juz: {p.get('juz_no', 'N/A')}\n"
#                     f"- Revelation: {p.get('place_of_revelation', 'N/A')}\n"
#                 )
                
#                 if p.get('sajdah'):
#                     result += "- Contains Sajdah (prostration) ⭐\n"
                
#                 print(f"✅ Found verse {verse_key}")
#                 return result
        
#         # Not found
#         return f"❌ Verse {surah_number}:{verse_number} not found in the database. Please check the verse reference."
    
#     except Exception as e:
#         print(f"❌ Error fetching verse: {e}")
#         import traceback
#         traceback.print_exc()
#         return f"Error retrieving verse: {str(e)}"

# @function_tool
# async def Quran_Semantic_Search(
#     query: str,
#     limit: int = 5,
#     min_score: float = 0.2
# ) -> str:
#     """
#     Search the Quran by semantic meaning (works with Arabic, English, or mixed queries).
#     """
#     try:
#         print(f"🔍 Searching Quran for: '{query}'")
        
#         # Generate embedding for the query
#         emb_response = embed_client.embeddings.create(
#             model=EMBEDDING_MODEL,
#             input=query
#         )
#         query_embedding = emb_response.data[0].embedding
#         print(f"✅ Embedding generated: {len(query_embedding)} dimensions")
        
#         # Check collection
#         collection_info = qdrant.get_collection(COLLECTION_NAME)
#         print(f"📦 Collection: {collection_info.points_count} points")
        
#         # Use scroll + manual search (works with old client)
#         print(f"🔄 Retrieving all points for search...")
        
#         import numpy as np
        
#         # Get all points with vectors
#         all_points = []
#         offset = None
        
#         while True:
#             scroll_result = qdrant.scroll(
#                 collection_name=COLLECTION_NAME,
#                 limit=100,  # Batch size
#                 offset=offset,
#                 with_payload=True,
#                 with_vectors=True
#             )
#             points, next_offset = scroll_result
#             all_points.extend(points)
            
#             if next_offset is None:
#                 break
#             offset = next_offset
        
#         print(f"📥 Retrieved {len(all_points)} points")
        
#         # Manual cosine similarity calculation
#         query_vec = np.array(query_embedding)
#         query_norm = np.linalg.norm(query_vec)
        
#         scored_results = []
#         for point in all_points:
#             point_vec = np.array(point.vector)
#             point_norm = np.linalg.norm(point_vec)
            
#             # Cosine similarity: dot product / (norm1 * norm2)
#             similarity = np.dot(query_vec, point_vec) / (query_norm * point_norm)
            
#             if similarity >= min_score:
#                 scored_results.append({
#                     'payload': point.payload,
#                     'score': float(similarity)
#                 })
        
#         # Sort by score descending
#         scored_results.sort(key=lambda x: x['score'], reverse=True)
        
#         # Take top N results
#         results = scored_results[:limit]
        
#         print(f"✅ Found {len(results)} results above threshold {min_score}")
        
#         if not results:
#             # Try without threshold to see best match
#             if scored_results:
#                 best_score = scored_results[0]['score']
#                 print(f"🧪 Best match score: {best_score:.3f} (below threshold)")
#             return f"No verses found above {min_score:.0%} similarity. Try:\n- Different keywords\n- More specific query\n- Lower the threshold"

#         # Format results
#         verses_output = []
#         for idx, hit in enumerate(results, 1):
#             p = hit['payload']
#             verse_key = p.get('verse_key', f"{p['surah_no']}:{p['ayah_no_surah']}")
#             surah_name = p.get('surah_name_en', 'Unknown Surah')
            
#             verse_text = (
#                 f"{idx}. **Surah {surah_name} ({verse_key})** — Relevance: {hit['score']:.2%}\n"
#                 f"   🕌 Arabic: {p['ayah_ar']}\n"
#                 f"   📖 English: {p['ayah_en']}\n"
#             )
#             verses_output.append(verse_text)

#         # header = f"Found {len(verses_output)} relevant verse(s) for: '{query}'\n\n"
#         # return header + "\n".join(verses_output)
    
#         # After the search completes in Quran_Semantic_Search
#         header = f"Found {len(verses_output)} relevant verse(s) for: '{query}'\n\n"
#         result = header + "\n".join(verses_output)
#         print(f"📤 Returning to agent: {result[:200]}...")  # Print first 200 chars
#         return result
    
#     except Exception as e:
#         print(f"❌ Search error: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return f"Search temporarily unavailable. Error: {str(e)}"
    
# @function_tool
# async def Get_Surah_Info(
#     surah_number: int
# ) -> str:
#     """
#     Get information about a complete Surah (chapter).
    
#     Use this when user asks about a Surah in general:
#     - "What juz is Surah Baqarah in?"
#     - "Tell me about Surah Al-Kahf"
#     - "How many verses in Surah Yasin?"
    
#     Args:
#         surah_number: Surah number (1-114)
    
#     Returns:
#         Complete information about the Surah
#     """
#     try:
#         print(f"📚 Fetching info for Surah {surah_number}")
        
#         # Get all verses from this Surah
#         all_points = []
#         offset = None
        
#         while True:
#             scroll_result = qdrant.scroll(
#                 collection_name=COLLECTION_NAME,
#                 limit=100,
#                 offset=offset,
#                 with_payload=True,
#                 with_vectors=False
#             )
#             points, next_offset = scroll_result
#             all_points.extend(points)
            
#             if next_offset is None:
#                 break
#             offset = next_offset
        
#         # Filter for this specific surah
#         surah_verses = [
#             point.payload for point in all_points 
#             if point.payload.get('surah_no') == surah_number
#         ]
        
#         if not surah_verses:
#             return f"❌ Surah {surah_number} not found in the database."
        
#         # Extract info from first verse
#         first_verse = surah_verses[0]
#         surah_name_en = first_verse.get('surah_name_en', 'Unknown')
#         surah_name_ar = first_verse.get('surah_name_ar', '')
#         surah_name_roman = first_verse.get('surah_name_roman', '')
#         revelation = first_verse.get('place_of_revelation', 'Unknown')
        
#         # Calculate statistics
#         total_verses = len(surah_verses)
#         juz_numbers = sorted(set(v.get('juz_no') for v in surah_verses if v.get('juz_no')))
#         has_sajdah = any(v.get('sajdah', False) for v in surah_verses)
        
#         # Format Juz range
#         if len(juz_numbers) == 1:
#             juz_info = f"Juz {juz_numbers[0]}"
#         else:
#             juz_info = f"Juz {juz_numbers[0]} to Juz {juz_numbers[-1]}"
        
#         result = (
#             f"**Surah {surah_number}: {surah_name_en}**\n"
#             f"Arabic: {surah_name_ar}\n"
#             f"Romanized: {surah_name_roman}\n\n"
#             f"📊 **Statistics:**\n"
#             f"- Total Verses: {total_verses}\n"
#             f"- Location: {juz_info}\n"
#             f"- Revelation: {revelation}\n"
#         )
        
#         if has_sajdah:
#             result += "- Contains Sajdah (prostration) ⭐\n"
        
#         print(f"✅ Found Surah info: {surah_name_en}")
#         return result
    
#     except Exception as e:
#         print(f"❌ Error fetching Surah info: {e}")
#         import traceback
#         traceback.print_exc()
#         return f"Error retrieving Surah info: {str(e)}"

# # @function_tool
# # async def tafseer(ayah_reference: str) -> str:
# #     print(f"Fetching tafseer for ayah reference: {ayah_reference}")
# #     """
# #     Fetches the tafseer for a given Quranic ayah reference using the Tafsir_Agent.

# #     Args:
# #         ayah_reference (str): The reference of the ayah (e.g., "2:25").

# #     Returns:
# #         str: The tafseer content for the specified ayah.
# #     """
# #     result = await Runner.run(
# #         Tafsir_Agent,
# #         ayah_reference,
# #         run_config=config
# #     )
# #     print(f"Tafseer fetched for {ayah_reference}: {result.final_output}")
# #     return str(result.final_output)

# 🧠 Guardrail Agent — checks semantic relevance
guardrail_agent = Agent(
    name="Guardrail check",
    instructions=(
        "Determine whether the user's request is semantically related to the provided Quranic dataset "
        "and its themes (moral lessons, reflection, faith, spirituality, prophets, divine guidance, etc.). "
        "If it’s unrelated to these themes or doesn’t use the Quranic context meaningfully, respond with 'UNRELATED'. "
        "Otherwise, respond with 'RELATED'."
    )
)

# --- CONTEXT FOR INPUT GUARDRAIL AGENT ---
quran_topics = """
The Quran discusses faith, worship, moral values, patience, guidance, repentance,
justice, stories of prophets, creation, the afterlife, and reflections on life, islamic history and
spiritual growth. It does not cover math, technology, or unrelated worldly knowledge.
"""

# 💬 Fallback Agent — responds gracefully to off-topic queries
fallback_agent = Agent(
    name="FallbackResponder",
    instructions=(
        "You are a polite assistant."
        f"If a user says something unrelated to the Quran topics like {quran_topics} reply politely and warmly that you cant reply to topics related to maths, technology etc but if you are greeted then greet back and tell who you are and what can the user ask you, "
        "gently remind them that you can only create Quran inspired moral stories."
    )
)

# 🛡️ Input Guardrail — uses semantic judgment instead of keyword matching
@input_guardrail
async def quran_input_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    print("Running QuranStory input guardrail...")
    """Checks if the input question is Quranic-stories"""
        # Extract the model selected by the user (passed via context from main.py)
    current_model_key = getattr(ctx.context, "model_key", "gpt-oss-20b")

    # Build a RunConfig with the SAME model the user chose
    guardrail_config = get_model_config(current_model_key)

    result = await Runner.run(guardrail_agent, input,run_config=guardrail_config, context=ctx.context)
    decision = str(result.final_output).strip().upper()
    print(decision)

    if "UNRELATED" in decision:
        # Graceful fallback: no error, just redirect
        fallback = await Runner.run(fallback_agent, "This seems unrelated to Quranic story telling",run_config=guardrail_config, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=fallback.final_output,
            tripwire_triggered=True  # tripwire signals fallback, not failure
        )

    return GuardrailFunctionOutput(
        output_info="Input is relevant to Quranic storytelling.",
        tripwire_triggered=False
    )

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

# story_agent = Agent(
#     name="QuranStoryTeller",
#     instructions=(
#         "You are Tadabbur, a storytelling assistant inspired by the Quran. "
#         f"Always craft short, emotionally engaging stories "
#         "that teach moral lessons from Quranic verses. "
#         "Your stories should be engaging and like this example:\n\n"
#         f"{story_example}\n\n"
#         "the final answer should be in a story format for users to read and not in json form. "
#         "Always stay relevant to the Quranic moral and narrative context."
#     ),
#     model=config.model,
#     # tools=[
#     #     Get_Specific_Verse,
#     #     Quran_Semantic_Search,
#     #     Get_Surah_Info,
#     # ],
#     model_settings=ModelSettings(temperature=0.7, max_turns=2),
#     # input_guardrails=[quran_input_guardrail],
#     # output_guardrails=[story_output_guardrail],
# )




        