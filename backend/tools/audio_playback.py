"""
Quran Audio Playback Tool
Provides audio URLs for Quran recitation
"""

import httpx
from typing import Optional, Dict, Any
import re
import logging
from langchain_core.tools import tool
from tools.utils import normalize_surah
from data.data import surah_name_english_array, comprehensive_surah_metadata

logger = logging.getLogger(__name__)

QURAN_API_BASE = "https://api.alquran.cloud/v1"

RECITERS = {
    "alafasy": {"name": "Mishary Rashid Alafasy", "identifier": "ar.alafasy"},
    "abdulbasit": {"name": "Abdul Basit", "identifier": "ar.abdulbasitmurattal"},
    "sudais": {"name": "Abdur-Rahman As-Sudais", "identifier": "ar.abdurrahmaansudais"},
    "husary": {"name": "Mahmoud Khalil Al-Husary", "identifier": "ar.husary"},
    "minshawi": {"name": "Mohamed Siddiq Al-Minshawi", "identifier": "ar.minshawi"},
    "saad": {"name": "Saad Al-Ghamdi", "identifier": "ar.saadalghamadi"},
    "shaatri": {"name": "Abu Bakr al-Shatri", "identifier": "ar.shaatree"},
}

class InvalidSurahError(Exception):
    pass

class InvalidAyahError(Exception):
    pass

class QuranAPIError(Exception):
    pass

def get_available_reciters():
    return [{"id": key, "name": value["name"]} for key, value in RECITERS.items()]

def get_quran_audio(
    surah: Optional[int] = None,
    ayah: Optional[int] = None,
    reciter: str = "alafasy"
) -> Dict[str, Any]:
    """Main function to get Quran audio URLs (Synchronous)"""
    
    if not surah or surah < 1 or surah > 114:
        raise InvalidSurahError(f"Invalid Surah number: {surah}. Must be between 1-114")
    
    reciter_info = RECITERS.get(reciter.lower())
    if not reciter_info:
        reciter_info = RECITERS["alafasy"]
    
    try:
        with httpx.Client() as client:
            if ayah:
                url = f"{QURAN_API_BASE}/ayah/{surah}:{ayah}/{reciter_info['identifier']}"

                print("URL to fetch Quran Data", url)
                response = client.get(url, timeout=30.0)
                if response.status_code != 200:
                    raise QuranAPIError(f"API returned status {response.status_code}")
                data = response.json()["data"]
                return {
                    "success": True, 
                    "type": "single_ayah",
                    "surah": {"number": data["surah"]["number"], "englishName": data["surah"]["englishName"]},
                    "ayah": {"number": data["numberInSurah"], "text": data.get("text", ""), "audio_url": data.get("audio", "")},
                    "reciter": {"name": reciter_info["name"], "identifier": reciter}
                }
            else:
                
                url = f"{QURAN_API_BASE}/surah/{surah}/{reciter_info['identifier']}"
                response = client.get(url, timeout=30.0)
                if response.status_code != 200:
                    raise QuranAPIError(f"API returned status {response.status_code}")
                data = response.json()["data"]
                ayahs = [{"number": a["numberInSurah"], "audio_url": a.get("audio", "")} for a in data["ayahs"]]
                return {
                    "success": True,
                    "type": "complete_surah",
                    "surah": {"number": data["number"], "englishName": data["englishName"], "numberOfAyahs": data["numberOfAyahs"]},
                    "ayahs": ayahs,
                    "reciter": {"name": reciter_info["name"], "identifier": reciter}
                }
    except Exception as e:
        raise QuranAPIError(str(e))

def parse_quran_audio_request(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Parse natural language audio requests using Fuzzy Matching (RapidFuzz).
    """
    if not user_input: return None
    user_input = user_input.lower()
    
    if "ayatul kursi" in user_input or "ayat ul kursi" in user_input:
        return {"surah": 2, "ayah": 255}
    
    number_match = re.search(r'(?:surah|surat)\s+(\d+)', user_input)
    if number_match:
        surah_num = int(number_match.group(1))
        ayah_match = re.search(r'(?:ayah|ayat|verse)\s*(\d+)', user_input)
        if ayah_match:
            return {"surah": surah_num, "ayah": int(ayah_match.group(1))}
        return {"surah": surah_num}

    name_match = re.search(r'(?:surah|surat)\s+([a-z\-\s\']+)', user_input)
    
    if name_match:
        raw_name = name_match.group(1).strip()
        
        best_match_name = normalize_surah(raw_name, surah_name_english_array)
        
        if best_match_name:
            surah_number = None
            for meta in comprehensive_surah_metadata:
              
                meta_name = meta.get("englishName")
                if meta_name == best_match_name:
                    surah_number = int(meta.get("surah_number"))
                    break
            
            if surah_number:
                
                ayah_match = re.search(r'(?:ayah|ayat|verse)\s*(\d+)', user_input)
                if ayah_match:
                    return {"surah": surah_number, "ayah": int(ayah_match.group(1))}
                return {"surah": surah_number}

    return None

@tool
def play_quran_audio(query: str) -> str:
    """
    Play Quran audio recitation for requested surah or ayah.
    """
    print(f"\n=== calling play_quran_audio (SYNC) ===\n📥 user: {query}\n")
    logging.info(f"[AUDIO_TOOL] Tool called with query: {query}")

    try:
        parsed = parse_quran_audio_request(query)
        logging.info(f"[AUDIO_TOOL] Parsed result: {parsed}")

        if not parsed:
            return "I couldn't understand which surah you want to listen to."

        result = get_quran_audio(
            surah=parsed["surah"],
            ayah=parsed.get("ayah"),
            reciter="alafasy"
        )

        if not result.get("success"):
            return f"Sorry, couldn't fetch audio: {result.get('error', 'Unknown error')}"

        if result["type"] == "single_ayah":
            return f"Audio URL for **Surah {result['surah']['englishName']}**, Ayah {result['ayah']['number']}: {result['ayah']['audio_url']}"
        else:
            return f"Audio URL for **Surah {result['surah']['englishName']}**: {result['ayahs'][0]['audio_url']} (Full surah available)"

    except Exception as e:
        logging.exception(f"[AUDIO_TOOL] Exception: {str(e)}")
        return f"Error fetching audio: {str(e)}"