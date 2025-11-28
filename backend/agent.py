from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner, AsyncOpenAI, GuardrailFunctionOutput, RunContextWrapper, TResponseInputItem, input_guardrail, output_guardrail
from story_agent import story_agent
from tafseer_agent import Tafsir_Agent
# from context_agent import contextAgent
import pandas as pd
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel
import asyncio
import os
from qdrant_client import QdrantClient
from agents import function_tool
from openai import OpenAI

load_dotenv()

# ===================== QDRANT & EMBEDDING SETUP =====================
qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)

embed_client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1"
)

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

# # Quran dataset
# df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")
# ct1 = "\n".join(df["ayah_en"].astype(str))
# ct2 = "\n".join(df["ayah_ar"].astype(str))
# ct3 = "\n".join(df["surah_no"].astype(str))
# ct4= "\n".join(df["surah_name_en"].astype(str))
# context = [ct1, ct2, ct3, ct4]

# ===================== SEMANTIC SEARCH TOOL =====================

@function_tool
async def Search_Quran(
    query: str,
    limit: int = 15
) -> str:
    """
    Universal Quran search tool that intelligently finds relevant answer for ANY query.
    
    Handles all types of requests:
    - Specific verses: "verse 2:255", "ayah 5 of Fatihah"
    - Full surahs: "Surah Fatihah translation", "complete Baqarah"
    - Topics/meanings: "verses about patience", "what Quran says about prayer"
    - Questions: "which juz is Surah Baqarah in?", "How many verses in Surah Fatihah?"
    
    Uses semantic similarity (90-92% accuracy threshold) to find the most relevant verses.
    
    Args:
        query: User's question or request (any format)
        limit: Maximum verses to return (default: 15)
    
    Returns:
        Relevant Quranic verses with Arabic, English translation, and metadata or stories using the verses found if user asks for.
    """
    try:
        print(f"🔍 Searching Quran for: '{query}'")
        
        # Retrieve all verses from database
        print(f"🔄 Loading database...")
        all_points = []
        offset = None
        
        while True:
            scroll_result = qdrant.scroll(
                collection_name=COLLECTION_NAME,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            points, next_offset = scroll_result
            all_points.extend(points)
            
            if next_offset is None:
                break
            offset = next_offset
        
        print(f"📥 Loaded {len(all_points)} verses")
        
        # Build list of available surahs
        available_surahs = {}
        for point in all_points:
            p = point.payload
            surah_no = p.get('surah_no')
            surah_name = p.get('surah_name_en', 'Unknown')
            if surah_no and surah_no not in available_surahs:
                available_surahs[surah_no] = surah_name
        
        print(f"📚 Available Surahs: {', '.join(available_surahs.values())}")
        
        # Check if requesting unavailable surah
        import re
        query_lower = query.lower()
        
        # Common surah names to check
        surah_names_map = {
            'yaseen': 36, 'yasin': 36, 'ya-seen': 36,
            'kahf': 18, 'al-kahf': 18,
            'mulk': 67, 'al-mulk': 67,
            'rahman': 55, 'ar-rahman': 55,
            'waqiah': 56, 'al-waqiah': 56,
            'ikhlas': 112, 'al-ikhlas': 112,
            'falaq': 113, 'al-falaq': 113,
            'nas': 114, 'an-nas': 114,
        }
        
        # Check for unavailable surah by name
        for name, number in surah_names_map.items():
            if name in query_lower and number not in available_surahs:
                available_list = '\n'.join([f"  • Surah {num}: {sname}" for num, sname in sorted(available_surahs.items())])
                return (
                    f"❌ **Surah {name.title()} (#{number}) is not in the database.**\n\n"
                    f"📚 **Available Surahs ({len(available_surahs)}):**\n{available_list}\n\n"
                    f"💡 The database contains {len(all_points)} verses from these surahs only."
                )
        
        # Check for unavailable surah by number (e.g., "36:5" or "surah 36")
        surah_num_match = re.search(r'\b(\d{1,3}):', query) or re.search(r'surah\s+(\d{1,3})', query_lower)
        if surah_num_match:
            requested_surah = int(surah_num_match.group(1))
            if requested_surah not in available_surahs:
                available_list = '\n'.join([f"  • Surah {num}: {sname}" for num, sname in sorted(available_surahs.items())])
                return (
                    f"❌ **Surah #{requested_surah} is not in the database.**\n\n"
                    f"📚 **Available Surahs:**\n{available_list}"
                )
        
        # Generate embedding for semantic search
        print(f"🧮 Generating embedding...")
        emb_response = embed_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        query_embedding = emb_response.data[0].embedding
        
        import numpy as np
        
        # Calculate cosine similarity for all verses
        print(f"🎯 Calculating similarity scores...")
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)
        
        scored_results = []
        for point in all_points:
            point_vec = np.array(point.vector)
            point_norm = np.linalg.norm(point_vec)
            
            # Cosine similarity (ranges from -1 to 1, we convert to 0-100%)
            similarity = np.dot(query_vec, point_vec) / (query_norm * point_norm)
            similarity_percent = (similarity + 1) / 2 * 100  # Convert to 0-100%
            
            scored_results.append({
                'payload': point.payload,
                'score': float(similarity),
                'score_percent': float(similarity_percent)
            })
        
        # Sort by similarity (highest first)
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top results
        top_results = scored_results[:limit]
        
        # Filter: Keep only results with 45%+ similarity (90%+ when normalized)
        # Cosine similarity of 0.45 ≈ 72.5% match, which is good for semantic search
        filtered_results = [r for r in top_results if r['score'] >= 0.45]
        
        if not filtered_results and top_results:
            # If strict filter gives nothing, take top 5 with lower threshold
            filtered_results = [r for r in top_results[:5] if r['score'] >= 0.20]
        
        print(f"✅ Found {len(filtered_results)} high-quality matches (threshold: 45%+ similarity)")
        
        if not filtered_results:
            available_list = '\n'.join([f"  • {sname}" for sname in available_surahs.values()])
            return (
                f"❌ No relevant verses found for: **'{query}'**\n\n"
                f"💡 **Suggestions:**\n"
                f"  • Try different keywords\n"
                f"  • Be more specific\n"
                f"  • Ask about available surahs\n\n"
                f"📚 **Available Surahs:**\n{available_list}"
            )
        
        # Format output
        verses_output = []
        current_surah = None
        
        for idx, hit in enumerate(filtered_results, 1):
            p = hit['payload']
            surah_no = p.get('surah_no')
            verse_key = p.get('verse_key', f"{surah_no}:{p.get('ayah_no_surah')}")
            surah_name = p.get('surah_name_en', 'Unknown')
            
            # Show surah header when switching to new surah
            if surah_no != current_surah:
                if current_surah is not None:
                    verses_output.append("")  # Blank line between surahs
                
                juz = p.get('juz_no', 'N/A')
                revelation = p.get('place_of_revelation', 'N/A')
                verses_output.append(
                    f"** Surah {surah_name} (#{surah_no})**\n"
                    f"Juz: {juz} | Revelation: {revelation}"
                )
                current_surah = surah_no
            
            # Format individual verse
            verse_text = (
                f"\n**{verse_key}** (Match: {hit['score']:.0%})\n"
                f" **Arabic:** {p['ayah_ar']}\n"
                f" **English:** {p['ayah_en']}"
            )
            
            # Add sajdah indicator if present
            if p.get('sajdah'):
                verse_text += "\n *Contains Sajdah (prostration)*"
            
            verses_output.append(verse_text)
        
        # Build final response
        result = "\n".join(verses_output)
        result += f"\n\n{'─' * 50}\n*Showing {len(filtered_results)} most relevant verses*"
        
        print(f" Returning {len(filtered_results)} verses")
        return result
    
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"❌ Search error: {str(e)}\n\nPlease try rephrasing your question."

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
#         print(f" Fetching exact verse: {surah_number}:{verse_number}")
        
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
#                     f"**Arabic:**\n{p['ayah_ar']}\n\n"
#                     f"**English Translation:**\n{p['ayah_en']}\n\n"
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
#         print(f" Collection: {collection_info.points_count} points")
        
