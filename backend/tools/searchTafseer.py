import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_fireworks import FireworksEmbeddings
from qdrant_client import QdrantClient, models
from tools.normalizeName import normalize_surah
from data.data import surah_name_english_translation_array, surah_name_english_array
from langchain.tools import tool
import logging
import json
from langchain_core.caches import InMemoryCache
from langchain_core.outputs import Generation

load_dotenv()
logger = logging.getLogger(__name__)
COLLECTION_NAME = "Quran_Tafsir"
EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"

embeddings = FireworksEmbeddings(
    api_key=os.getenv('FIREWORKS_AI_API_KEY'),
    model=EMBEDDING_MODEL
)
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)

TAFSEER_CACHE = InMemoryCache(maxsize=1000)


class ToolSchema(BaseModel):
    "Surah, verse and metadata filters for tafseer search"
    surah_number: Optional[int] = Field(default=None)
    surah_number_min: Optional[int] = Field(default=None)
    surah_number_max: Optional[int] = Field(default=None)

    verse_number: Optional[int] = Field(default=None)
    verse_number_min: Optional[int] = Field(default=None)
    verse_number_max: Optional[int] = Field(default=None)

    juz: Optional[int] = Field(default=None)
    juz_min: Optional[int] = Field(default=None)
    juz_max: Optional[int] = Field(default=None)

    ruku: Optional[int] = Field(default=None)
    manzil: Optional[int] = Field(default=None)
    hizbQuarter: Optional[int] = Field(default=None)

    surah_englishName: Optional[str] = Field(default=None)
    surah_englishNameTranslation: Optional[str] = Field(default=None)
    limit: Optional[int] = Field(default=1)
    query: Optional[str] = Field(default=None)


class ToolSchemaList(BaseModel):
    "List of tafseer search filters"
    args: List[ToolSchema] = Field(default_factory=list, description="List of tafseer search filters")


@tool(args_schema=ToolSchemaList)
def searchTafseer(
    args: List[ToolSchema] = None
) -> List:
    """Search tool for searching Tafseer (Quranic exegesis) by Ibn Kathir.

    **ARGS:**
    --- args (List[ToolSchema], optional)
    Each ToolSchema object contains the following:
        1. surah_number (int)
        2. surah_number_min (int)
        3. surah_number_max (int)
        4. verse_number (int)
        5. verse_number_min (int)
        6. verse_number_max (int)
        7. juz (int)
        8. juz_min (int)
        9. juz_max (int)
        10. ruku (int)
        11. manzil (int)
        12. hizbQuarter (int)
        13. surah_englishName (str)
        14. surah_englishNameTranslation (str)
        15. limit (int)
        16. query (str)

    ### When to use searchTafseer
    1. Use when the user asks for tafseer, explanation, or exegesis of a surah or verse.
    2. Use when the user asks about the meaning or interpretation of a Quranic verse.
    3. Use when the user references a juz, manzil, ruku, or hizb quarter for tafseer.

    ## Example Queries
    1. What is the tafseer of Surah Fatiha?
    2. Explain the meaning of Surah Baqarah verse 255 (Ayat al-Kursi).
    3. What does Ibn Kathir say about the verses of Juz Amma?
    4. Give me the tafseer of verses about patience in the Quran.
    5. Explain the tafseer of Surah Kahf verses 1 to 10.

    ### Important Guidelines
    1. When calling `searchTafseer`, pass **only the arguments explicitly mentioned by the user**. Leave all others as None.
    2. Do **not** infer metadata such as surah_number, verse_number, juz, ruku etc unless the user explicitly states them.
    3. If the user provides only a surah name → pass only surah_englishName, leaving others as None.
    """

    logger.info("Tafseer tool called!")
    cache_key = json.dumps(
        {"args": [arg.model_dump() for arg in args]},
        sort_keys=True
    )
    llm_string = "tafseer_v1"

    cached_result = TAFSEER_CACHE.lookup(prompt=cache_key, llm_string=llm_string)
    if cached_result:
        logger.info("Cache hit — Tafseer result from cache")
        return json.loads(cached_result[0].text)

    if not qdrant_client:
        return {
            "success": False,
            "results": [],
            "error": "Retrieval failed due to database connection errors"
        }

    results_array = []

    for row in args:
        query = row.query
        limit = row.limit

        verse_tool_args = {
            "surah_number":              row.surah_number,
            "surah_number_min":          row.surah_number_min,
            "surah_number_max":          row.surah_number_max,

            "verse_number":              row.verse_number,
            "verse_number_min":          row.verse_number_min,
            "verse_number_max":          row.verse_number_max,

            "juz":                       row.juz,
            "juz_min":                   row.juz_min,
            "juz_max":                   row.juz_max,

            "ruku":                      row.ruku,
            "manzil":                    row.manzil,
            "hizbQuarter":               row.hizbQuarter,

            "surah_englishName":         normalize_surah(row.surah_englishName, surah_name_english_array),
            "surah_englishNameTranslation": normalize_surah(row.surah_englishNameTranslation, surah_name_english_translation_array),
        }

        if not any(verse_tool_args.values()) and not query:
            continue
            # return {
            #     "success": False,
            #     "results": [],
            #     "error": "Your query needs more information to return results."
            # }

        clean_arguments = {k: v for k, v in verse_tool_args.items() if v is not None}
        logger.info("Clean tool arguments: %s", clean_arguments)

        must = []

        if clean_arguments:
            for k, v in clean_arguments.items():
                if k == "limit":
                    continue
                min_or_max = "min" if "_min" in k else ("max" if "_max" in k else None)

                if min_or_max in ("min", "max"):
                    field = k.replace(f"_{min_or_max}", "")
                    if min_or_max == "min":
                        must.append(models.FieldCondition(
                            key=field,
                            range=models.Range(gte=v)
                        ))
                    elif min_or_max == "max":
                        must.append(models.FieldCondition(
                            key=field,
                            range=models.Range(lte=v)
                        ))
                else:
                    must.append(models.FieldCondition(
                        key=k,
                        match=models.MatchValue(value=v)
                    ))

        query_embeddings = None
        logger.info(f"Query: {query}")
        if query:
            query_embeddings = embeddings.embed_query(query)

        if not query_embeddings and not must:
            logger.info("No query of filters provided")
            continue
            # return {
            #     "success": True,
            #     "results": [],
            #     "error": "No query or filters provided"
            # }

        similar_points = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embeddings,
            limit=limit,
            using="verse-tafsir-dense-vector",
            query_filter=models.Filter(must=must) if must else None,
            with_vectors = False,
            score_threshold = 0.3 if query_embeddings else None
        )
        results_array.append(similar_points)

    if results_array and any(
        r.points for r in results_array if hasattr(r, "points")
    ):
        logger.info("Results found: %d", len(results_array))
        serializable = [r.model_dump() if hasattr(r, "model_dump") else r for r in results_array]
        response_obj = {
            "success": True,
            "results": serializable,
            "error": ""
        }
        TAFSEER_CACHE.update(
            prompt=cache_key,
            llm_string=llm_string,
            return_val=[Generation(text=json.dumps(serializable))]
        )
        logger.info("Cache updated with new Tafseer result")
        return response_obj
    else:
        logger.warning("No results found for the user's query")
        return {
            "success": False,
            "results": [],
            "error": "No results found for the user's query"
        }
