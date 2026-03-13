import json
import requests
import operator
import logging
from data.data import surah_name_english_array, surah_name_english_translation_array
from langchain_core.caches import InMemoryCache
from langchain_core.outputs import Generation
from pydantic import BaseModel, Field
from typing import Optional
from tools.normalizeName import normalize_surah
from typing import List, Literal
from langchain.tools import tool
from threading import Lock

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

class SurahFilter(BaseModel):
    """Input for surah queries"""
    number: Optional[int] = None
    number_min: Optional[int] = None
    number_max: Optional[int] = None
    name: Optional[str] = None
    englishName: Optional[str] = None
    englishNameTranslation: Optional[str] = None
    revelationType: Optional[Literal["Meccan", "Medinan"]] = None


class VerseFilter(BaseModel):
    """Input for verse queries"""
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
    limit: Optional[int] = 1

class Filters(BaseModel):
    surah_args: SurahFilter = None
    verse_args: VerseFilter = None

# lock to prevent race condition
QURAN_DATA_LOCK = Lock()
QURAN_API_BASE = "https://api.alquran.cloud/v1/quran/en.asad"
QURAN_IMAGE_BASE_API = "http://cdn.islamic.network/quran/images/high-resolution"
QURAN_DATA_CACHE = None
QURAN_TOOL_CACHE = InMemoryCache(maxsize=1000)  


def get_Quran_data():
    global QURAN_DATA_CACHE
    with QURAN_DATA_LOCK:
        if QURAN_DATA_CACHE is None:
            try:
                response = requests.get(QURAN_API_BASE, timeout = 10)
                # response.raise_for_status() raise error for bad HTTP responses 
                if not response.ok:
                    raise ValueError("Quran data not available")
                QURAN_DATA_CACHE = response.json()['data']['surahs']
                if not QURAN_DATA_CACHE:
                    response_data = {
                        "success": False,
                        "verse_images": [],
                        "error": "Quran data is empty"
                    }
                    return response_data
            except requests.Timeout:
                raise ValueError("Request to Quran API timed out")
            except requests.RequestException as e:
                raise ValueError(f"Error fetching Quran data: {e}")
        return QURAN_DATA_CACHE

class FiltersList(BaseModel):  # New top-level schema
    """List of Quran filters"""
    args: List[Filters] = Field(default_factory=list, description="List of filter queries")

