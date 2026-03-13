import requests
import operator
from data.data import reciters_name_array, surah_name_english_array, surah_name_english_translation_array
from tools.normalizeName import normalize_reciter_name, normalize_surah
from pydantic import BaseModel, Field
from typing import Optional
from langchain.tools import tool
from typing import List, Literal
from langchain.tools import tool
import json
import logging
from langchain_core.caches import InMemoryCache
from langchain_core.outputs import Generation
from threading import Lock
from collections import OrderedDict

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
    surah_args: Optional[SurahFilter] = None
    verse_args: Optional[VerseFilter] = None


QURAN_API_BASE = "http://api.alquran.cloud/v1/quran"
AUDIO_TOOL_CACHE = InMemoryCache(maxsize=1000)
logger = logging.getLogger(__name__)
MAX_RECITERS_IN_CACHE = 6
AUDIO_DATA_LOCK = Lock()
AUDIO_DATA_CACHE = OrderedDict()

class QuranAudioInput(BaseModel):
    args: Optional[List[Filters]] = None
    reciter: str = "ar.alafasy"

def get_Quran_Audio_Data(reciter_identifier: str):
    """
LRU Cache Logic:

Cache contains:
    [alafasy, minshawi, sudais, ghamdi, husary, ajami]
     ↑ oldest                                   ↑ newest

User requests "alafasy":
    → Found in cache 
    → Use move_to_end() to move it to the end (now it becomes the most recent)
    → [minshawi, sudais, ghamdi, husary, ajami, alafasy]

Cache is full and a new reciter is requested:
    [minshawi, sudais, ghamdi, husary, ajami, alafasy]

User requests "bukhatir":
    → Not found in cache ✗
    → Cache is full (6/6)
    → Remove the oldest item (minshawi) 
    → Load "bukhatir" and add it to the end
    → [sudais, ghamdi, husary, ajami, alafasy, bukhatir]
"""
    global AUDIO_DATA_CACHE
    with AUDIO_DATA_LOCK:
        if reciter_identifier in AUDIO_DATA_CACHE:
           
            AUDIO_DATA_CACHE.move_to_end(reciter_identifier)
            logger.info("Data cache hit for reciter: %s", reciter_identifier)
        else:
            
            if len(AUDIO_DATA_CACHE) >= MAX_RECITERS_IN_CACHE:
                
                oldest_reciter = next(iter(AUDIO_DATA_CACHE))
                del AUDIO_DATA_CACHE[oldest_reciter]
                logger.info("Cache full — oldest reciter removed: %s", oldest_reciter)

            
            try:
                request_url = f'{QURAN_API_BASE}/{reciter_identifier}'
                response = requests.get(request_url, timeout=10)
                if not response.ok:
                    raise ValueError("Quran audio data not available")
                data = response.json()['data']['surahs']
                if not data:
                    raise ValueError("Quran audio data is empty")
                
                AUDIO_DATA_CACHE[reciter_identifier] = data
                logger.info("New reciter cached: %s | Cache size: %d/%d",
                            reciter_identifier, len(AUDIO_DATA_CACHE), MAX_RECITERS_IN_CACHE)
            except requests.Timeout:
                raise ValueError("Request to Quran API timed out")
            except requests.RequestException as e:
                raise ValueError(f"Error fetching Quran audio data: {e}")

        return AUDIO_DATA_CACHE[reciter_identifier]
    

@tool(args_schema = QuranAudioInput)
def get_Quran_Audio(args: List[Filters] = None, reciter:str = "ar.alafasy") -> List[str]:

    """Get Quran Audio using metadata filters
    This tool does an exact filter search on the Quran verses stored in the cloud and retreives audio for a particular verse or verses .Only fields that are provided (not None) are used as filter conditions.
    
    **ARGS:**

    1. --- args (List[Filters], optional) ---
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
    
    2. --- reciter ---
    
    **Notes:** Each Filters object represents a single surah–verse query. Multiple queries can be provided as a list of Filters.

    **PURPOSE:**
    1. Used for queries that can retreive data through specific fields filtering.
    2. Uses filter queries for fetching data. 

    **EXAMPLE QUERIES:**
    1. I want to listen to verse number 5 of surah fatiha.
    2. Play the verse number 5 of Al Quran.
    3. Play a sajda verse for me.
    5. Play the audio of verse 13 of Surah An'aam and verse 50 of Al-Baqarah.
    6. I want to listen to the recitation of verse 5 of Surah Baqarah, verse 9 of surah An'aam and verse 10 of Surah Nisa.
    7. I want to listen to verses 1-10 of surah Baqarah, Quraysh and Bani Israeel.
    """

    if not args:
        print("No filters provided")
        response_data = {
            "success": False,
            "audio_data": [],
            "error": "No filters provided"

        }
        return response_data
    
    cache_payload = {
        "args": [arg.model_dump() for arg in args],
        "reciter": reciter
    }
    cache_key = json.dumps(cache_payload, sort_keys=True)
    llm_string = "quran_audio_v1"

    cached_result = AUDIO_TOOL_CACHE.lookup(prompt=cache_key, llm_string=llm_string)
    if cached_result:
        logger.info(f"Audio cache hit for reciter: {reciter}")
        return json.loads(cached_result[0].text)
    
    surah_array = []    
    # fetch the data
    reciter_identifier = normalize_reciter_name(reciter, reciters_name_array)
    
    try:
        Quran_data = get_Quran_Audio_Data(reciter_identifier)
    except Exception as e:
        logger.error("Couldn't get data from the Quran Cloud: %s", e)
        return {
            "success": False,
            "audio_data": [],
            "error": "Data not available from Quran Cloud"
        }

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

        #filter out the non null parameters
        clean_args_surah = {k:v for k,v in surah_arguments.items() if v is not None}
        clean_args_verse = {k:v for k,v in verse_arguments.items() if v is not None}

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
                new_surah['ayahs'] = filtered_verses[:clean_args_verse['limit']]
                new_filtered_array.append(new_surah)

        filtered_array = new_filtered_array
        
        for surah in filtered_array:
            new_verses = []
            for verse in surah["ayahs"]:
                new_verses.append({
                    "audio": verse.get("audio") or (verse.get("audioSecondary") or [""])[0],
                    "numberInSurah": verse.get("numberInSurah"),
                    "juz": verse.get("juz", ""),
                    "manzil": verse.get("manzil", ""),
                    "ruku": verse.get("ruku", ""),
                    "sajda": verse.get("sajda")
                })

            surah_array.append({
                "name": surah.get("name", ""),
                "englishName": surah.get("englishName", ""),
                "englishNameTranslation": surah.get("englishNameTranslation", ""),
                "revelationType": surah.get("revelationType"),
                "ayahs": new_verses,
            })
        
    if surah_array:
        response_data = {
            "success": True,
            "audio_data": surah_array,
            "error": None

        }
        AUDIO_TOOL_CACHE.update(
            prompt=cache_key,
            llm_string=llm_string,
            return_val=[Generation(text=json.dumps(response_data))]
        )
        return response_data
    else:
        response_data = {
            "success": False,
            "audio_data": [],
            "error": "No audio data found for the provided filters"

        }
        return response_data
    