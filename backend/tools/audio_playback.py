"""
Quran Audio Playback Tool
Provides audio URLs for Quran recitation
"""

import asyncio
import httpx
from typing import Optional, Dict, Any
import re
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

QURAN_API_BASE = "https://api.alquran.cloud/v1"
# Available reciters
RECITERS = {
    "alafasy": {"name": "Mishary Rashid Alafasy", "identifier": "ar.alafasy"},
    "abdulbasit": {"name": "Abdul Basit", "identifier": "ar.abdulbasitmurattal"},
    "sudais": {"name": "Abdur-Rahman As-Sudais", "identifier": "ar.abdurrahmaansudais"},
    "husary": {"name": "Mahmoud Khalil Al-Husary", "identifier": "ar.husary"},
    "minshawi": {"name": "Mohamed Siddiq Al-Minshawi", "identifier": "ar.minshawi"},
    "saad": {"name": "Saad Al-Ghamdi", "identifier": "ar.saadalghamadi"},
    "shaatri": {"name": "Abu Bakr al-Shatri", "identifier": "ar.shaatree"},
}

# Surah names mapping
SURAH_NAMES = {
    "fatiha": 1, "al-fatiha": 1, "الفاتحة": 1,
    "baqarah": 2, "al-baqarah": 2, "البقرة": 2,
    "imran": 3, "aal-e-imran": 3, "آل عمران": 3,
    "nisa": 4, "an-nisa": 4, "النساء": 4,
    "maidah": 5, "al-maidah": 5, "المائدة": 5,
    "anam": 6, "al-anam": 6, "الأنعام": 6,
    "araf": 7, "al-araf": 7, "الأعراف": 7,
    "anfal": 8, "al-anfal": 8, "الأنفال": 8,
    "tawbah": 9, "at-tawbah": 9, "التوبة": 9,
    "yunus": 10, "يونس": 10,
    "hud": 11, "هود": 11,
    "yusuf": 12, "يوسف": 12,
    "raad": 13, "ar-raad": 13, "الرعد": 13,
    "ibrahim": 14, "إبراهيم": 14,
    "hijr": 15, "al-hijr": 15, "الحجر": 15,
    "nahl": 16, "an-nahl": 16, "النحل": 16,
    "isra": 17, "al-isra": 17, "الإسراء": 17,
    "kahf": 18, "al-kahf": 18, "الكهف": 18,
    "maryam": 19, "مريم": 19,
    "taha": 20, "طه": 20,
    "anbiya": 21, "al-anbiya": 21, "الأنبياء": 21,
    "hajj": 22, "al-hajj": 22, "الحج": 22,
    "muminun": 23, "al-muminun": 23, "المؤمنون": 23,
    "nur": 24, "an-nur": 24, "النور": 24,
    "furqan": 25, "al-furqan": 25, "الفرقان": 25,
    "shuara": 26, "ash-shuara": 26, "الشعراء": 26,
    "naml": 27, "an-naml": 27, "النمل": 27,
    "qasas": 28, "al-qasas": 28, "القصص": 28,
    "ankabut": 29, "al-ankabut": 29, "العنكبوت": 29,
    "rum": 30, "ar-rum": 30, "الروم": 30,
    "luqman": 31, "لقمان": 31,
    "sajdah": 32, "as-sajdah": 32, "السجدة": 32,
    "ahzab": 33, "al-ahzab": 33, "الأحزاب": 33,
    "saba": 34, "سبأ": 34,
    "fatir": 35, "فاطر": 35,
    "yaseen": 36, "yasin": 36, "يس": 36,
    "saffat": 37, "as-saffat": 37, "الصافات": 37,
    "sad": 38, "ص": 38,
    "zumar": 39, "az-zumar": 39, "الزمر": 39,
    "ghafir": 40, "غافر": 40,
    "fussilat": 41, "فصلت": 41,
    "shura": 42, "ash-shura": 42, "الشورى": 42,
    "zukhruf": 43, "az-zukhruf": 43, "الزخرف": 43,
    "dukhan": 44, "ad-dukhan": 44, "الدخان": 44,
    "jathiyah": 45, "al-jathiyah": 45, "الجاثية": 45,
    "ahqaf": 46, "al-ahqaf": 46, "الأحقاف": 46,
    "muhammad": 47, "محمد": 47,
    "fath": 48, "al-fath": 48, "الفتح": 48,
    "hujurat": 49, "al-hujurat": 49, "الحجرات": 49,
    "qaf": 50, "ق": 50,
    "dhariyat": 51, "adh-dhariyat": 51, "الذاريات": 51,
    "tur": 52, "at-tur": 52, "الطور": 52,
    "najm": 53, "an-najm": 53, "النجم": 53,
    "qamar": 54, "al-qamar": 54, "القمر": 54,
    "rahman": 55, "ar-rahman": 55, "الرحمن": 55,
    "waqiah": 56, "al-waqiah": 56, "الواقعة": 56,
    "hadid": 57, "al-hadid": 57, "الحديد": 57,
    "mujadila": 58, "al-mujadila": 58, "المجادلة": 58,
    "hashr": 59, "al-hashr": 59, "الحشر": 59,
    "mumtahina": 60, "al-mumtahina": 60, "الممتحنة": 60,
    "saff": 61, "as-saff": 61, "الصف": 61,
    "jumuah": 62, "al-jumuah": 62, "الجمعة": 62,
    "munafiqun": 63, "al-munafiqun": 63, "المنافقون": 63,
    "taghabun": 64, "at-taghabun": 64, "التغابن": 64,
    "talaq": 65, "at-talaq": 65, "الطلاق": 65,
    "tahrim": 66, "at-tahrim": 66, "التحريم": 66,
    "mulk": 67, "al-mulk": 67, "الملك": 67,
    "qalam": 68, "al-qalam": 68, "القلم": 68,
    "haqqah": 69, "al-haqqah": 69, "الحاقة": 69,
    "maarij": 70, "al-maarij": 70, "المعارج": 70,
    "nuh": 71, "نوح": 71,
    "jinn": 72, "al-jinn": 72, "الجن": 72,
    "muzzammil": 73, "al-muzzammil": 73, "المزمل": 73,
    "muddathir": 74, "al-muddathir": 74, "المدثر": 74,
    "qiyamah": 75, "al-qiyamah": 75, "القيامة": 75,
    "insan": 76, "al-insan": 76, "الإنسان": 76,
    "mursalat": 77, "al-mursalat": 77, "المرسلات": 77,
    "naba": 78, "an-naba": 78, "النبأ": 78,
    "naziat": 79, "an-naziat": 79, "النازعات": 79,
    "abasa": 80, "عبس": 80,
    "takwir": 81, "at-takwir": 81, "التكوير": 81,
    "infitar": 82, "al-infitar": 82, "الإنفطار": 82,
    "mutaffifin": 83, "al-mutaffifin": 83, "المطففين": 83,
    "inshiqaq": 84, "al-inshiqaq": 84, "الإنشقاق": 84,
    "buruj": 85, "al-buruj": 85, "البروج": 85,
    "tariq": 86, "at-tariq": 86, "الطارق": 86,
    "ala": 87, "al-ala": 87, "الأعلى": 87,
    "ghashiyah": 88, "al-ghashiyah": 88, "الغاشية": 88,
    "fajr": 89, "al-fajr": 89, "الفجر": 89,
    "balad": 90, "al-balad": 90, "البلد": 90,
    "shams": 91, "ash-shams": 91, "الشمس": 91,
    "layl": 92, "al-layl": 92, "الليل": 92,
    "duha": 93, "ad-duha": 93, "الضحى": 93,
    "sharh": 94, "ash-sharh": 94, "الشرح": 94,
    "tin": 95, "at-tin": 95, "التين": 95,
    "alaq": 96, "al-alaq": 96, "العلق": 96,
    "qadr": 97, "al-qadr": 97, "القدر": 97,
    "bayyinah": 98, "al-bayyinah": 98, "البينة": 98,
    "zalzalah": 99, "az-zalzalah": 99, "الزلزلة": 99,
    "adiyat": 100, "al-adiyat": 100, "العاديات": 100,
    "qariah": 101, "al-qariah": 101, "القارعة": 101,
    "takathur": 102, "at-takathur": 102, "التكاثر": 102,
    "asr": 103, "al-asr": 103, "العصر": 103,
    "humazah": 104, "al-humazah": 104, "الهمزة": 104,
    "fil": 105, "al-fil": 105, "الفيل": 105,
    "quraysh": 106, "قريش": 106,
    "maun": 107, "al-maun": 107, "الماعون": 107,
    "kawthar": 108, "al-kawthar": 108, "الكوثر": 108,
    "kafirun": 109, "al-kafirun": 109, "الكافرون": 109,
    "nasr": 110, "an-nasr": 110, "النصر": 110,
    "masad": 111, "al-masad": 111, "المسد": 111,
    "ikhlas": 112, "al-ikhlas": 112, "الإخلاص": 112,
    "falaq": 113, "al-falaq": 113, "الفلق": 113,
    "nas": 114, "an-nas": 114, "الناس": 114,
}

