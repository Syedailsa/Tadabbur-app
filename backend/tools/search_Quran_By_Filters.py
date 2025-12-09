import operator
import os
import requests
from rapidfuzz import process, fuzz
from data.data import surah_name_english_translation_array, surah_name_english_array
from agents import function_tool
from pydantic import BaseModel
from typing import Optional
from qdrant_client import QdrantClient, models

# ===================== QDRANT & EMBEDDING SETUP =====================

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)

COLLECTION_NAME = "Quran-Dataset-Collection"
EMBEDDING_MODEL = "fireworks/qwen3-embedding-8b"

# {'number': 1, 'text': 'In the name of God, The Most Gracious, The Dispenser of Grace:', 'numberInSurah': 1, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}, {'number': 2, 'text': 'All praise is due to God alone, the Sustainer of all the worlds,', 'numberInSurah': 2, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False

def normalize_surah(name:str, array:list) -> str | None:
    """
    Converts user-provided surah name → canonical surah name using fuzzy match.
    Returns None if input is empty or extremely unclear.
    """

    if not name:
        return None

    name = name.strip().lower()
    best, score,_ = process.extractOne(
        name,
        array,
        scorer = fuzz.WRatio
    )

    if score < 65:
        
        return None
    
    return best


class SurahFilter(BaseModel):
    number: Optional[int] = None
    number_min: Optional[int] = None
    number_max: Optional[int] = None
    name: Optional[str] = None
    englishName: Optional[str] = None
    englishNameTranslation: Optional[str] = None
    revelationType: Optional[str] = None


class VerseFilter(BaseModel):
    number: Optional[int] = None
    number_min: Optional[int] = None
    number_max: Optional[int] = None

    numberInSurah: Optional[int] = None
    numberInSurah_min: Optional[int] = None
    numberInSurah_max: Optional[int] = None

    ruku: Optional[int] = None
    ruku_min: Optional[int] = None
    ruku_max: Optional[int] = None

    juz: Optional[int] = None
    juz_min: Optional[int] = None
    juz_max: Optional[int] = None

    manzil: Optional[int] = None
    manzil_min: Optional[int] = None
    manzil_max: Optional[int] = None

    hizbQuarter: Optional[int] = None
    hizbQuarter_min: Optional[int] = None
    hizbQuarter_max: Optional[int] = None

    sajdah: Optional[bool] = None


