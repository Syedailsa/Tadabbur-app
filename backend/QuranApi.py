# Get tafsirs for specific Surah

import requests
import os
from dotenv import load_dotenv
from langchain_fireworks import FireworksEmbeddings
from qdrant_client import QdrantClient, models
from data.data import comprehensive_surah_metadata
from bs4 import BeautifulSoup

def strip_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text(separator=" ").strip()

load_dotenv()

QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL_ENDPOINT')
QURAN_API_BASE_URL = os.getenv('QURAN_API_BASE_URL')
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImY5MzAxZjgwLTdkY2QtNGNkMi04NWZlLTJjNWM5NjBhYTA2OSIsInR5cCI6IkpXVCJ9.eyJhdWQiOltdLCJjbGllbnRfaWQiOiI0OWNhMzNlZi04NDc2LTRlMmYtYjQ3Yy1kNzI3NGU5Mzc1OTQiLCJleHAiOjE3NzcxMjU4OTcsImV4dCI6e30sImlhdCI6MTc3NzEyMjI5NywiaXNzIjoiaHR0cHM6Ly9vYXV0aDIucXVyYW4uZm91bmRhdGlvbiIsImp0aSI6ImM2OGQzOGNjLTcxOGQtNGJkMC1hZTE0LTA1YmE0ZGJhOWQyYiIsIm5iZiI6MTc3NzEyMjI5Nywic2NwIjpbImNvbnRlbnQiXSwic3ViIjoiNDljYTMzZWYtODQ3Ni00ZTJmLWI0N2MtZDcyNzRlOTM3NTk0In0.KCarbpfFHQuGZPB-9blnWy6O8pBa5YvN0QLa8HY2vCbE2BxyQtacSvXCKwN-UzNK65O2PVYYqhb7zbxLv1vTEmvHsLsBo-AGA_j2e1GvPKo8H4ezk3ri42K_6HhTjcZfSmW46PYUJg39-aZy_2aq8DOBnwXxt3wWgq5Ln0eW_qt_A_J20vsVuBBoAkEjsfcn1XLwXhU4JIR33AddgBQbufK5_7YRJs6STfylYzwXUiT4a3C0HhuJYDcQq8-2B9JNQ_mtTJLf8AQaaqAm6Tfh9Xn023hkMLf3PPQ1wMM9FuYymgTOjarfnYQO4JlHgTO447BXxZlXzN53P2XjkELwKYVL149P4j2cViBDr0CXrfldp_8EeZpsqhZ2t7_Q_6kRdU9cE7RTpNhK2BuA1z-IeJzLEXvNmh-UFXU-0fCPRAwWqyXyWSy9EAV4Qjb8NPQRjPfuZ7JnKJEOBtZXkCr9KgsohUPH9YYsJzeopvH0QYBMEaxEUQAwqkFiuo0s7OnvcSXWX4hyckWYPzfClGyKwdW25MYtuwFfeyXPMRbWkBoGlP1h1wH7vM8VRTkouPSqMbApRZLZvWxce0KK-ePBBgQNd-hKIjjcf2lRTySoi7adcJlMYsZobdP80jA4vOslFkBl6zvgcXGl6ZmDp_lxDucF2yn0wM4gXVr_MVIhFFk"
CLIENT_ID = os.getenv('QURAN_API_CLIENT_ID')

def call_api(resource_id, chapter_number, page = 1):
    params = {
        "fields" : "verse_number,juz_number,hizb_number,ruku_number,manzil_number",
        "page": page,
        "per_page": 50
        }
    
    response = requests.get(
        f'{QURAN_API_BASE_URL}/tafsirs/{resource_id}/by_chapter/{chapter_number}',
        headers={
            'x-auth-token': ACCESS_TOKEN,
            'x-client-id': CLIENT_ID
        },
        params=params
    )
    response.raise_for_status()
    return response.json()

# qdrant = QdrantClient(url=QDRANT_URL, api_key = QDRANT_API_KEY, timeout=120)
# EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"

# embeddings = FireworksEmbeddings(
#   api_key=os.getenv('FIREWORKS_AI_API_KEY'),
#   model = EMBEDDING_MODEL
# )

# if not qdrant:
#     raise ValueError("Could not initialize Qdrant!")

# if not embeddings:
#     raise ValueError("Could not initialize Fireworks Embeddings model!")

# # # Example usage

# total_surahs = 114
# print(f"\n{'='*60}")
# print(f"  Quran Tafsir Ingestion — {total_surahs} Surahs")
# print(f"{'='*60}\n")

# surah_errors = []

# for surah_idx in range(total_surahs):
#     surah_number = surah_idx + 1
#     surah_name = comprehensive_surah_metadata[surah_idx]['englishName']
#     try:
#         result = call_api(169, f"{surah_number}")
#         total_pages = result['pagination']['total_pages']
#         print(f"[{surah_number:>3}/114] {surah_name} ({total_pages} page(s))")
#         print(f"  {'-'*40}")

#         total_verses_inserted = 0
#         for page_idx in range(total_pages):
#             data = call_api(169, f"{surah_number}", page_idx + 1)
#             tafseer = data['tafsirs']

#             asbab_nuzul_array = [strip_html(verse['text']) for verse in tafseer]
#             embeddings_array = embeddings.embed_documents(asbab_nuzul_array)

