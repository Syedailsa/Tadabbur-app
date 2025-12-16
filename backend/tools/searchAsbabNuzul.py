import os
import operator
from pydantic import BaseModel, Field
from typing import Optional
from langchain_fireworks import FireworksEmbeddings
from qdrant_client import QdrantClient, models
from tools.utils import normalize_surah
from data.data import surah_name_english_translation_array, surah_name_english_array


COLLECTION_NAME = "Asbab_Nuzul"
EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"

# instantiate the embeddings model
embeddings = FireworksEmbeddings(
  api_key=os.getenv('FIREWORKS_API_KEY'),
  model = EMBEDDING_MODEL
)

class ToolSchema(BaseModel):
    surah_number: Optional[int] = None
    surah_number_min: Optional[int] = None
    surah_number_max: Optional[int] = None


    verse_number: Optional[int]= None
    verse_number_min: Optional[int]= None
    verse_number_max: Optional[int]= None

    surahEnglishName: Optional[str]= None
    surahEnglishNameTranslation: Optional[str]= None


def searchAsbabNuzul(args: ToolSchema, limit:int = 3, query = None):
    """Search tool for searching Asbab e Nuzul (Cicrumstances under revelation)
    
    **ARGS:**
    1. surah_number
    2. surah_number_min
    3. surah_number_max
    4. verse_number
    5. verse_number_min
    6. verse_number_max
    7. surahEnglishName
    8. surahEnglishNameTranslation
    
    ### • searchAsbabNuzul
    1. Use searchAsbabNuzul when user asks for queries related to Asbab_Nuzul/Shan_Nuzul (Circumstances of revelation)

    ## Example Queries
    1. What is the asbab e nuzul of surah Kafiroun?
    2. What is the asbab e nuzul of Surah Fatiha verse 1?
    3. What is the shan e nuzul of the surah which was revealed when the Prophet A.S was inflicted by magic?

    ### Important Guidelines
    1. When calling `searchAsbabNuzul`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.  
    2. Do **not** infer metadata such as surah_number, verse_number, surahEnglishName, surahEnglishNameTranslation.  
    3. If the user provides only surah and ayah numbers → pass **only those fields**.  
    """

    
    qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
    )

    tool_args = {
        "surah_number": args.surah_number,    
        "surah_number_min": args.surah_number_min,
        "surah_number_max": args.surah_number_max,

        "verse_number": args.verse_number,
        "verse_number_min": args.verse_number_min,
        "verse_number_max":args.verse_number_max,

        "surahEnglishName": normalize_surah(args.surahEnglishName , surah_name_english_array), 
        "surahEnglishNameTranslation": normalize_surah(args.surahEnglishName , surah_name_english_translation_array)
    }
    # if no Qdrant Client, then return
    if not qdrant_client:
        return "Qdrant client not instantiated properly"

    # checks if all tool arguments are none
    if not any(tool_args.values()):
        # all arguments are none so return
        return "No tool arguments are provided"

    # filter and remove the none tool arguments
    clean_arguments = {k:v for k,v in tool_args.items() if v is not None}

    print("Clean tool arguments", clean_arguments)

    print("Number of results to return", limit)

    must = []
    # build the filter
    for k,v in clean_arguments.items():
        min_or_max = "min" if "_min" in k else ("max" if "_max" in k else None) 

        print("Min or max", min_or_max)

        if min_or_max in ("min", "max"):
            field = k.replace(f"_{min_or_max}", "")
            if min_or_max == "min":
                must.append(models.FieldCondition(
                    key = field,
                    range = models.Range(
                        gte = v
                    )
                ))
            elif min_or_max  == 'max':
                must.append(models.FieldCondition(
                    key = field,
                    range = models.Range(
                        lte = v
                    )
                ))      
            
        else:
            must.append(
                models.FieldCondition(
                    key = k,
                    match = models.MatchValue(value = v)
                )
            )
    if query:
        query_embeddings = embeddings.embed_query(query)
    

    if not query_embeddings and not must:
         return "No query or filters provided"
    
    results = qdrant_client.query_points(
        collection_name = COLLECTION_NAME,
        query = query_embeddings,
        query_filter = models.Filter(must=must) if must else None,
        limit = limit
    )
    return results