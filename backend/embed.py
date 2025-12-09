# embedding asbab e nuzul for semantic and filter search
import os
import json
import PyPDF2
from langchain_fireworks import ChatFireworks
from langchain_core.prompts import ChatPromptTemplate
import re
from pydantic import BaseModel, Field
from typing import Optional, List
from data.data import comprehensive_surah_metadata
from dotenv import load_dotenv

load_dotenv()


pdf_path = r"C:\Users\anas_\Downloads\Asbab Al-Nuzul by Al-Wahidi.pdf"

reader = PyPDF2.PdfReader(pdf_path)
full_text = ""


class VerseSchema(BaseModel):
    verse_number: Optional[int] = Field(
        default = None,
        description = "Verse number of asbab e nuzul and must be >=1"
    )
    asbab_nuzul: Optional[str] = Field(
        default = "Not provided",
        description = "Circumstances of revelation of each verse"
    )

class SurahSchema(BaseModel):
    surah_number: Optional[int] = Field(
        default = None,
        description="Surah number of the verse, must be >=1"

    )
    surah_name: Optional[str] = Field(
        default = "Not provided",
        description = "Surah name of the verse"
    )
    surah: List[VerseSchema]

class AllSurahSchema(BaseModel):
    all_surahs_list: List[SurahSchema]



safe_meta_data_str = json.dumps(comprehensive_surah_metadata)
safe_meta_data_str = safe_meta_data_str.replace("{", "{{").replace("}", "}}")

system_instructions = f"""
You are an expert in extracting structured information from Asbab e Nuzul (Circumstances of Revelation)
from a given extract.


EXAMPLES

**Extract:**
[2:1-2] 
(Alif. Lam. Mim. This is the Scripture) [2:1-2]. Abu 'Uthman al-Thaqafi al-Za'farani informed us > Abu 'Amr
ibn Matar > Ja'far ibn Muhammad ibn al-Layth > Abu Hudhayfah > Shibl > Ibn Abi Najih > Mujahid who said:
"Four verses from the beginning of this Surah were revealed about the believers, and two verses after these
four were revealed about the disbelievers and thirteen verses after these last two were revealed about the
hypocrites."

## STRUCTURED_OUTPUT (Example)
The output must always follow EXACTLY this shape:

{{{{
  "all_surahs_list": [
    {{{{
      "surah_number": 2,
      "surah_name": "Al-Baqarah",
      "surah": [
        {{{{
          "verse_number": 1,
          "asbab_nuzul": "Abu 'Uthman al-Thaqafi ..."
        }}}},
        {{{{
          "verse_number": 2,
          "asbab_nuzul": "Abu 'Uthman al-Thaqafi ..."
        }}}}
      ]
    }}}}
  ]
}}}}

# GUIDELINES:

1. Each Asbab paragraph STARTS immediately before patterns like:
   - [surah_number:verse_number]
   - [surah_number:start_verse-end_verse]


2. Ignore any other [x:y] found inside explanation text.

3. If a verse range is given (e.g., [2:1-5]), expand into individual verse entries.

4. The field "asbab_nuzul" must contain the exact text belonging to that verse or verse range.

5. Use the following Surah metadata when needed:
{safe_meta_data_str}
"""

# system_instructions = system_instructions.format(
#     comprehensive_surah_metadata = safe_meta_data_str
# )

prompt = ChatPromptTemplate.from_messages([
    ("system", system_instructions), ("user", "{extract}")
])
llm = ChatFireworks(api_key = os.getenv("FIREWORKS_API_KEY"), model = "accounts/fireworks/models/kimi-k2-instruct-0905")

structured_llm = llm.with_structured_output(AllSurahSchema, method="json_mode", )


chain  = prompt | structured_llm


output_file = open("spam.txt", "w", encoding="utf-8")
for page in reader.pages[15: ]:
    response = chain.invoke({"extract": page.extract_text()})
    print(response, file=output_file, flush=True) 


output_file.close()  # Close at end