#             points = []
#             for verse_index, verse in enumerate(tafseer):
#                 clean_tafseer = asbab_nuzul_array[verse_index]
#                 print(f"Verse {verse['verse_number']:>3} | {clean_tafseer[:120]}{'...' if len(clean_tafseer) > 120 else ''}")
#                 points.append(models.PointStruct(id = surah_number * 1000 + verse["verse_number"], vector = {"verse-tafsir-dense-vector": embeddings_array[verse_index]}, payload = {"surah_number": surah_number, "verse_number": verse['verse_number'], "tafseer": clean_tafseer, "ruku": verse['ruku_number'], "hizbQuarter": verse["hizb_number"], "juz": verse["juz_number"], "manzil": verse["manzil_number"], "surah_englishName": surah_name, "surah_englishNameTranslation": comprehensive_surah_metadata[surah_idx]['englishNameTranslation'], "reference": 'Tafsir-Ibn-Kathir', "book_author": 'Ibn Kathir'}))

#             qdrant.upsert(collection_name="Quran_Tafsir", wait=True, points=points)
#             total_verses_inserted += len(points)
#             print(f"\n  Page {page_idx + 1}/{total_pages} upserted — {len(points)} verses\n")

#         print(f"  DONE: {total_verses_inserted} verses inserted for {surah_name}")
#         print(f"{'='*60}\n")

#     except Exception as e:
#         print(f"  ERROR: Surah {surah_number} ({surah_name}) failed — {e}")
#         print(f"{'='*60}\n")
#         surah_errors.append(surah_number)

# print(f"Ingestion complete.")
# if surah_errors:
#     print(f"  Failed surahs: {surah_errors}")
# else:
#     print(f"  All 114 surahs ingested successfully.")
# print(f"{'='*60}\n")    

import sys
import io
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Force UTF-8 for stdout when redirected
if not sys.stdout.isatty():  # If output is being redirected
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# test the api
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 100,
    chunk_overlap = 20,
    length_function = len,
    separators = [
        "\n\n",
        "\n",
    ]
)

# --- Semantic Tafseer Chunker ---
from langchain_fireworks import ChatFireworks
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List


class ChunkBoundaries(BaseModel):
    split_at: List[int] = Field(
        ...,
        description=(
            "Character position indices in the tafseer text where new chunks should begin. "
            "Do NOT include 0. Each index must be greater than 0 and less than the total length of the text."
        )
    )


_chunker_llm = ChatFireworks(
    model="accounts/fireworks/models/gpt-oss-20b",
    api_key=os.getenv('FIREWORKS_AI_API_KEY'),
    temperature=0
).with_structured_output(ChunkBoundaries)

_chunker_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a semantic chunker for Quranic tafseer (exegesis) text, preparing data for a RAG (Retrieval-Augmented Generation) pipeline.

## Goal
Split the tafseer passage into self-contained semantic chunks so that each chunk:
- Covers exactly one coherent idea, argument, narration, or scholarly point.
- Can be retrieved independently by a semantic search query.
- Is dense enough to embed meaningfully (target 150–350 words per chunk).

## Hard Constraints
1. NEVER split a Quranic verse or its translation from the commentary that immediately follows it — they must stay in the same chunk.
2. NEVER split a hadith across chunks — the chain of narrators (isnad) and the hadith text (matn) must stay together.
3. Do not create chunks under 80 words unless a standalone hadith or verse naturally ends there.

## Output
Return a list of integer character position indices in the text where each new semantic chunk should begin.
- These are 0-indexed character offsets into the raw string.
- Do NOT include 0 (the first chunk always starts at the beginning)."""),
    ("user", "{tafseer_text}")
])

_chunker_chain = _chunker_prompt | _chunker_llm


CHUNK_OVERLAP = 50


def _snap_to_word_boundary(text: str, pos: int) -> int:
    while pos < len(text) and not text[pos].isspace():
        pos += 1
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def _add_overlap(chunks: List[str], overlap: int = CHUNK_OVERLAP) -> List[str]:
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        tail = chunks[i - 1][-overlap:]
        boundary = tail.rfind('. ')
        overlap_text = tail[boundary + 2:] if boundary != -1 else tail
        result.append(overlap_text.strip() + ' ' + chunks[i])
    return result


def chunk_tafseer_semantic(tafseer_text: str) -> List[str]:
    """Split a tafseer passage into semantic chunks using an LLM.
    The LLM returns character position indices and slices the original string —
    content is never modified."""
    if len(tafseer_text.split()) < 120:
        return [tafseer_text]

    result = _chunker_chain.invoke({"tafseer_text": tafseer_text})

    positions = sorted({
        _snap_to_word_boundary(tafseer_text, pos)
        for pos in result.split_at
        if 0 < pos < len(tafseer_text)
    })

    chunks, prev = [], 0
    for pos in positions:
        chunk = tafseer_text[prev:pos].strip()
        if chunk:
            chunks.append(chunk)
        prev = pos
    chunks.append(tafseer_text[prev:].strip())

    return [{"chunk": c} for c in chunks if c.strip()]


data = call_api(169, "2", 1)
first_tafseer = (data['tafsirs'])[0]
# for verse in tafseers:
#     clean_verse_tafsir_text = strip_html(verse['text'])
#     chunk = chunk_tafseer_semantic(clean_verse_tafsir_text)
    # chunks_array.append(chunk)


chunks = chunk_tafseer_semantic(strip_html(first_tafseer['text']))


print(chunks)


