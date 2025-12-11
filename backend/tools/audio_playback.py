# import httpx
# import asyncio
# from typing import Optional
# import os

# # Audio playback libraries
# try:
#     import pygame
#     PYGAME_AVAILABLE = True
# except ImportError:
#     PYGAME_AVAILABLE = False
#     print("⚠️ pygame not installed. Install with: pip install pygame")

# try:
#     from playsound import playsound
#     PLAYSOUND_AVAILABLE = True
# except ImportError:
#     PLAYSOUND_AVAILABLE = False
#     print("⚠️ playsound not installed. Install with: pip install playsound")

# QURAN_API_BASE = "https://api.alquran.cloud/v1"

# # Popular reciters
# RECITERS = {
#     "alafasy": "ar.alafasy",  # Mishary Rashid Alafasy
#     "abdulbasit": "ar.abdulbasitmurattal",  # Abdul Basit
#     "sudais": "ar.abdurrahmaansudais",  # Abdur-Rahman As-Sudais
#     "husary": "ar.husary",  # Mahmoud Khalil Al-Husary
#     "minshawi": "ar.minshawi",  # Mohamed Siddiq Al-Minshawi
# }


# async def download_audio(url: str, filename: str) -> str:
#     """Download audio file from URL"""
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url, timeout=30.0)
            
#             if response.status_code == 200:
#                 with open(filename, 'wb') as f:
#                     f.write(response.content)
#                 return filename
#             else:
#                 raise Exception(f"Failed to download audio: {response.status_code}")
#     except Exception as e:
#         raise Exception(f"Download error: {str(e)}")


# def play_audio_file(filepath: str):
#     """Play audio file using available library"""
#     if PYGAME_AVAILABLE:
#         # Using pygame
#         pygame.mixer.init()
#         pygame.mixer.music.load(filepath)
#         pygame.mixer.music.play()
        
#         # Wait until playback finishes
#         while pygame.mixer.music.get_busy():
#             pygame.time.Clock().tick(10)
            
#     elif PLAYSOUND_AVAILABLE:
#         # Using playsound
#         playsound(filepath)
        
#     else:
#         print("❌ No audio library available!")
#         print("Install one of these:")
#         print("  pip install pygame")
#         print("  pip install playsound")


# async def get_ayah_audio_url(surah_id: int, ayah_number: int, reciter: str = "alafasy") -> str:
#     """Get audio URL for specific ayah"""
#     reciter_id = RECITERS.get(reciter, "ar.alafasy")
    
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{QURAN_API_BASE}/ayah/{surah_id}:{ayah_number}/{reciter_id}",
#                 timeout=10.0
#             )
            
#             if response.status_code == 200:
#                 data = response.json()["data"]
#                 audio_url = data.get("audio", "")
                
#                 if not audio_url:
#                     raise Exception("Audio URL not found")
                
#                 return audio_url
#             else:
#                 raise Exception(f"API error: {response.status_code}")
                
#     except Exception as e:
#         raise Exception(f"Failed to get audio: {str(e)}")


# async def get_surah_audio_urls(surah_id: int, reciter: str = "alafasy") -> list:
#     """Get all audio URLs for a surah"""
#     reciter_id = RECITERS.get(reciter, "ar.alafasy")
    
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{QURAN_API_BASE}/surah/{surah_id}/{reciter_id}",
#                 timeout=15.0
#             )
            
#             if response.status_code == 200:
#                 data = response.json()["data"]
#                 audio_urls = [ayah.get("audio", "") for ayah in data["ayahs"]]
#                 return [url for url in audio_urls if url]
#             else:
#                 raise Exception(f"API error: {response.status_code}")
                
#     except Exception as e:
#         raise Exception(f"Failed to get surah audio: {str(e)}")


# # ==================== MAIN FUNCTIONS ====================

# async def play_ayah(surah_id: int, ayah_number: int, reciter: str = "alafasy"):
#     """
#     Play specific ayah audio
    
#     Args:
#         surah_id: Surah number (1-114)
#         ayah_number: Ayah number within surah
#         reciter: Reciter name (alafasy, abdulbasit, sudais, husary, minshawi)
    
#     Example:
#         await play_ayah(1, 1)  # Play Surah Al-Fatiha, Ayah 1
#         await play_ayah(2, 255, "abdulbasit")  # Play Ayatul Kursi with Abdul Basit
#     """
#     print(f"🎧 Playing Surah {surah_id}, Ayah {ayah_number} ({reciter})...")
    
#     try:
#         # Get audio URL
#         audio_url = await get_ayah_audio_url(surah_id, ayah_number, reciter)
#         print(f"📥 Downloading audio...")
        