@function_tool
async def Search_Quran_By_filters(surah_args:SurahFilter, verse_args: VerseFilter, limit: int) -> str:

    """Search Quran using metadata filters
    This tool does an exact filter search on the Quran verses stored in the vector database. It does not use embeddings or similarity search. Only fields that are provided (not None) are used as filter conditions.
    
    **ARGS:**

    --- Surah filters (surah_args) ---
    1. **number (int)**  
       Exact surah number (1–114).

    2. **number_min (int)**  
       Minimum surah number for range filtering.

    3. **number_max (int)**  
       Maximum surah number for range filtering.

    4. **name (str)**  
       Surah name in Arabic.

    5. **englishName (str)**  
       Surah name in English (e.g., "The Cow").

    6. **englishNameTranslation (str)**  
       Surah name translation in English.

    7. **revelationType (str)**  
       Either `"Meccan"` or `"Medinan"`.

    --- Verse filters (verse_args) ---
    8. **number (int)**  
       Exact ayah number in the entire Quran.

    9. **number_min (int)**  
       Minimum ayah number in the entire Quran.

    10. **number_max (int)**  
        Maximum ayah number in the entire Quran.

    11. **numberInSurah (int)**  
        Exact ayah number within the surah.

    12. **numberInSurah_min (int)**  
        Minimum ayah number within the surah.

    13. **numberInSurah_max (int)**  
        Maximum ayah number within the surah.

    14. **ruku (int)**  
        Exact Ruku number.

    15. **ruku_min (int)**  
        Minimum Ruku number.

    16. **ruku_max (int)**  
        Maximum Ruku number.

    17. **juz (int)**  
        Exact Juz number (1–30).

    18. **juz_min (int)**  
        Minimum Juz number.

    19. **juz_max (int)**  
        Maximum Juz number.

    20. **manzil (int)**  
        Exact Manzil number (1–7).

    21. **manzil_min (int)**  
        Minimum Manzil number.

    22. **manzil_max (int)**  
        Maximum Manzil number.

    23. **hizbQuarter (int)**  
        Exact Hizb quarter number (1–240).

    24. **hizbQuarter_min (int)**  
        Minimum Hizb quarter number.

    25. **hizbQuarter_max (int)**  
        Maximum Hizb quarter number.

    26. **sajdah (bool)**  
        Indicates whether the ayah contains a sajdah (True/False).

    27. **limit (int)**
        Number of results to return

    **PURPOSE:**
    1. Used for queries that can retreive data through specific fields filtering.
    2. Uses filter queries for fetching data. 

    **EXAMPLE QUERIES:**
    1. What is verse number 5 of surah fatiha.
    2. What is the verse number 5 of Al Quran.
    3. What does Surah Fatiha verse 5 says about Guidance and worshipping Allah.
    4. Is verse number 128 of Surah Baqarah a Sajda verse.
    5. Give me translation of verse 13 of Surah An'aam and verse 50 of Al-Baqarah.
    """

    surah_arguments = {
        "number": surah_args.number,
        "number_min": surah_args.number_min,
        "number_max": surah_args.number_max,
        "name" : surah_args.name,
        "englishName" : normalize_surah(surah_args.englishName, surah_name_english_array),
        "englishNameTranslation": normalize_surah(surah_args.englishNameTranslation, surah_name_english_translation_array),
        "revelationType": surah_args.revelationType
    }

    verse_arguments = {
        # --- Ayah number in entire Quran ---
        "number": verse_args.number,
        "number_min": verse_args.number_min,
        "number_max": verse_args.number_max,

        # --- Ayah number within surah ---
        "numberInSurah": verse_args.numberInSurah,
        "numberInSurah_min": verse_args.numberInSurah_min,
        "numberInSurah_max": verse_args.numberInSurah_max,

        # --- Ruku ---
        "ruku": verse_args.ruku,
        "ruku_min": verse_args.ruku_min,
        "ruku_max": verse_args.ruku_max,

        # --- Juz ---
        "juz": verse_args.juz,
        "juz_min": verse_args.juz_min,
        "juz_max": verse_args.juz_max,

        # --- Manzil ---
        "manzil": verse_args.manzil,
        "manzil_min": verse_args.manzil_min,
        "manzil_max": verse_args.manzil_max,

        # --- Hizb quarter ---
        "hizbQuarter": verse_args.hizbQuarter,
        "hizbQuarter_min": verse_args.hizbQuarter_min,
        "hizbQuarter_max": verse_args.hizbQuarter_max,

        # --- Sajdah ---
        "sajdah": verse_args.sajdah,
    }

    #filter out the non null parameters
    clean_args_surah = {k:v for k,v in surah_arguments.items() if v is not None}
    clean_args_verse = {k:v for k,v in verse_arguments.items() if v is not None}

    print("Clean Surah arguments", clean_args_surah)
    print("Clean Verse arguments", clean_args_verse)

    # fetch the data
    response = requests.get("https://api.alquran.cloud/v1/quran/en.asad")

    if not response.ok:
        print("Couldn't get data from the Quran Cloud")
        return "Couldn't get data from the Quran Cloud"
    
    Quran_data = response.json()['data']['surahs']
    filtered_array = Quran_data
    # Initialize filter conditions array for surah filtering    
    surah_filter_conditions = []    
    # build the filter
    print('Number of results to return', limit)
    for k,v in clean_args_surah.items():        
        min_or_max = "min" if "_min" in k else ("max" if "_max" in k else None)

        print("Min or max", min_or_max)
        if min_or_max in ("min", "max"):
            field = k.replace(f"_{min_or_max}", "")
            if min_or_max == "min":
                op = operator.ge
            elif min_or_max == "max":
                op = operator.le
            surah_filter_conditions.append(lambda surah, f = field, vv = v, o = op: o(surah[field], vv))
        else:
            surah_filter_conditions.append(lambda surah, f = k , vv= v: surah[f] == vv)
    
    all_surah_filter_conditions = lambda surah: all (cond(surah) for cond in surah_filter_conditions)

    # apply the surah filter
    filtered_array = list(filter(all_surah_filter_conditions, filtered_array))
    
        
    # Initialize filter conditions array for verse filtering
    verse_filter_conditions = []
    for k,v in clean_args_verse.items():
        min_or_max = "min" if "_min" in k else ("max" if "_max" in k else None) 
        # check for minimum and maximum values in the key
        print("Min or Max", min_or_max)
        if min_or_max in ("min", "max"):
            field = k.replace(f"_{min_or_max}", "")
            if min_or_max == "min":
                op = operator.ge
            elif min_or_max == "max":
                op = operator.le
            verse_filter_conditions.append(lambda ayah, f = field, vv=v, o=op: o(ayah[field], vv))
        else:
            verse_filter_conditions.append(lambda ayah, f=k, vv=v: ayah[f] == vv)

    all_verse_filter_conditions = lambda ayah: all (cond(ayah) for cond in verse_filter_conditions)

    # apply the verse filter
    new_filtered_array = []
    for surah in filtered_array:
        filtered_verses = list(filter(all_verse_filter_conditions, surah['ayahs']))
        
        if filtered_verses:
            surah['ayahs'] = filtered_verses
            new_filtered_array.append(surah)

    filtered_array = new_filtered_array

    
    print("filtered_array after verse filter", filtered_array)
        
    return filtered_array[:limit]



# {'surahs': [{'number': 1, 'name': '╪│┘Å┘ê╪▒┘Ä╪⌐┘Å ┘▒┘ä┘Æ┘ü┘Ä╪º╪¬┘É╪¡┘Ä╪⌐┘É', 'englishName': 'Al-Faatiha', 'englishNameTranslation': 'The Opening', 'revelationType': 'Meccan', 'ayahs': [{'number': 1, 'text': 'In the name of God, The Most Gracious, The Dispenser of Grace:', 'numberInSurah': 1, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}, {'number': 2, 'text': 'All praise is due to God alone, the Sustainer of all the worlds,', 'numberInSurah': 2, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}, {'number': 3, 'text': 'The Most Gracious, the Dispenser of Grace,', 'numberInSurah': 3, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}, {'number': 4, 'text': 'Lord of the Day of Judgment!', 'numberInSurah': 4, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}, {'number': 5, 'text': 'Thee alone do we worship; and unto Thee alone do we turn for aid.', 'numberInSurah': 5, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}, {'number': 6, 'text': 'Guide us the straight way.', 'numberInSurah': 6, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}, {'number': 7, 'text': 'The way of those upon whom Thou hast bestowed Thy blessings, not of those who have been condemned [by Thee], nor of those who go astray!', 'numberInSurah': 7, 'juz': 1, 'manzil': 1, 'page': 1, 'ruku': 1, 'hizbQuarter': 1, 'sajda': False}]}
