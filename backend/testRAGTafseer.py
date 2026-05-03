import os
import re
import time
import logging
import qdrant_client
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import sys
import io
from langchain_fireworks import FireworksEmbeddings
from qdrant_client import QdrantClient, models
# Force UTF-8 for stdout when redirected
if not sys.stdout.isatty():  # If output is being redirected
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

FIREWORKS_API_KEY = os.getenv('FIREWORKS_AI_API_KEY')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL_ENDPOINT')
QURAN_API_BASE_URL = os.getenv('QURAN_API_BASE_URL')
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImY5MzAxZjgwLTdkY2QtNGNkMi04NWZlLTJjNWM5NjBhYTA2OSIsInR5cCI6IkpXVCJ9.eyJhdWQiOltdLCJjbGllbnRfaWQiOiI0OWNhMzNlZi04NDc2LTRlMmYtYjQ3Yy1kNzI3NGU5Mzc1OTQiLCJleHAiOjE3Nzc1NTI2NTEsImV4dCI6e30sImlhdCI6MTc3NzU0OTA1MSwiaXNzIjoiaHR0cHM6Ly9vYXV0aDIucXVyYW4uZm91bmRhdGlvbiIsImp0aSI6IjI0ZTM1NDE5LWIwNjgtNDNkMC04NjMxLWY0NDU4MzFjMTBmMiIsIm5iZiI6MTc3NzU0OTA1MSwic2NwIjpbImNvbnRlbnQiXSwic3ViIjoiNDljYTMzZWYtODQ3Ni00ZTJmLWI0N2MtZDcyNzRlOTM3NTk0In0.K57AfkI5-a6dwNBiiAgwUhSLovJtSRL6BANmzqNfubWO7WaNkUqrp6f8tDjULM_H9KVzgp-9Tfl79lrEe3HIr7FyCPoNRG8B5MX2d4KOOBL47g3GCrTsXXL6TUChUH1MURuYEhJJCG5E3N6XXmq-HTUQrm1kHGbmonsDc9ezIm7a1D8Uw18AZWxFH1dfzSUmngTF5XNfWWH-AE6xvxSyQd0Zpim8GC4Usb_JWKY0y2_uOwFBFKYUAjstsW2-gKOuOWW6y9g92Z-5ykM6UXmqV9kLjQeuBvCldX7mTmz1rWk6VsBTdhyw8cA-0l32kutpkI8IGvvPijAvrcCW2-j_vn9kgRkNYzsaU0dRIBktSJdJGl1cnkJnE2DMxaGhJsVTmXNHYDuPahuO-j5flq4rxfNwtCE2DsE8QuO77R6ZpA453VvIa71bOUOqQNU4dfb_bZG_eQzsW1ApHtJ_YwDNPBPo8ccFMAa74tLUwzdSZEsp6Myx1kr1-UYBNzWGg4fVP5ZkulT1HReybVuEStffNoPvRXCQh1TdKQfHW91rUJWRgydionpzRsyN9XoSMdIGw3i36dcJONNGjOMxFRkN66d5n8TM97_Wnl5esSFOd3A9qm5Lu-fIWFAmP16VAxdr2ogJ4wzXHkm9qjNprOR3xwHmYzuJ_V-Wk77Vjp6RMV0"
CLIENT_ID = os.getenv('QURAN_API_CLIENT_ID')


qdrant_client = QdrantClient(url = QDRANT_URL, api_key = QDRANT_API_KEY, timeout = 120)
embedding_model = FireworksEmbeddings(api_key = FIREWORKS_API_KEY, model = "fireworks/qwen3-embedding-8b")

def strip_html(text, separator = " "):
    return BeautifulSoup(text or "", "html.parser").get_text(separator = separator).strip()

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
                                                                        
# text_splitter = RecursiveCharacterTextSplitter(              
#     chunk_size=1500,
#     chunk_overlap=50,
#     is_separator_regex=True,
#     separators=[                                                                                                                                               r"</p>\s*<p[^>]*>",          # p → p
#     r"</h[1-6]>\s*<[^>]+>",      # any h tag exit → next tag                                                                                                                                             
#     r"<br\s*/?>",                 # line break
#     r"\.\s+",                     # sentence boundary
#     r"\s+",                       # whitespace fallback
#   ]
# )

def merge_small_chunks(chunks, min_words=50):
    merged = []
    buffer = ""
    
    for chunk in chunks:
        if buffer:
            chunk = buffer + " " + chunk
            buffer = ""
        
        if len(chunk.split()) < min_words:
            buffer = chunk
        else:
            merged.append(chunk)
    
    # If buffer still has content, append to last chunk or add as-is
    if buffer:
        if merged:
            merged[-1] = merged[-1] + " " + buffer
        else:
            merged.append(buffer)
    
    return merged