#         # Download audio
#         filename = f"ayah_{surah_id}_{ayah_number}.mp3"
#         await download_audio(audio_url, filename)
        
#         print(f"▶️  Playing...")
#         # Play audio
#         play_audio_file(filename)
        
#         # Cleanup
#         if os.path.exists(filename):
#             os.remove(filename)
            
#         print("✅ Playback completed!")
        
#     except Exception as e:
#         print(f"❌ Error: {str(e)}")


# async def play_surah(surah_id: int, reciter: str = "alafasy", start_ayah: int = 1, end_ayah: Optional[int] = None):
#     """
#     Play complete surah or specific range
    
#     Args:
#         surah_id: Surah number (1-114)
#         reciter: Reciter name
#         start_ayah: Starting ayah (default: 1)
#         end_ayah: Ending ayah (default: None = till end)
    
#     Example:
#         await play_surah(1)  # Play complete Surah Al-Fatiha
#         await play_surah(2, start_ayah=1, end_ayah=5)  # Play first 5 ayahs of Al-Baqarah
#     """
#     print(f"🎧 Playing Surah {surah_id} ({reciter})...")
    
#     try:
#         # Get all audio URLs
#         audio_urls = await get_surah_audio_urls(surah_id, reciter)
        
#         if not audio_urls:
#             print("❌ No audio found")
#             return
        
#         # Determine range
#         if end_ayah is None:
#             end_ayah = len(audio_urls)
        
#         end_ayah = min(end_ayah, len(audio_urls))
        
#         print(f"📥 Playing ayahs {start_ayah} to {end_ayah}...")
        
#         # Play each ayah
#         for i in range(start_ayah - 1, end_ayah):
#             print(f"\n▶️  Ayah {i + 1}/{end_ayah}")
            
#             filename = f"surah_{surah_id}_ayah_{i + 1}.mp3"
#             await download_audio(audio_urls[i], filename)
            
#             play_audio_file(filename)
            
#             # Cleanup
#             if os.path.exists(filename):
#                 os.remove(filename)
        
#         print("\n✅ Surah playback completed!")
        
#     except Exception as e:
#         print(f"❌ Error: {str(e)}")


# async def play_ayatul_kursi(reciter: str = "alafasy"):
#     """
#     Play Ayatul Kursi (Surah 2, Ayah 255)
    
#     Example:
#         await play_ayatul_kursi()
#         await play_ayatul_kursi("abdulbasit")
#     """
#     print("🎧 Playing Ayatul Kursi...")
#     await play_ayah(2, 255, reciter)


# async def play_surah_yaseen(reciter: str = "alafasy"):
#     """
#     Play complete Surah Yaseen (Surah 36)
    
#     Example:
#         await play_surah_yaseen()
#     """
#     print("🎧 Playing Surah Yaseen...")
#     await play_surah(36, reciter)


# async def play_last_3_surahs(reciter: str = "alafasy"):
#     """
#     Play last 3 Surahs (Al-Ikhlas, Al-Falaq, An-Nas)
    
#     Example:
#         await play_last_3_surahs()
#     """
#     print("🎧 Playing last 3 Surahs...")
#     for surah_id in [112, 113, 114]:
#         await play_surah(surah_id, reciter)
#         print("\n" + "="*50 + "\n")


# # ==================== SYNCHRONOUS WRAPPERS ====================
# # Agar async nahi use karna to ye functions use karein

# def play_ayah_sync(surah_id: int, ayah_number: int, reciter: str = "alafasy"):
#     """Synchronous version of play_ayah"""
#     asyncio.run(play_ayah(surah_id, ayah_number, reciter))


# def play_surah_sync(surah_id: int, reciter: str = "alafasy", start_ayah: int = 1, end_ayah: Optional[int] = None):
#     """Synchronous version of play_surah"""
#     asyncio.run(play_surah(surah_id, reciter, start_ayah, end_ayah))


# def play_ayatul_kursi_sync(reciter: str = "alafasy"):
#     """Synchronous version of play_ayatul_kursi"""
#     asyncio.run(play_ayatul_kursi(reciter))


# def play_surah_yaseen_sync(reciter: str = "alafasy"):
#     """Synchronous version of play_surah_yaseen"""
#     asyncio.run(play_surah_yaseen(reciter))


# # ==================== EXAMPLE USAGE ====================

# if __name__ == "__main__":
#     print("=" * 50)
#     print("🕌 QURAN AUDIO PLAYER")
#     print("=" * 50)
    
#     # Example 1: Play single ayah (Bismillah)
#     print("\n1️⃣ Playing Bismillah...")
#     play_ayah_sync(2,  "alafasy")
    
