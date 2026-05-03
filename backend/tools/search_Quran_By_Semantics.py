import os
from agents import function_tool
from pydantic import BaseModel
from typing import Optional
from qdrant_client import QdrantClient, models
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# ===================== QDRANT & EMBEDDING SETUP =====================

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)
EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"
FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY')
print("Fireworks api key", FIREWORKS_API_KEY)
client = OpenAI(
    api_key = FIREWORKS_API_KEY, 
    base_url = "https://api.fireworks.ai/inference/v1"
)


@function_tool
async def Quran_Search_By_Semantics(query:str, limit = 1) -> str:
    """Searches Quran for semantic meaningful queries
    This tool does semantic searching over Quran Dataset for queries that can't be responded through filters. This tool fetches the semantically related content from the vector database and returns the answers to the agent
    
    **ARGS**
    1. Query - For Semantic Search.
    2. Limit - Number of results to fetch

    **PURPOSE**
    1. Used for queries that require semantic search over Quran Dataset.
    2. Fetches content for meaningful, semantic and conceptual queries.   

    **EXAMPLE QUERIES:**
    1. Find some verses that mention the importance of gratitude to Allah.
    2. Which verses describe the creation of the heavens in Quran?
    3. Tell me some verses related to kindness and helping others.
    4. What does the Quran say about trusting Allah in difficult times?
    5. Which verses talk about being truthful, honest, humble or modest?
    6. Give me ayahs discussing charity and giving to the poor.
    7. Which ayahs warn against backbiting or gossip?
    8. Find verses that describe the Day of Judgement in detail.
    9. What does the Quran say about the rights of orphans?
    10. Which verses talk about the consequences of arrogance?
    11. Which verses encourage reflection and pondering upon creation?
    12. Any verses that talk about the importance of knowledge or learning?
    13. Show me verses about the story of Ibrahim/Moses/Noah/Muhammad A.S when he was tested.
    14. What does the Quran say about treating parents with respect?
    15. Which ayahs speak about hypocrisy and hypocrites?
    16. Find verses about the virtues of those who do good deeds.
    17. Show me verses that comfort someone feeling hopeless or sad.
    18. Verses that talk about the temporary nature of this world.
    """

    args = {
        "query": query,
        "limit": limit
    }

    print("Args", args)
    try:

        embedding_response = client.embeddings.create(
            model = EMBEDDING_MODEL,
            input = query
        )
        
        query_embedding = embedding_response.data[0].embedding

        search_results = qdrant.query_points(
            collection_name = "Quran-Dataset-Collection",
            query = query_embedding,
            limit=limit,
            with_payload = True
        ).points

        if search_results:
            print("Results from vector database", search_results)
            return search_results
        else:
            return ""
    except Exception as e:
        print("Some error occured while performing semantic search", e)