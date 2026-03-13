from rapidfuzz import process, fuzz
import unicodedata
import re

from typing import Optional

def clean_text(text: str) -> str:
    return text.replace("\x00", "")

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

def normalize_reciter_name(name:str, array:list) -> str | None:
    """
    Converts user-provided name → canonical name using fuzzy match.
    Returns None if input is empty or extremely unclear.
    """

    if not name:
        return array[0]

    name = name.strip().lower()
    best, score,_ = process.extractOne(
        name,
        array,
        scorer = fuzz.WRatio
    )

    if score < 65:
        return array[0]
    
    return best

def clean_surah_name(name: str) -> str:
    """
    Aggressively cleans Surah names:
    1. Removes Markdown (*, _)
    2. Normalizes Unicode (ā -> a, ī -> i)
    3. Removes hyphens and special chars
    """
    if not name: return ""
    
    name = name.replace("*", "").replace("_", "")
    
    # Unicode Normalization 
    # "Yā-Sīn" -> "Ya-Sin" and "Ar-Rahmān" -> "Ar-Rahman"
    normalized = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    
    # "Ya-Sin" -> "Ya Sin" (easier for fuzzy match)
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', normalized)
    
    return cleaned.strip()

def get_surah_id_from_name(name: str) -> Optional[int]:
    """
    Tries to find Surah ID from a name using manual overrides first.
    Handles 'An-Nisa', 'Nisaa', 'Ar-Rahman', etc.
    """
    if not name: return None
    
    clean = name.lower()
    clean = unicodedata.normalize('NFKD', clean).encode('ASCII', 'ignore').decode('utf-8')
    clean = re.sub(r'[^a-z0-9]', '', clean)
    
    overrides = {
        "fatiha": 1, "alfatiha": 1,
        "baqara": 2, "baqarah": 2, "albaqara": 2, "albaqarah": 2, "bakara": 2,
        "imran": 3, "alimran": 3, "aliimran": 3,
        "nisa": 4, "annisa": 4, "nisaa": 4, "annisaa": 4, 
        "maidah": 5,"maida": 5, "almaidah": 5,
        "anams": 6, "anam": 6, "alanam": 6,
        "araf": 7, "alaraf": 7,
        "anfal": 8, "alanfal": 8,
        "tawbah": 9, "tawba": 9, "altawbah": 9, "tauba": 9,
        "younus": 10, "yunus": 10,
        "yusuf": 12, "yousuf": 12, 
        "kahf": 18, "alkahf": 18, 
        "maryam": 19, "mary": 19,
        "taha": 20, "Taa-Haa": 20,
        "yasin": 36, "yas": 36, "yaseen": 36, "yassin": 36, "ya-sin": 36,
        "rahman": 55, "arrahman": 55, "rehman": 55, "arrehman": 55,
        "waqiah": 56, "alwaqiah": 56, "waqia": 56,
        "mulk": 67, "almulk": 67,
        "jinn": 72, "aljinn": 72,
        "ikhlas": 112, "alikhlas": 112,
        "falaq": 113, "alfalaq": 113,
        "nas": 114, "annas": 114,
        "Ar-Ra'd": 13, "raad": 13, "rad": 13,
        "AlHijr": 15, "Hijr": 15, 
        "Ash-Shu'araa": 26, "ashora": 26,
        "An-Naba": 78, "naba": 78,
        "Al-Burooj": 85, "buruj": 85, "borooj": 85,
        "Al-A'laa": 87, "alaa": 87, "ala": 87,
        "Al-Fajr": 89, "fajr": 89,
        "Al-Lail": 92, "lail": 92,
        "Ad-Dhuhaa": 93, "duha": 93, "duhaa": 93, "adduha": 93, "dhuha": 93, "wadduha": 93,
        "Ash-Sharh": 94, "ashrh": 94, "alashrh": 94, "ashrah": 94,
        "Al-Alaq": 96, "alaq": 96, "alalaq": 96, "alaaq": 96,
    }
    
    if clean in overrides:
        return overrides[clean]
    for key, val in overrides.items():
        if key in clean:
            return val
            
    return None