#     # Example 2: Play Ayatul Kursi
#     print("\n2️⃣ Playing Ayatul Kursi...")
#     play_ayatul_kursi_sync("abdulbasit")
    
#     # Example 3: Play complete Surah Al-Fatiha
#     print("\n3️⃣ Playing Surah Al-Fatiha...")
#     play_surah_sync(1, "alafasy")
    
#     # Example 4: Play first 5 ayahs of Surah Al-Baqarah
#     print("\n4️⃣ Playing first 5 ayahs of Al-Baqarah...")
#     play_surah_sync(2, "sudais", start_ayah=1, end_ayah=5)








# import httpx
# import asyncio
# from typing import Optional, Dict, Any
# import json

# QURAN_API_BASE = "https://api.alquran.cloud/v1"

# # Available reciters
# RECITERS = {
#     "alafasy": "ar.alafasy",
#     "abdulbasit": "ar.abdulbasitmurattal",
#     "sudais": "ar.abdurrahmaansudais",
#     "husary": "ar.husary",
#     "minshawi": "ar.minshawi",
# }


# async def get_ayah_audio_url(surah_id: int, ayah_number: int, reciter: str = "alafasy") -> Dict[str, Any]:
#     """
#     Get audio URL for specific ayah
    
#     Args:
#         surah_id: Surah number (1-114)
#         ayah_number: Ayah number
#         reciter: Reciter name (alafasy, abdulbasit, sudais, husary, minshawi)
    
#     Returns:
#         Dict with audio_url, text, surah info
#     """
#     reciter_id = RECITERS.get(reciter.lower(), "ar.alafasy")
    
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{QURAN_API_BASE}/ayah/{surah_id}:{ayah_number}/{reciter_id}",
#                 timeout=10.0
#             )
            
#             if response.status_code == 200:
#                 data = response.json()["data"]
                
#                 return {
#                     "success": True,
#                     "audio_url": data.get("audio", ""),
#                     "text": data.get("text", ""),
#                     "ayah_number": data["numberInSurah"],
#                     "surah": {
#                         "number": data["surah"]["number"],
#                         "name": data["surah"]["name"],
#                         "englishName": data["surah"]["englishName"]
#                     },
#                     "reciter": reciter
#                 }
#             else:
#                 return {
#                     "success": False,
#                     "error": "Failed to fetch ayah audio"
#                 }
                
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }


# async def get_surah_audio_urls(surah_id: int, reciter: str = "alafasy") -> Dict[str, Any]:
#     """
#     Get all audio URLs for a complete surah
    
#     Args:
#         surah_id: Surah number (1-114)
#         reciter: Reciter name
    
#     Returns:
#         Dict with list of audio URLs for all ayahs
#     """
#     reciter_id = RECITERS.get(reciter.lower(), "ar.alafasy")
    
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{QURAN_API_BASE}/surah/{surah_id}/{reciter_id}",
#                 timeout=15.0
#             )
            
#             if response.status_code == 200:
#                 data = response.json()["data"]
                
#                 ayahs = []
#                 for ayah in data["ayahs"]:
#                     ayahs.append({
#                         "number": ayah["numberInSurah"],
#                         "text": ayah["text"],
#                         "audio": ayah.get("audio", "")
#                     })
                
#                 return {
#                     "success": True,
#                     "surah": {
#                         "number": data["number"],
#                         "name": data["name"],
#                         "englishName": data["englishName"],
#                         "numberOfAyahs": data["numberOfAyahs"]
#                     },
#                     "reciter": reciter,
#                     "ayahs": ayahs
#                 }
#             else:
#                 return {
#                     "success": False,
#                     "error": "Failed to fetch surah audio"
#                 }
                
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }


# # ==================== MAIN TOOL FUNCTIONS ====================

# async def play_quran_audio(
#     surah: Optional[int] = None,
#     ayah: Optional[int] = None,
#     reciter: str = "alafasy"
# ) -> Dict[str, Any]:
#     """
#     Main tool function to get Quran audio
    
#     Usage:
#         - play_quran_audio(surah=1, ayah=1) → Get Surah 1, Ayah 1
#         - play_quran_audio(surah=2, ayah=255) → Get Ayatul Kursi
#         - play_quran_audio(surah=36) → Get complete Surah Yaseen
    
#     Returns:
#         Dict with audio URLs and metadata
#     """
    
#     # Validate inputs
#     if not surah or surah < 1 or surah > 114:
#         return {
#             "success": False,
#             "error": "Invalid Surah number. Must be between 1-114"
#         }
    
