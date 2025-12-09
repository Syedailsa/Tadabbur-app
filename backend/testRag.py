import json
import os
import requests
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from openai import OpenAI
import sys

load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
QDRANT_URL = os.getenv("")
qdrant_client = QdrantClient (
    url=os.getenv("QDRANT_URL_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)

# client = OpenAI(api_key=FIREWORKS_API_KEY, base_url="https://api.fireworks.ai/inference/v1")
# EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"
# resp = client.embeddings.create(model=EMBEDDING_MODEL, input="Tell me the story of Prophet Musa.")
# query_embeddings = resp.data[0].embedding

# search_results = qdrant_client.query_points(
#     collection_name = "Quran-Dataset-Collection",
#     query = query_embeddings,
#     limit=1,
#     with_payload = True
# ).points


sys.stdout.reconfigure(encoding='utf-8')
response = requests.get('https://api.alquran.cloud/v1/surah')

surah_name_array_english = []
surah_name_array_english_translation = []

if response.ok:
    data = response.json()
    surah_array = data["data"]
    for surah in surah_array:
        surah_name_array_english.append(surah["englishName"])
        surah_name_array_english_translation  .append(surah["englishNameTranslation"])

print("Surah name array english")
print(surah_name_array_english)
print("Surah name array english translation")
print(surah_name_array_english_translation)