def split_large_chunks(chunks, max_words=200):
    result = []
    
    for chunk in chunks:
        words = chunk.split()
        
        if len(words) <= max_words:
            result.append(chunk)
        else:
            # Split into sentences first, then group within max_words
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            buffer = ""
            
            for sentence in sentences:
                if len((buffer + " " + sentence).split()) <= max_words:
                    buffer = (buffer + " " + sentence).strip()
                else:
                    if buffer:
                        result.append(buffer)
                    buffer = sentence
            
            if buffer:
                result.append(buffer)
    
    return result



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)


# # initialize the array
# chunked_tafseer_texts = []
# data = call_api("169", 2, 1)
# tafseers =  data['tafsirs'][:6]
# for verse in tafseers:
#     cleaned_chunks = strip_html(verse['text']).split("<logical boundary>")
#     cleaned_chunks = [c.strip() for c in cleaned_chunks if c.strip()]
    
#     final_small_chunks = merge_small_chunks(cleaned_chunks)
#     final_large_chunks = split_large_chunks(final_small_chunks)
    
#     chunked_tafseer_texts.append({
#         "chunk_count_before_merge": len(cleaned_chunks),
#         "chunk_count_after_small_merge": len(final_small_chunks),
#         "chunk_count_after_large_merge": len(final_large_chunks),
#         "chunks": [
#             {"text": chunk, "chunk_length": len(chunk.split())}
#             for chunk in final_large_chunks
#         ]
#     })


def get_all_chunks_for_quran(resource_id="169", total_chapters=10):
    all_chunks = []

    for chapter in range(1, total_chapters + 1):
        log.info(f"--- Starting chapter {chapter}/{total_chapters} ---")
        page = 1
        first_response = call_api(resource_id, chapter, page)
        total_pages = first_response['pagination']['total_pages']
        log.info(f"Chapter {chapter} — total pages: {total_pages}")

        while page <= total_pages:
            data = call_api(resource_id, chapter, page) if page > 1 else first_response
            verses = data['tafsirs']
            log.info(f"Chapter {chapter}, page {page}/{total_pages} — {len(verses)} verses")

            for verse in verses:
                tafseer_text = strip_html(verse['text'])
                cleaned_chunks = strip_html(verse['text'], separator="<logical boundary>").split("<logical boundary>")
                cleaned_chunks = [c.strip() for c in cleaned_chunks if c.strip()]
                final_chunks = merge_small_chunks(cleaned_chunks)
                final_chunks = split_large_chunks(final_chunks)

                for chunk in final_chunks:
                    all_chunks.append({
                        "tafseer_text": tafseer_text,
                        "surah_number": chapter,
                        "verse_number": verse['verse_number'],
                        "juz_number": verse['juz_number'],
                        "hizb_number": verse['hizb_number'],
                        "ruku_number": verse['ruku_number'],
                        "manzil_number": verse['manzil_number'],
                        "text": chunk,
                        "chunk_length": len(chunk.split())
                    })

            log.info(f"Chapter {chapter}, page {page} done — total chunks so far: {len(all_chunks)}")
            page += 1
            time.sleep(0.5)

        log.info(f"Chapter {chapter} complete — chunks so far: {len(all_chunks)}")

    return all_chunks


all_chunks = get_all_chunks_for_quran()

EMBEDDING_BATCH_SIZE = 50

embddings_document = [chunk['text'].strip() for chunk in all_chunks]
embeddings_array = []
for i in range(0, len(embddings_document), EMBEDDING_BATCH_SIZE):
    batch = embddings_document[i:i + EMBEDDING_BATCH_SIZE]
    log.info(f"Embedding batch {i // EMBEDDING_BATCH_SIZE + 1}/{(len(embddings_document) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE} ({len(batch)} docs)")
    embeddings_array.extend(embedding_model.embed_documents(batch))

payloads_array = [{"tafseer_text": chunk['tafseer_text'],
                    'surah_number': chunk['surah_number'],
                    "verse_number": chunk['verse_number'],
                    "juz_number": chunk['juz_number'],
                    "hizb_number": chunk['hizb_number'],
                    "ruku_number": chunk['ruku_number'],
                    "manzil_number": chunk['manzil_number'],
                    "chunk_text": chunk["text"]}
                    for chunk in all_chunks]

points = [models.PointStruct(id = i + 1, payload = payloads_array[i], vector = embeddings_array[i]) for i, _ in enumerate(all_chunks)]

try:
    qdrant_client.upsert(
        collection_name = "Quran_Tafsir_test",
        points = points
    )
    log.info("Successfully inserted all points in collection: Quran_Tafsir_test")
except Exception as e:
    log.error(f"Some error occured while inserting points in vector db, Error: {e}")



# embed_query = embedding_model.embed_query("Wife of Aziz tried to seduce Yusuf A.S but he sought refuge in Allah")
# points = qdrant_client.query_points(
#     collection_name = "Quran_Tafsir_test",
#     query = embed_query,
#     with_vectors = False,
# )
# print(points)


# qdrant_client.delete(
#     collection_name="Quran_Tafsir_test",
#     points_selector=models.FilterSelector(
#             filter=models.Filter()
#     )
# )