#     # If ayah specified, get single ayah
#     if ayah:
#         result = await get_ayah_audio_url(surah, ayah, reciter)
#         result["type"] = "single_ayah"
#         return result
    
#     # Otherwise get complete surah
#     result = await get_surah_audio_urls(surah, reciter)
#     result["type"] = "complete_surah"
#     return result


# # ==================== SHORTCUT FUNCTIONS ====================

# async def play_ayatul_kursi(reciter: str = "alafasy") -> Dict[str, Any]:
#     """Play Ayatul Kursi (Surah 2, Ayah 255)"""
#     return await play_quran_audio(surah=2, ayah=255, reciter=reciter)


# async def play_surah_fatiha(reciter: str = "alafasy") -> Dict[str, Any]:
#     """Play Surah Al-Fatiha"""
#     return await play_quran_audio(surah=1, reciter=reciter)


# async def play_surah_yaseen(reciter: str = "alafasy") -> Dict[str, Any]:
#     """Play Surah Yaseen"""
#     return await play_quran_audio(surah=36, reciter=reciter)


# async def play_last_3_surahs(reciter: str = "alafasy") -> Dict[str, Any]:
#     """Play last 3 Surahs (Al-Ikhlas, Al-Falaq, An-Nas)"""
#     results = []
#     for surah_id in [112, 113, 114]:
#         result = await play_quran_audio(surah=surah_id, reciter=reciter)
#         results.append(result)
    
#     return {
#         "success": True,
#         "type": "multiple_surahs",
#         "surahs": results
#     }


# # ==================== HELPER: PARSE USER INPUT ====================

# def parse_quran_audio_request(user_input: str) -> Dict[str, Any]:
#     """
#     Parse natural language requests for Quran audio
    
#     Examples:
#         "play surah fatiha" → {surah: 1}
#         "play ayatul kursi" → {surah: 2, ayah: 255}
#         "play surah 36" → {surah: 36}
#         "play surah 2 ayah 255" → {surah: 2, ayah: 255}
#     """
#     user_input = user_input.lower()
    
#     # Ayatul Kursi
#     if "ayatul kursi" in user_input or "ayat ul kursi" in user_input:
#         return {"surah": 2, "ayah": 255}
    
#     # Surah names mapping
#     surah_names = {
#         "fatiha": 1, "al-fatiha": 1,
#         "baqarah": 2, "al-baqarah": 2,
#         "imran": 3, "al-imran": 3,
#         "kahf": 18, "al-kahf": 18,
#         "yaseen": 36, "yasin": 36, "ya-sin": 36,
#         "mulk": 67, "al-mulk": 67,
#         "ikhlas": 112, "al-ikhlas": 112,
#         "falaq": 113, "al-falaq": 113,
#         "nas": 114, "an-nas": 114
#     }
    
#     # Check for surah names
#     for name, number in surah_names.items():
#         if name in user_input:
#             # Check if ayah number is mentioned
#             import re
#             ayah_match = re.search(r'ayah?\s*(\d+)', user_input)
#             if ayah_match:
#                 return {"surah": number, "ayah": int(ayah_match.group(1))}
#             return {"surah": number}
    
#     # Check for "surah X ayah Y" pattern
#     import re
#     match = re.search(r'surah\s*(\d+)\s*(?:ayah?\s*(\d+))?', user_input)
#     if match:
#         surah = int(match.group(1))
#         ayah = int(match.group(2)) if match.group(2) else None
#         result = {"surah": surah}
#         if ayah:
#             result["ayah"] = ayah
#         return result
    
#     return None


# # ==================== EXAMPLE USAGE ====================

# if __name__ == "__main__":
#     # Test examples
#     async def test():
#         print("Testing Quran Audio Tool...")
        
#         # Test 1: Single ayah
#         print("\n1. Getting Bismillah audio...")
#         result = await play_quran_audio(surah=2, ayah=1)
#         print(f"Success: {result['success']}")
#         if result['success']:
#             print(f"Audio URL: {result['audio_url'][:50]}...")
        
#         # Test 2: Parse natural language
#         print("\n2. Parsing 'play ayatul kursi'...")
#         parsed = parse_quran_audio_request("play ayatul kursi with abdul basit")
#         print(f"Parsed: {parsed}")
        
#         result = await play_quran_audio(**parsed, reciter="abdulbasit")
#         print(f"Success: {result['success']}")
        
#         # Test 3: Complete surah
#         print("\n3. Getting Surah Al-Fatiha...")
#         result = await play_surah_fatiha()
#         print(f"Success: {result['success']}")
#         if result['success']:
#             print(f"Total Ayahs: {len(result['ayahs'])}")
    
