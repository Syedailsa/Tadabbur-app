import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_fireworks import FireworksEmbeddings
from qdrant_client import QdrantClient, models
from tools.utils import normalize_surah
from data.data import surah_name_english_translation_array, surah_name_english_array
from langchain.tools import tool

load_dotenv()
COLLECTION_NAME = "Asbab_Nuzul"
EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"

# instantiate the embeddings model
embeddings = FireworksEmbeddings(
  api_key = os.getenv('FIREWORKS_AI_API_KEY'),
  model = EMBEDDING_MODEL
)

class ToolSchema(BaseModel):
    "Surah filters"
    surah_number: Optional[int] = Field(default=None)
    surah_number_min: Optional[int] = Field(default=None)
    surah_number_max: Optional[int] = Field(default=None)

    verse_number: Optional[int] = Field(default=None)
    verse_number_min: Optional[int] = Field(default=None)
    verse_number_max: Optional[int] = Field(default=None)

    surah_englishName: Optional[str] = Field(default=None)
    surah_englishNameTranslation: Optional[str] = Field(default=None)
    query: Optional[str] = Field(default=None)
    limit: Optional[int] = Field(default = None)

class ToolSchemaList(BaseModel):
    "List of surah filters"
    args: List[ToolSchema] = Field(default_factory = list, description = "List of surah filters")

@tool(args_schema = ToolSchema)
def searchAsbabNuzul(
    args: List[ToolSchema] = None
    ) -> List[dict]:
    """Search tool for searching Asbab e Nuzul (Cicrumstances under revelation)
    
    **ARGS:**
    --- args (List[ToolSchema], optional)
    Each ToolSchema object contains: 
    1. surah_number (int)
    2. surah_number_min (int)
    3. surah_number_max (int)
    4. verse_number (int)
    5. verse_number_min (int)
    6. verse_number_max (int)
    7. surah_englishName (int)
    8. surah_englishNameTranslation (str)
    8. limit (int)
    8. query (str)
    
    ### • searchAsbabNuzul
    1. Use searchAsbabNuzul when user asks for queries related to Asbab_Nuzul/Shan_Nuzul (Circumstances of revelation)

    ## Example Queries
    1. What is the asbab e nuzul of surah Kafiroun?
    2. What is the asbab e nuzul of Surah Fatiha verse 1?
    3. What is the shan e nuzul of the surah which was revealed when the Prophet A.S was inflicted by magic?
    4. Asbab e Nuzul of surah Yusuf, Quraysh, Noor and Namal.

    ### Important Guidelines
    1. When calling `searchAsbabNuzul`, pass **only the arguments explicitly mentioned by the user**. Leave all others as `None`.  
    2. Do **not** infer metadata such as surah_number, verse_number, surah_englishName, surah_englishNameTranslation.  
    3. If the user provides only surah and ayah numbers → pass **only those fields**.  
    """

    
    qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
    )
    results_array = []

    for row in args:
        query = row.query
        limit = row.query
        print("Query", query)
        print("Limit", limit)
        verse_tool_args = {
            "surah_number": row.surah_number,    
            "surah_number_min": row.surah_number_min,
            "surah_number_max": row.surah_number_max,

            "verse_number": row.verse_number,
            "verse_number_min": row.verse_number_min,
            "verse_number_max": row.verse_number_max,

            "surah_englishName": normalize_surah(row.surah_englishName , surah_name_english_array), 
            "surah_englishNameTranslation": normalize_surah(row.surah_englishNameTranslation , surah_name_english_translation_array),
        }
    
        # if no Qdrant Client, then return
        if not qdrant_client:
            print("Qdrant client not instantiated properly")
            return "Qdrant client not instantiated properly"

        # checks if all tool arguments are none
        if not any(verse_tool_args.values()):
            # all arguments are none so return
            print("No tool arguments are provided")
            return "No tool arguments are provided"

        # filter and remove the none tool arguments
        clean_arguments = {k:v for k,v in verse_tool_args.items() if v is not None}

        print("Clean tool arguments", clean_arguments)

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
        query_embeddings = None
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
        results_array.append(results)
    if results_array:
        print("Resuls to return", results_array)
        return results
    else:
        print("No results for the query")