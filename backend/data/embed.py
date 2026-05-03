# embedding asbab e nuzul for semantic and filter search
# from math import e
# import re
import os
# import json
# import PyPDF2
# from langchain_fireworks import ChatFireworks
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_fireworks import FireworksEmbeddings
# from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
# from typing import Optional, List
# from data.data import comprehensive_surah_metadata
# from data.asbab_nuzul import structured_data
# from dotenv import load_dotenv
# from qdrant_client.models import PointStruct
from dotenv import load_dotenv
load_dotenv()


# EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"
# fireworks_api_key = os.getenv('FIREWORKS_API_KEY') 
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL_ENDPOINT')

# print("QDRANT_API_KEY", QDRANT_API_KEY)
# print("QDRANT_URL", QDRANT_URL)
# # breakpoint()

qdrant = QdrantClient(url=QDRANT_URL, api_key = QDRANT_API_KEY, timeout=120)
# pdf_path = r"C:\Users\anas_\Downloads\Asbab Al-Nuzul by Al-Wahidi.pdf"

# reader = PyPDF2.PdfReader(pdf_path)
# full_text = ""


# class VerseSchema(BaseModel):
#     verse_number: Optional[int] = Field(
#         default = None,
#         description = "Verse number of asbab e nuzul and must be >=1"
#     )
#     asbab_nuzul: Optional[str] = Field(
#         default = "Not provided",
#         description = "Circumstances of revelation of each verse"
#     )

# class SurahSchema(BaseModel):
#     surah_number: Optional[int] = Field(
#         default = None,
#         description="Surah number of the verse, must be >=1"
#     )
#     englishName: Optional[str] = Field(
#         default = "Not provided",
#         description = "English Name of the surah"
#     )
#     englishNameTranslation: Optional[str] = Field(
#       default = "Not provided",
#       description = "Surah's english name translation"
#     )
#     surah: List[VerseSchema]

# class AllSurahSchema(BaseModel):
#     all_surahs_list: List[SurahSchema]


# safe_meta_data_str = json.dumps(comprehensive_surah_metadata)
# safe_meta_data_str = safe_meta_data_str.replace("{", "{{").replace("}", "}}")

# system_instructions = f"""
# You are an expert in extracting structured information from Asbab e Nuzul (Circumstances of Revelation)
# from a given extract.

# EXAMPLES

# **Extract:**
# [2:1-2] 
# (Alif. Lam. Mim. This is the Scripture) [2:1-2]. Abu ‘Uthman al-Thaqafi al-Za‘farani informed us> Abu ‘Amr 
# ibn Matar> Ja‘far ibn Muhammad ibn al-Layth> Abu Hudhayfah> Shibl>Ibn Abi Najih> Mujahid who said: 
# “Four verses from the beginning of this Surah were revealed about the believers, and two verses after these 
# four were revealed about the disbelievers and thirteen verses after these last two were revealed about the 
# hypocrites”.  

# ## STRUCTURED_OUTPUT (Example)
# The output must always follow EXACTLY this shape:

# {{{{
#   "all_surahs_list": [
#     {{{{
#       "surah_number": 2,
#       "surah_name": "Al-Baqara",
#       "surah": [
#         {{{{
#           "verse_number": 1,
#           "asbab_nuzul": "Abu ‘Uthman al-Thaqafi al-Za‘farani informed us> Abu ‘Amr 
#           ibn Matar> Ja‘far ibn Muhammad ibn al-Layth> Abu Hudhayfah> Shibl>Ibn Abi Najih> Mujahid who said: 
#           “Four verses from the beginning of this Surah were revealed about the believers, and two verses after these 
#           four were revealed about the disbelievers and thirteen verses after these last two were revealed about the 
#           hypocrites"
#         }}}},
#         {{{{
#           "verse_number": 2,
#           "asbab_nuzul": "Abu ‘Uthman al-Thaqafi al-Za‘farani informed us> Abu ‘Amr 
#           ibn Matar> Ja‘far ibn Muhammad ibn al-Layth> Abu Hudhayfah> Shibl>Ibn Abi Najih> Mujahid who said: 
#           “Four verses from the beginning of this Surah were revealed about the believers, and two verses after these 
#           four were revealed about the disbelievers and thirteen verses after these last two were revealed about the 
#           hypocrites"
#         }}}}
#       ]
#     }}}}
#   ]
# }}}}

# # GUIDELINES:

# 1. Each Asbab paragraph STARTS immediately before patterns like:
#    - [surah_number:verse_number]
#    - [surah_number:start_verse-end_verse]


# 2. Ignore any other [x:y] found inside explanation text.

# 3. If a verse range is given (e.g., [2:1-5]), expand into individual verse entries.

# 4. The field "asbab_nuzul" must contain the exact text belonging to that verse or verse range.

# 5. Use the following Surah metadata when needed:
# {safe_meta_data_str}
# """

# system_instructions = system_instructions.format(
#     comprehensive_surah_metadata = safe_meta_data_str
# )

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_instructions), ("user", "{extract}")
# ])
# llm = ChatFireworks(api_key = os.getenv("FIREWORKS_API_KEY"), model = "accounts/fireworks/models/kimi-k2-instruct-0905", temperature = 0.1)