#     asyncio.run(test())



"""
Quran Audio Playback Module
Handles fetching Quran audio from AlQuran Cloud API
"""
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

# Setup logger
logger = logging.getLogger(__name__)

# API Configuration
QURAN_API_BASE = "https://api.alquran.cloud/v1"
API_TIMEOUT = 15.0  # seconds
MAX_RETRIES = 3


# ==================== ENUMS & DATA CLASSES ====================

class ReciterID(str, Enum):
    """Available Quran reciters with their API IDs"""
    ALAFASY = "ar.alafasy"
    ABDUL_BASIT = "ar.abdulbasitmurattal"
    SUDAIS = "ar.abdurrahmaansudais"
    HUSARY = "ar.husary"
    MINSHAWI = "ar.minshawi"
    SHAATREE = "ar.shaatree"
    HANI_RIFAI = "ar.hanirifai"
    MUHAMMAD_AYYOUB = "ar.muhammadayyoub"
    SAOOD_SHURAYM = "ar.saoodshuraym"


# Mapping for user-friendly names
RECITER_NAMES = {
    "alafasy": ReciterID.ALAFASY,
    "abdulbasit": ReciterID.ABDUL_BASIT,
    "sudais": ReciterID.SUDAIS,
    "husary": ReciterID.HUSARY,
    "minshawi": ReciterID.MINSHAWI,
    "shaatree": ReciterID.SHAATREE,
    "hanirifai": ReciterID.HANI_RIFAI,
    "ayyoub": ReciterID.MUHAMMAD_AYYOUB,
    "shuraym": ReciterID.SAOOD_SHURAYM,
}


@dataclass
class SurahInfo:
    """Surah metadata"""
    number: int
    name: str  # Arabic
    english_name: str
    total_ayahs: Optional[int] = None


@dataclass
class AyahAudio:
    """Single Ayah audio data"""
    ayah_number: int
    text: str
    audio_url: str
    surah: SurahInfo
    reciter: str


@dataclass
class SurahAudio:
    """Complete Surah audio data"""
    surah: SurahInfo
    reciter: str
    ayahs: List[Dict[str, Any]]


# ==================== EXCEPTIONS ====================

class QuranAPIError(Exception):
    """Base exception for Quran API errors"""
    pass


class InvalidSurahError(QuranAPIError):
    """Invalid surah number"""
    pass


class InvalidAyahError(QuranAPIError):
    """Invalid ayah number"""
    pass


class ReciterNotFoundError(QuranAPIError):
    """Reciter not found"""
    pass


# ==================== VALIDATORS ====================

def validate_surah(surah_id: int) -> None:
    """Validate surah number (1-114)"""
    if not isinstance(surah_id, int) or surah_id < 1 or surah_id > 114:
        raise InvalidSurahError(
            f"Invalid Surah number: {surah_id}. Must be between 1-114"
        )


def validate_ayah(ayah_number: int) -> None:
    """Validate ayah number (must be positive)"""
    if not isinstance(ayah_number, int) or ayah_number < 1:
        raise InvalidAyahError(
            f"Invalid Ayah number: {ayah_number}. Must be positive"
        )


def get_reciter_id(reciter_name: str) -> str:
    """Get reciter API ID from user-friendly name"""
    reciter_lower = reciter_name.lower().strip()
    
    # Direct enum member
    if reciter_lower in ReciterID.__members__.values():
        return reciter_lower
    
    # From mapping
    if reciter_lower in RECITER_NAMES:
        return RECITER_NAMES[reciter_lower].value
    
    # Default fallback
    logger.warning(f"Unknown reciter '{reciter_name}', using Alafasy as default")
    return ReciterID.ALAFASY.value


# ==================== API FUNCTIONS ====================

