import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

qdrant = QdrantClient(url=os.getenv('QDRANT_URL_ENDPOINT'), api_key=os.getenv('QDRANT_API_KEY'), timeout=120)

COLLECTION_NAME = "Quran_Tafsir"

qdrant.delete(
    collection_name=COLLECTION_NAME,
    points_selector=models.FilterSelector(filter=models.Filter())
)
print(f"All points deleted from '{COLLECTION_NAME}'. Collection remains intact.")