#         # Use scroll + manual search (works with old client)
#         print(f" Retrieving all points for search...")
        
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
        
#         print(f" Retrieved {len(all_points)} points")
        
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
#                 print(f" Best match score: {best_score:.3f} (below threshold)")
#             return f"No verses found above {min_score:.0%} similarity. Try:\n- Different keywords\n- More specific query\n- Lower the threshold"

#         # Format results
#         verses_output = []
#         for idx, hit in enumerate(results, 1):
#             p = hit['payload']
#             verse_key = p.get('verse_key', f"{p['surah_no']}:{p['ayah_no_surah']}")
#             surah_name = p.get('surah_name_en', 'Unknown Surah')
            
#             verse_text = (
#                 f"{idx}. **Surah {surah_name} ({verse_key})** — Relevance: {hit['score']:.2%}\n"
#                 f"  Arabic: {p['ayah_ar']}\n"
#                 f"  English: {p['ayah_en']}\n"
#             )
#             verses_output.append(verse_text)

#         # header = f"Found {len(verses_output)} relevant verse(s) for: '{query}'\n\n"
#         # return header + "\n".join(verses_output)
    
#         # After the search completes in Quran_Semantic_Search
#         header = f"Found {len(verses_output)} relevant verse(s) for: '{query}'\n\n"
#         result = header + "\n".join(verses_output)
#         print(f" Returning to agent: {result[:200]}...")  # Print first 200 chars
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
#         print(f" Fetching info for Surah {surah_number}")
        
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
#             f" **Statistics:**\n"
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