async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    max_retries: int = MAX_RETRIES
) -> httpx.Response:
    """Fetch URL with retry logic"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = await client.get(url, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                raise QuranAPIError("Resource not found")
            else:
                raise QuranAPIError(
                    f"API returned status {response.status_code}"
                )
        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        except httpx.RequestError as e:
            last_error = e
            logger.warning(f"Request error on attempt {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(1 * (attempt + 1))
    
    raise QuranAPIError(f"Failed after {max_retries} retries: {last_error}")


async def get_ayah_audio(
    surah_id: int,
    ayah_number: int,
    reciter: str = "alafasy"
) -> AyahAudio:
    """
    Fetch single ayah audio
    
    Args:
        surah_id: Surah number (1-114)
        ayah_number: Ayah number within surah
        reciter: Reciter name (default: alafasy)
    
    Returns:
        AyahAudio object with audio URL and metadata
    
    Raises:
        InvalidSurahError: If surah number invalid
        InvalidAyahError: If ayah number invalid
        QuranAPIError: If API request fails
    """
    # Validate inputs
    validate_surah(surah_id)
    validate_ayah(ayah_number)
    
    reciter_id = get_reciter_id(reciter)
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"{QURAN_API_BASE}/ayah/{surah_id}:{ayah_number}/{reciter_id}"
            
            logger.info(f"Fetching ayah audio: Surah {surah_id}, Ayah {ayah_number}")
            response = await fetch_with_retry(client, url)
            
            data = response.json()["data"]
            
            # Extract data
            surah_info = SurahInfo(
                number=data["surah"]["number"],
                name=data["surah"]["name"],
                english_name=data["surah"]["englishName"]
            )
            
            ayah_audio = AyahAudio(
                ayah_number=data["numberInSurah"],
                text=data.get("text", ""),
                audio_url=data.get("audio", ""),
                surah=surah_info,
                reciter=reciter
            )
            
            logger.info(f"✅ Successfully fetched audio for {surah_info.english_name}:{ayah_number}")
            return ayah_audio
            
    except (InvalidSurahError, InvalidAyahError):
        raise
    except Exception as e:
        logger.error(f"Failed to fetch ayah audio: {e}")
        raise QuranAPIError(f"Error fetching ayah: {str(e)}")


async def get_surah_audio(
    surah_id: int,
    reciter: str = "alafasy"
) -> SurahAudio:
    """
    Fetch complete surah audio
    
    Args:
        surah_id: Surah number (1-114)
        reciter: Reciter name
    
    Returns:
        SurahAudio object with all ayahs
    
    Raises:
        InvalidSurahError: If surah number invalid
        QuranAPIError: If API request fails
    """
    validate_surah(surah_id)
    reciter_id = get_reciter_id(reciter)
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"{QURAN_API_BASE}/surah/{surah_id}/{reciter_id}"
            
            logger.info(f"Fetching complete surah: {surah_id}")
            response = await fetch_with_retry(client, url)
            
            data = response.json()["data"]
            
            # Extract surah info
            surah_info = SurahInfo(
                number=data["number"],
                name=data["name"],
                english_name=data["englishName"],
                total_ayahs=data["numberOfAyahs"]
            )
            
            # Extract all ayahs
            ayahs = [
                {
                    "number": ayah["numberInSurah"],
                    "text": ayah["text"],
                    "audio": ayah.get("audio", "")
                }
                for ayah in data["ayahs"]
            ]
            
            surah_audio = SurahAudio(
                surah=surah_info,
                reciter=reciter,
                ayahs=ayahs
            )
            
            logger.info(f"✅ Fetched {len(ayahs)} ayahs for {surah_info.english_name}")
            return surah_audio
            
    except InvalidSurahError:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch surah audio: {e}")
        raise QuranAPIError(f"Error fetching surah: {str(e)}")


# ==================== MAIN API FUNCTION ====================

async def play_quran_audio(
    surah: int,
    ayah: Optional[int] = None,
    reciter: str = "alafasy"
) -> Dict[str, Any]:
    """
    Main function to get Quran audio
    
    Args:
        surah: Surah number (1-114)
        ayah: Optional ayah number
        reciter: Reciter name
    
    Returns:
        Dict with success status and audio data
    
    Examples:
        >>> await play_quran_audio(surah=1, ayah=1)  # Single ayah
        >>> await play_quran_audio(surah=36)  # Complete surah
    """
    try:
        if ayah:
            # Single ayah request
            ayah_audio = await get_ayah_audio(surah, ayah, reciter)
            
            return {
                "success": True,
                "type": "single_ayah",
                "audio_url": ayah_audio.audio_url,
                "text": ayah_audio.text,
                "ayah_number": ayah_audio.ayah_number,
                "surah": {
                    "number": ayah_audio.surah.number,
                    "name": ayah_audio.surah.name,
                    "englishName": ayah_audio.surah.english_name
                },
                "reciter": reciter
            }
        else:
            # Complete surah request
            surah_audio = await get_surah_audio(surah, reciter)
            
            return {
                "success": True,
                "type": "complete_surah",
                "surah": {
                    "number": surah_audio.surah.number,
                    "name": surah_audio.surah.name,
                    "englishName": surah_audio.surah.english_name,
                    "numberOfAyahs": surah_audio.surah.total_ayahs
                },
                "reciter": reciter,
                "ayahs": surah_audio.ayahs
            }
    
    except (InvalidSurahError, InvalidAyahError, ReciterNotFoundError) as e:
        logger.error(f"Validation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "validation_error"
        }
    except QuranAPIError as e:
        logger.error(f"API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "api_error"
        }
    except Exception as e:
        logger.exception("Unexpected error in play_quran_audio")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unknown_error"
        }


# ==================== NATURAL LANGUAGE PARSER ====================

def parse_quran_audio_request(user_input: str) -> Optional[Dict[str, int]]:
    """
    Parse natural language requests for Quran audio
    
    Args:
        user_input: User's natural language request
    
    Returns:
        Dict with surah and optionally ayah numbers, or None if parsing fails
    
    Examples:
        >>> parse_quran_audio_request("play surah fatiha")
        {'surah': 1}
        >>> parse_quran_audio_request("play ayatul kursi")
        {'surah': 2, 'ayah': 255}
        >>> parse_quran_audio_request("listen to surah 36 ayah 1")
        {'surah': 36, 'ayah': 1}
    """
    import re
    
    if not user_input:
        return None
    
    user_input = user_input.lower().strip()
    
    # Special cases
    if "ayatul kursi" in user_input or "ayat ul kursi" in user_input:
        return {"surah": 2, "ayah": 255}
    
    # Surah name mapping
    SURAH_NAMES = {
        "fatiha": 1, "al-fatiha": 1, "fatihah": 1,
        "baqarah": 2, "al-baqarah": 2, "bakra": 2,
        "imran": 3, "al-imran": 3, "ali imran": 3,
        "nisa": 4, "an-nisa": 4,
        "maidah": 5, "al-maidah": 5,
        "anam": 6, "al-anam": 6,
        "araf": 7, "al-araf": 7,
        "anfal": 8, "al-anfal": 8,
        "tawbah": 9, "at-tawbah": 9,
        "yunus": 10,
        "hud": 11,
        "yusuf": 12,
        "rad": 13, "ar-rad": 13,
        "ibrahim": 14,
        "hijr": 15, "al-hijr": 15,
        "nahl": 16, "an-nahl": 16,
        "isra": 17, "al-isra": 17,
        "kahf": 18, "al-kahf": 18,
        "maryam": 19,
        "taha": 20, "ta-ha": 20,
        "anbiya": 21, "al-anbiya": 21,
        "hajj": 22, "al-hajj": 22,
        "muminun": 23, "al-muminun": 23,
        "nur": 24, "an-nur": 24,
        "furqan": 25, "al-furqan": 25,
        "shuara": 26, "ash-shuara": 26,
        "naml": 27, "an-naml": 27,
        "qasas": 28, "al-qasas": 28,
        "ankabut": 29, "al-ankabut": 29,
        "rum": 30, "ar-rum": 30,
        "luqman": 31,
        "sajdah": 32, "as-sajdah": 32,
        "ahzab": 33, "al-ahzab": 33,
        "saba": 34,
        "fatir": 35,
        "yasin": 36, "yaseen": 36, "ya-sin": 36,
        "saffat": 37, "as-saffat": 37,
        "sad": 38,
        "zumar": 39, "az-zumar": 39,
        "ghafir": 40,
        "fussilat": 41,
        "shura": 42, "ash-shura": 42,
        "zukhruf": 43, "az-zukhruf": 43,
        "dukhan": 44, "ad-dukhan": 44,
        "jathiyah": 45, "al-jathiyah": 45,
        "ahqaf": 46, "al-ahqaf": 46,
        "muhammad": 47,
        "fath": 48, "al-fath": 48,
        "hujurat": 49, "al-hujurat": 49,
        "qaf": 50,
        "dhariyat": 51, "adh-dhariyat": 51,
        "tur": 52, "at-tur": 52,
        "najm": 53, "an-najm": 53,
        "qamar": 54, "al-qamar": 54,
        "rahman": 55, "ar-rahman": 55,
        "waqiah": 56, "al-waqiah": 56,
        "hadid": 57, "al-hadid": 57,
        "mujadila": 58, "al-mujadila": 58,
        "hashr": 59, "al-hashr": 59,
        "mumtahanah": 60, "al-mumtahanah": 60,
        "saff": 61, "as-saff": 61,
        "jumuah": 62, "al-jumuah": 62,
        "munafiqun": 63, "al-munafiqun": 63,
        "taghabun": 64, "at-taghabun": 64,
        "talaq": 65, "at-talaq": 65,
        "tahrim": 66, "at-tahrim": 66,
        "mulk": 67, "al-mulk": 67,
        "qalam": 68, "al-qalam": 68,
        "haqqah": 69, "al-haqqah": 69,
        "maarij": 70, "al-maarij": 70,
        "nuh": 71,
        "jinn": 72, "al-jinn": 72,
        "muzzammil": 73, "al-muzzammil": 73,
        "muddaththir": 74, "al-muddaththir": 74,
        "qiyamah": 75, "al-qiyamah": 75,
        "insan": 76, "al-insan": 76,
        "mursalat": 77, "al-mursalat": 77,
        "naba": 78, "an-naba": 78,
        "naziat": 79, "an-naziat": 79,
        "abasa": 80,
        "takwir": 81, "at-takwir": 81,
        "infitar": 82, "al-infitar": 82,
        "mutaffifin": 83, "al-mutaffifin": 83,
        "inshiqaq": 84, "al-inshiqaq": 84,
        "buruj": 85, "al-buruj": 85,
        "tariq": 86, "at-tariq": 86,
        "ala": 87, "al-ala": 87,
        "ghashiyah": 88, "al-ghashiyah": 88,
        "fajr": 89, "al-fajr": 89,
        "balad": 90, "al-balad": 90,
        "shams": 91, "ash-shams": 91,
        "layl": 92, "al-layl": 92,
        "duha": 93, "ad-duha": 93,
        "sharh": 94, "ash-sharh": 94, "inshirah": 94,
        "tin": 95, "at-tin": 95,
        "alaq": 96, "al-alaq": 96,
        "qadr": 97, "al-qadr": 97,
        "bayyinah": 98, "al-bayyinah": 98,
        "zalzalah": 99, "az-zalzalah": 99,
        "adiyat": 100, "al-adiyat": 100,
        "qariah": 101, "al-qariah": 101,
        "takathur": 102, "at-takathur": 102,
        "asr": 103, "al-asr": 103,
        "humazah": 104, "al-humazah": 104,
        "fil": 105, "al-fil": 105,
        "quraysh": 106,
        "maun": 107, "al-maun": 107,
        "kawthar": 108, "al-kawthar": 108,
        "kafirun": 109, "al-kafirun": 109,
        "nasr": 110, "an-nasr": 110,
        "masad": 111, "al-masad": 111, "lahab": 111,
        "ikhlas": 112, "al-ikhlas": 112,
        "falaq": 113, "al-falaq": 113,
        "nas": 114, "an-nas": 114, "naas": 114
    }
    
    # Check for surah names
    for name, number in SURAH_NAMES.items():
        if name in user_input:
            # Check if ayah mentioned
            ayah_match = re.search(r'ayah?\s*(\d+)', user_input)
            if ayah_match:
                return {"surah": number, "ayah": int(ayah_match.group(1))}
            return {"surah": number}
    
    # Pattern: "surah X ayah Y"
    match = re.search(r'surah\s*(\d+)\s*(?:ayah?\s*(\d+))?', user_input)
    if match:
        result = {"surah": int(match.group(1))}
        if match.group(2):
            result["ayah"] = int(match.group(2))
        return result
    
    # Pattern: "X:Y" (colon format)
    match = re.search(r'(\d+):(\d+)', user_input)
    if match:
        return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
    return None


# ==================== HELPER FUNCTIONS ====================

def get_available_reciters() -> List[Dict[str, str]]:
    """Get list of available reciters"""
    return [
        {"id": "alafasy", "name": "Mishary Rashid Alafasy"},
        {"id": "abdulbasit", "name": "Abdul Basit Abdul Samad"},
        {"id": "sudais", "name": "Abdur-Rahman As-Sudais"},
        {"id": "husary", "name": "Mahmoud Khalil Al-Husary"},
        {"id": "minshawi", "name": "Mohamed Siddiq Al-Minshawi"},
        {"id": "shaatree", "name": "Abu Bakr Ash-Shaatree"},
        {"id": "hanirifai", "name": "Hani Ar-Rifai"},
        {"id": "ayyoub", "name": "Muhammad Ayyub"},
        {"id": "shuraym", "name": "Saood Ash-Shuraym"}
    ]


# ==================== SHORTCUTS ====================

async def play_ayatul_kursi(reciter: str = "alafasy") -> Dict[str, Any]:
    """Shortcut: Play Ayatul Kursi"""
    return await play_quran_audio(surah=2, ayah=255, reciter=reciter)


async def play_surah_fatiha(reciter: str = "alafasy") -> Dict[str, Any]:
    """Shortcut: Play Surah Al-Fatiha"""
    return await play_quran_audio(surah=1, reciter=reciter)


async def play_surah_yaseen(reciter: str = "alafasy") -> Dict[str, Any]:
    """Shortcut: Play Surah Yaseen"""
    return await play_quran_audio(surah=36, reciter=reciter)