# structured_llm = llm.with_structured_output(AllSurahSchema, method = "json_mode")


# chain  = prompt | structured_llm

# pattern = r'\[\s*(\d+)\s*:\s*(\d+(?:-\d+)?)\s*\]\s*$'
# vector_embeddings_array = []
# embeddings = FireworksEmbeddings(
#   api_key=os.getenv('FIREWORKS_API_KEY'),
#   model = EMBEDDING_MODEL
# )

# full_text = ""
# for i, page in enumerate(reader.pages[15:], start = 15):
#   page_text = page.extract_text()
#   full_text += page_text


# tracker = None
# new_match_array = []
# matches = list(re.finditer(pattern, full_text, flags=re.MULTILINE))
# for i,match in enumerate(matches):

#   if match.group() != tracker:
#     start = match.start()
#     end = match.end()
#     tracker = match.group()
#     new_match_array.append({'heading': tracker, 'start': start, 'end': end})
#   tracker = match.group()
  
# for i, match in enumerate(new_match_array):
#   if i != (len(new_match_array) - 1):
#     match['asbab_nuzul'] = full_text[match['end']: new_match_array[i+1]['start']]
#   else:
#     match['asbab_nuzul'] = full_text[match['end']: ]
# print("matches", new_match_array)

# count = 0
# pattern = r'\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*'
# data = []
# for i, verse in enumerate(structured_data):
#   match = re.fullmatch(pattern, verse['heading'])
#   if match:
#     surah_number = int(match.group(1))
#     verse_number = int(match.group(2))
#     data.append({"surah_number": surah_number, "verse_number": verse_number, "asbab_nuzul": verse['asbab_nuzul']})    
#   else:
#     pass
#   #   data.append({"surah_number" : surah_number, "asbab_nuzul": verse['asbab_nuzul'], "verse_number": i})
# for i,verse in enumerate(structured_data):
#   verse['reference'] = "Asbāb al-Nuzūl"
#   verse["book_author"] = "Alī ibn Ahmad al-Wāhidī"

# with open("extra.txt", "w", encoding = 'utf-8') as f:
#   f.write(json.dumps(structured_data, indent = 2, ensure_ascii = False))

# asbab_nuzul_array = [verse['asbab_nuzul'] for verse in structured_data]
# embeddings_array = embeddings.embed_documents(asbab_nuzul_array)

# print("Length of embeddings array", len(embeddings_array))

# points = []
# for i, verse in enumerate(structured_data):

#   print(f"Appending point {i+1} to points array")
#   points.append(models.PointStruct(id = i + 1, vector = {"verse-dense-vector": embeddings_array[i]}, payload = {"surah_number": verse['surah_number'], "verse_number": verse['verse_number'], "asbab_nuzul" :verse['asbab_nuzul'], "surah_englishName": verse['surah_englishName'], "surah_englishNameTranslation": verse['surah_englishNameTranslation'], "reference": verse['reference'], "book_author": verse['book_author']}))


# # upsert the point in the Asbab e nuzul collection
# operation_info  = qdrant.upsert(
#   collection_name = "Asbab_Nuzul",
#   wait = True,
#   points = points
# )

# print('All points upserted successfully!')
# # verify count of points in the collection
# count = qdrant.count(collection_name="Asbab_Nuzul").count


index_schema = [
  {'field_name': "surah_englishName", "field_schema" : "keyword"},
  {'field_name': "surah_englishNameTranslation", "field_schema" : "keyword"},
  {'field_name': "reference", "field_schema" : "keyword"},
  {'field_name': "book_author", "field_schema" : "keyword"},
  {'field_name': "surah_number", "field_schema" : "integer"},
  {'field_name': "verse_number", "field_schema" : "integer"},
  {'field_name': "ruku", "field_schema" : "integer"},
  {'field_name': "hizbQuarter", "field_schema" : "integer"},
  {'field_name': "juz", "field_schema" : "integer"},
  {'field_name': "manzil", "field_schema" : "integer"},
  {'field_name': "tafseer", "field_schema" : "keyword"},
]

for i, schema in enumerate(index_schema):
  print(f"Field name {schema['field_name']} with schema {schema['field_schema']}")
  qdrant.create_payload_index(
    collection_name = "Quran_Tafsir",
    field_name = schema['field_name'],
    field_schema = schema['field_schema']
  )
print('All indexes created successfully!')


# embedding_query = embeddings.embed_query("Patience, Preservance and Honesty")

# qdrant_response = qdrant.query_points(
#   collection_name = "Asbab_Nuzul",
#   query = embedding_query,
#   using = 'verse-dense-vector',
#   query_filter = models.Filter(
#     must=[
#       models.FieldCondition(
#         key = "surah_englishName",
#         match = models.MatchValue(
#           value = "Al-Baqara",
#         )
#       ),
#       models.FieldCondition(
#         key = "verse_number",
#         match = models.MatchValue(
#           value = 284
#         )
#       )
#     ]
#   ),
#   limit = 1
# )

# print(qdrant_response)