@tool(args_schema = FiltersList)
def get_verse_image(args: List[Filters] = None) -> dict:

    """Get Verse Image using metadata filters
    This tool does an exact filter search on the Quran verses stored in the cloud and retreives image for a particular verse(s). Only fields that are provided (not None) are used as filter conditions.
    
    **ARGS:**

    --- args (List[Filters], optional) ---
    Each Filters object contains:
    
    - surah_args (SurahFilter):    
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


    - verse_args (VerseFilter, optional) ---
        1. **number (int)**  
        Exact ayah number in the entire Quran.

        2. **number_min (int)**  
        Minimum ayah number in the entire Quran.

        3. **number_max (int)**  
            Maximum ayah number in the entire Quran.

        4. **numberInSurah (int)**  
            Exact ayah number of the surah.

        5. **numberInSurah_min (int)**  
            Minimum ayah number of the surah.

        6. **numberInSurah_max (int)**  
            Maximum ayah number of the surah.

        7. **ruku (int)**  
            Exact Ruku number.

        8. **ruku_min (int)**  
            Minimum Ruku number.

        9. **ruku_max (int)**  
            Maximum Ruku number.

        10. **juz (int)**  
            Exact Juz number (1–30).

        11. **juz_min (int)**  
            Minimum Juz number.

        12. **juz_max (int)**  
            Maximum Juz number.

        13. **manzil (int)**  
            Exact Manzil number (1–7).

        14. **manzil_min (int)**  
            Minimum Manzil number.

        15. **manzil_max (int)**  
            Maximum Manzil number.

        16. **hizbQuarter (int)**  
            Exact Hizb quarter number (1–240).

        17. **hizbQuarter_min (int)**  
            Minimum Hizb quarter number.

        18. **hizbQuarter_max (int)**  
            Maximum Hizb quarter number.

        19. **sajdah (bool)**  
            Indicates whether the ayah contains a sajdah (True/False).

        20. **limit (int)**
            Number of results to return

    **Notes:** Each Filters object represents a single surah–verse query. Multiple queries can be provided as a list of Filters.

    **PURPOSE:**
    1. Used for queries that can retreive data through filtering specific fields.
    2. Uses surah-verse arguments for fetching relevant verse images.

    **EXAMPLE QUERIES:**
    1. I want to read to verse number 10 of surah An'aam.
    2. Show me the verse number 5 of Al Quran.
    3. Show me a sajda verse.
    5. I want to read verse 13 of Surah An'aam and verse 50 of Al-Baqarah.
    6. I want to see the arabic of verse 10 of Surah Yusuf, verse 9 of Muzammil and verse 100 of Surah Baqarah.
    7. I want to read verses 1-10 of surah Baqarah, Quraysh and Bani Israeel.
    """

    if not args:
        response_data = {
            "success": False,
            "verse_images": [],
            "error": "No filters are provided for retrieving verse images"
        }
        return response_data
    # initialize a results array to concatenate results
    cache_key = json.dumps([arg.model_dump() for arg in args], sort_keys=True)
    llm_string = "quran_tool_v1" # Identifier for this specific tool version
    cached_result = QURAN_TOOL_CACHE.lookup(prompt=cache_key, llm_string=llm_string)
    if cached_result:
        logger.info("Cache hit for Quran verse image query")
        # LangChain cache returns a list of Generation objects
        return json.loads(cached_result[0].text)
    surah_array = [] 
    Quran_data = None
    try:
        Quran_data = get_Quran_data()
    except Exception as e:
        response_data = {
            "success": False,
            "verse_images": [],
            "error": "Data not available from Quran Cloud"
        }
        logger.error("Couldn't get data from the Quran Cloud: %s", e)
        return response_data

    for filter_args in args:
        # start with the complete copy of the Quran
        filtered_array = list(Quran_data)
        surah_args = filter_args.surah_args or SurahFilter()
        surah_arguments = {
            "number": surah_args.number,
            "number_min": surah_args.number_min,
            "number_max": surah_args.number_max,
            "name" : surah_args.name,
            "englishName" : normalize_surah(surah_args.englishName, surah_name_english_array),
            "englishNameTranslation": normalize_surah(surah_args.englishNameTranslation, surah_name_english_translation_array),
            "revelationType": surah_args.revelationType
        }

        verse_args = filter_args.verse_args or VerseFilter()
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
            "limit": verse_args.limit
        }

        # filter out the non null parameters
        clean_args_surah = {k:v for k,v in surah_arguments.items() if v is not None}
        clean_args_verse = {k:v for k,v in verse_arguments.items() if v is not None}

        logger.debug("Clean Surah arguments: %s", clean_args_surah)
        logger.debug("Clean Verse arguments: %s", clean_args_verse)
        # Initialize filter conditions array for surah filtering    
        surah_filter_conditions = []    
        # build the filter
        for k,v in clean_args_surah.items():        
            min_or_max = "min" if "_min" in k else ("max" if "_max" in k else None)

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
            if k == "limit":
                continue
            min_or_max = "min" if "_min" in k else ("max" if "_max" in k else None) 
            # check for minimum and maximum values in the key
            
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
                new_surah = surah.copy()
                limit = clean_args_verse.get("limit", 1)
                new_surah['ayahs'] = filtered_verses[:limit]
                new_filtered_array.append(new_surah)

        filtered_array = new_filtered_array
        for surah in filtered_array:
            surah_number = surah["number"]
            new_ayahs = []
            for ayah in surah["ayahs"]:
                verse_number = ayah["numberInSurah"]
                image_url = f"{QURAN_IMAGE_BASE_API}/{surah_number}_{verse_number}.png"

                new_ayahs.append({
                    "numberInSurah": verse_number,
                    "text": ayah.get("text"),
                    "verse_image_url": image_url,
                })

            surah_array.append({
                "name": surah.get("name", ""),
                "englishName": surah.get("englishName", ""),
                "ayahs": new_ayahs,
            })
    if surah_array:
        response_data = {
            "success": True,
            "verse_images": surah_array,
            "error": None
        }
        
        QURAN_TOOL_CACHE.update(
            prompt=cache_key,
            llm_string=llm_string,
            return_val=[Generation(text=json.dumps(response_data))]
        )

        return response_data
    else:
        response_data = {
            "success": False,
            "verse_images": [],
            "error": "No verse images found for the provided filters"

        }

        return response_data
    