# Custom exceptions
class InvalidSurahError(Exception):
    pass

class InvalidAyahError(Exception):
    pass

class QuranAPIError(Exception):
    pass


async def get_available_reciters():
    """Get list of available reciters"""
    return [
        {"id": key, "name": value["name"]}
        for key, value in RECITERS.items()
    ]


def get_quran_audio(
    surah: Optional[int] = None,
    ayah: Optional[int] = None,
    reciter: str = "alafasy"
) -> Dict[str, Any]:
    """
    Main function to get Quran audio URLs
    
    Args:
        surah: Surah number (1-114)
        ayah: Ayah number (optional, if not provided returns full surah)
        reciter: Reciter identifier
    
    Returns:
        Dict with audio data or error
    """
    
    # Validate surah
    if not surah or surah < 1 or surah > 114:
        raise InvalidSurahError(f"Invalid Surah number: {surah}. Must be between 1-114")
    
    # Get reciter info
    reciter_info = RECITERS.get(reciter.lower())
    if not reciter_info:
        reciter_info = RECITERS["alafasy"]  # Default fallback
    
    try:
        with httpx.Client() as client:
            # If specific ayah requested
            if ayah:
                url = f"{QURAN_API_BASE}/ayah/{surah}:{ayah}/{reciter_info['identifier']}"
                response = client.get(url, timeout=30.0)
                
                if response.status_code != 200:
                    raise QuranAPIError(f"API returned status {response.status_code}")
                
                data = response.json()["data"]
                
                return {
                    "success": True,
                    "type": "single_ayah",
                    "surah": {
                        "number": data["surah"]["number"],
                        "name": data["surah"]["name"],
                        "englishName": data["surah"]["englishName"]
                    },
                    "ayah": {
                        "number": data["numberInSurah"],
                        "text": data.get("text", ""),
                        "audio_url": data.get("audio", "")
                    },
                    "reciter": {
                        "name": reciter_info["name"],
                        "identifier": reciter
                    }
                }
            
            # If full surah requested
            else:
                url = f"{QURAN_API_BASE}/surah/{surah}/{reciter_info['identifier']}"
                response = client.get(url, timeout=30.0)
                
                if response.status_code != 200:
                    raise QuranAPIError(f"API returned status {response.status_code}")
                
                data = response.json()["data"]
                
                ayahs = []
                for ayah_data in data["ayahs"]:
                    ayahs.append({
                        "number": ayah_data["numberInSurah"],
                        "text": ayah_data.get("text", ""),
                        "audio_url": ayah_data.get("audio", "")
                    })
                
                return {
                    "success": True,
                    "type": "complete_surah",
                    "surah": {
                        "number": data["number"],
                        "name": data["name"],
                        "englishName": data["englishName"],
                        "englishNameTranslation": data.get("englishNameTranslation", ""),
                        "numberOfAyahs": data["numberOfAyahs"],
                        "revelationType": data.get("revelationType", "")
                    },
                    "ayahs": ayahs,
                    "reciter": {
                        "name": reciter_info["name"],
                        "identifier": reciter
                    }
                }
    
    except httpx.TimeoutException:
        raise QuranAPIError("Request timeout - please try again")
    except httpx.RequestError as e:
        raise QuranAPIError(f"Network error: {str(e)}")
    except KeyError as e:
        raise QuranAPIError(f"Invalid API response: {str(e)}")