# --- OUTPUT GUARDRAIL AGENT ---
output_guard_agent = Agent(
    name="OutputVerifier",
    instructions=(
        "You are a strict verifier ensuring that Tadabbur’s responses remain Quran-related. "
        "If the assistant’s reply focuses on Quranic verses, tafsir, themes, moral lessons, or reflections, respond ONLY with 'VALID'. "
        "If it drifts into unrelated topics (e.g., math, tech, movies, or general knowledge), respond ONLY with 'INVALID'. "
        f"Context summary:\n{quran_topics}"
    )
)

@output_guardrail
async def quran_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    print("Running Quran output guardrail...")
    """Checks if the generated output is Quranic and valid"""

    # Extract the model selected by the user (passed via context from main.py)
    current_model_key = getattr(ctx.context, "model_key", "gpt-oss-20b")

    # Build a RunConfig with the SAME model the user chose
    guardrail_config = get_model_config(current_model_key)

    result = await Runner.run(output_guard_agent, output,run_config=guardrail_config, context=ctx.context)
    output = str(result.final_output).strip().lower()

    if "invalid" in output:
        # If the model says the response drifted — send fallback
        fallback = await Runner.run(fallback_agent, "Sorry, I can only provide responses based on Quranic content.",run_config=guardrail_config, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=fallback.final_output,
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="Response validated — relevant to Quranic context.",
        tripwire_triggered=False
    )


agent = Agent(
    name="QuranTadabburAgent",
    instructions=(
          "You are *Tadabbur*, a Quranic knowledge assistant.\n\n"
      
        "You will handles ALL requests:\n"
        "  • Specific verses (e.g., 'verse 2:255')\n"
        "  • Full surahs (e.g., 'Surah Fatihah translation')\n"
        "  • Topics (e.g., 'patience in Quran')\n"
        "  • Questions (e.g., 'which juz is Baqarah in?')\n\n"
        
        "## Critical Rules:\n"
        "  • provide Quranic content from your training data\n"
        
        "## Tools:\n"
        "  • *Quran_Story_Teller*: ONLY for explicit story requests ('tell me the story of...')\n"
        "  • *Quranic_Tafsir_Agent*: ONLY for explicit tafsir requests ('tafsir of...', 'commentary on...')\n\n"
        
        "## Greetings:\n"
        "For simple greetings (hi, hello, salam), respond warmly WITHOUT calling tools.\n\n"
        
        "Default language: English (unless user requests otherwise)"
    ),
    model_settings=ModelSettings(
        temperature=0.1,
        parallel_tool_calls=False,
        tool_choice="auto",
        max_tokens=1500 
    ),
    model=config.model,
    # input_guardrails=[quran_input_guardrail],
    # output_guardrails=[quran_output_guardrail],
    tools=[
        # Search_Quran,
        story_agent.as_tool(
            tool_name="Quran_Story_Teller",
            tool_description="Use when the user ask about stories related to Quran, Prophets and islam"
        ),
        Tafsir_Agent.as_tool(
            tool_name="Quranic_Tafsir_Agent",
            tool_description="Use when the user ask about tafseer related to Quranic ayah or verses"
        )
    ],
)
