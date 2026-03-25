import operator
import os
import requests
from data.data import surah_name_english_translation_array, surah_name_english_array
from pydantic import BaseModel, Field
from typing import Optional
from tools.normalizeName import normalize_surah
from langchain.tools import tool
from typing import List, Literal


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


class Filters(BaseModel):
    surah_args: SurahFilter = None
    verse_args: VerseFilter = None


class FiltersList(BaseModel):  # New top-level schema
    """List of Quran filters"""
    args: List[Filters] = Field(default_factory=list, description="List of filter queries")

@tool(args_schema = FiltersList)
def Search_Quran_By_filters(args: List[Filters] = None) -> List[str]:

    """Search Quran using metadata filters
    This tool does an exact filter search on the Quran verses stored in the vector database. It does not use embeddings or similarity search. Only fields that are provided (not None) are used as filter conditions.
    
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
            Exact ayah number within the surah.

        5. **numberInSurah_min (int)**  
            Minimum ayah number within the surah.

        6. **numberInSurah_max (int)**  
            Maximum ayah number within the surah.

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
    1. Used for queries that can retreive data through specific fields filtering.
    2. Uses filter queries for fetching data. 

    **EXAMPLE QUERIES:**
    1. What is verse number 5 of surah fatiha.
    2. What is the verse number 5 of Al Quran.
    3. What does Surah Fatiha verse 5 says about Guidance and worshipping Allah.
    4. Is verse number 128 of Surah Baqarah a Sajda verse.
    5. Give me translation of verse 13 of Surah An'aam and verse 50 of Al-Baqarah.
    6. Give me verse 5 of Surah Baqarah, verse 9 of surah An'aam and verse 10 of Surah Nisa.
    7. Give me verses 1-10 of surah Baqarah, Quraysh and Bani Israeel.
    
    """

    if not args:
        return "No filters provided"

    # initialize a results array to concatenate results
    results_array = []    
    # fetch the data
    response = requests.get("https://api.alquran.cloud/v1/quran/en.asad")

    if not response.ok:
        print("Couldn't get data from the Quran Cloud")
        return "Couldn't get data from the Quran Cloud"
    
    Quran_data = response.json()['data']['surahs']

    for filter_args in args:
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
        }

        #filter out the non null parameters
        clean_args_surah = {k:v for k,v in surah_arguments.items() if v is not None}
        clean_args_verse = {k:v for k,v in verse_arguments.items() if v is not None}

        print("Clean Surah arguments", clean_args_surah)
        print("Clean Verse arguments", clean_args_verse)

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
                new_surah = surah.copy()
                new_surah['ayahs'] = filtered_verses
                new_filtered_array.append(new_surah)

        filtered_array = new_filtered_array
        
        for surah in filtered_array:
            surah_string = ""
            
            surah_string += f"Surah {surah['number']}: {surah['englishName']}\n"
            surah_string += f"Arabic Name: {surah['name']}\n"
            surah_string += f'Translation: "{surah["englishNameTranslation"]}"\n'
            surah_string += f"Revelation Type: {surah['revelationType']}\n"
            surah_string += f"Number of Ayahs: {len(surah['ayahs'])}\n\n"
            
            for i, ayah in enumerate(surah['ayahs']):
                surah_string += f"Ayah {ayah['numberInSurah']} (Global #{ayah['number']}):\n"
                surah_string += f'"{ayah["text"]}"\n'
                surah_string += f"Details: Juz {ayah['juz']}, Manzil {ayah['manzil']}, Page {ayah['page']}, Ruku {ayah['ruku']}, HizbQuarter {ayah['hizbQuarter']}, Sajda: {ayah['sajda']}\n"
                
                if i < len(surah['ayahs']) - 1:
                    surah_string += "-" * 40 + "\n"
            
            results_array.append(surah_string)

    if results_array:
        print(f"Total queries processed: {len(results_array)}")
        if results_array:
            print("filtered results", results_array)
            
            return results_array
        else:
            return "No results found for the user query"
    else:
        return "No results found for the user query"