def parse_quran_audio_request(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Parse natural language audio requests
    
    Examples:
        "listen to surah fatiha" → {surah: 1}
        "play ayatul kursi" → {surah: 2, ayah: 255}
        "recite surah 36" → {surah: 36}
        "play surah 2 ayah 255" → {surah: 2, ayah: 255}
    """
    user_input = user_input.lower()
    
    # Special cases
    if "ayatul kursi" in user_input or "ayat ul kursi" in user_input:
        return {"surah": 2, "ayah": 255}
    
    # Check for surah names
    for name, number in SURAH_NAMES.items():
        if name in user_input:
            # Check if ayah number mentioned
            ayah_match = re.search(r'ayah?\s*(\d+)', user_input)
            if ayah_match:
                return {"surah": number, "ayah": int(ayah_match.group(1))}
            return {"surah": number}
    
    # Check for "surah X ayah Y" pattern
    match = re.search(r'surah\s*(\d+)\s*(?:ayah?\s*(\d+))?', user_input)
    if match:
        result = {"surah": int(match.group(1))}
        if match.group(2):
            result["ayah"] = int(match.group(2))
        return result
    
    return None


@tool
def play_quran_audio(query: str) -> str:
    """
    Play Quran audio recitation for requested surah or ayah.
    
    Use this tool when user wants to listen to Quran.
    
    Args:
        query: User's request (e.g., "Surah Fatiha", "Ayatul Kursi")
    
    Returns:
        Audio URL and details
    """
    print("\n" + "="*60)
    print("calling play_quran_audio (ASYNC)")
    print(f"📥 user:  {query}")
    print("="*60 + "\n")

    logging.info(f"[AUDIO_TOOL] Tool called with query: {query}")

    try:
        # CHANGE: Use await directly instead of asyncio.run()
        parsed = parse_quran_audio_request(query)
        logging.info(f"[AUDIO_TOOL] Parsed result: {parsed}")

        if not parsed:
            return "I couldn't understand which surah you want to listen to."

        # Get audio
        logging.info(f"[AUDIO_TOOL] Fetching audio for surah={parsed['surah']}")
        
        # CHANGE: Use await directly instead of asyncio.run()
        result = get_quran_audio(
            surah=parsed["surah"],
            ayah=parsed.get("ayah"),
            reciter="alafasy"
        )

        if not result.get("success"):
            return f"Sorry, couldn't fetch audio: {result.get('error', 'Unknown error')}"

        # Format response
        if result["type"] == "single_ayah":
            return f"""
Here is the audio for **Surah {result['surah']['englishName']}**, Ayah {result['ayah']['number']}:

🎧 **Audio URL:** {result['ayah']['audio_url']}

📖 **Arabic Text:** {result['ayah']['text']}

🎙️ **Reciter:** {result['reciter']['name']}
""".strip()
        else:
            urls = "\n".join([f"  - Ayah {a['number']}: {a['audio_url']}" for a in result['ayahs'][:5]])
            return f"""
Here is the audio for **Surah {result['surah']['englishName']}**:

🎙️ **Reciter:** {result['reciter']['name']}

🎧 **Audio links:**
{urls}

(Total: {result['surah']['numberOfAyahs']} ayahs)
""".strip()

    except Exception as e:
        logging.exception(f"[AUDIO_TOOL] Exception: {str(e)}")
        return f"Error fetching audio: {str(e)}"