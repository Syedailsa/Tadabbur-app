import httpx
import asyncio
from typing import Optional
import os

# Audio playback libraries
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame not installed. Install with: pip install pygame")

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False
    print("⚠️ playsound not installed. Install with: pip install playsound")

QURAN_API_BASE = "https://api.alquran.cloud/v1"

# Popular reciters
RECITERS = {
    "alafasy": "ar.alafasy",  # Mishary Rashid Alafasy
    "abdulbasit": "ar.abdulbasitmurattal",  # Abdul Basit
    "sudais": "ar.abdurrahmaansudais",  # Abdur-Rahman As-Sudais
    "husary": "ar.husary",  # Mahmoud Khalil Al-Husary
    "minshawi": "ar.minshawi",  # Mohamed Siddiq Al-Minshawi
}


async def download_audio(url: str, filename: str) -> str:
    """Download audio file from URL"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
            else:
                raise Exception(f"Failed to download audio: {response.status_code}")
    except Exception as e:
        raise Exception(f"Download error: {str(e)}")


def play_audio_file(filepath: str):
    """Play audio file using available library"""
    if PYGAME_AVAILABLE:
        # Using pygame
        pygame.mixer.init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        
        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    elif PLAYSOUND_AVAILABLE:
        # Using playsound
        playsound(filepath)
        
    else:
        print("❌ No audio library available!")
        print("Install one of these:")
        print("  pip install pygame")
        print("  pip install playsound")


async def get_ayah_audio_url(surah_id: int, ayah_number: int, reciter: str = "alafasy") -> str:
    """Get audio URL for specific ayah"""
    reciter_id = RECITERS.get(reciter, "ar.alafasy")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QURAN_API_BASE}/ayah/{surah_id}:{ayah_number}/{reciter_id}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                audio_url = data.get("audio", "")
                
                if not audio_url:
                    raise Exception("Audio URL not found")
                
                return audio_url
            else:
                raise Exception(f"API error: {response.status_code}")
                
    except Exception as e:
        raise Exception(f"Failed to get audio: {str(e)}")


async def get_surah_audio_urls(surah_id: int, reciter: str = "alafasy") -> list:
    """Get all audio URLs for a surah"""
    reciter_id = RECITERS.get(reciter, "ar.alafasy")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QURAN_API_BASE}/surah/{surah_id}/{reciter_id}",
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                audio_urls = [ayah.get("audio", "") for ayah in data["ayahs"]]
                return [url for url in audio_urls if url]
            else:
                raise Exception(f"API error: {response.status_code}")
                
    except Exception as e:
        raise Exception(f"Failed to get surah audio: {str(e)}")


# ==================== MAIN FUNCTIONS ====================

async def play_ayah(surah_id: int, ayah_number: int, reciter: str = "alafasy"):
    """
    Play specific ayah audio
    
    Args:
        surah_id: Surah number (1-114)
        ayah_number: Ayah number within surah
        reciter: Reciter name (alafasy, abdulbasit, sudais, husary, minshawi)
    
    Example:
        await play_ayah(1, 1)  # Play Surah Al-Fatiha, Ayah 1
        await play_ayah(2, 255, "abdulbasit")  # Play Ayatul Kursi with Abdul Basit
    """
    print(f"🎧 Playing Surah {surah_id}, Ayah {ayah_number} ({reciter})...")
    
    try:
        # Get audio URL
        audio_url = await get_ayah_audio_url(surah_id, ayah_number, reciter)
        print(f"📥 Downloading audio...")
        
        # Download audio
        filename = f"ayah_{surah_id}_{ayah_number}.mp3"
        await download_audio(audio_url, filename)
        
        print(f"▶️  Playing...")
        # Play audio
        play_audio_file(filename)
        
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
            
        print("✅ Playback completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def play_surah(surah_id: int, reciter: str = "alafasy", start_ayah: int = 1, end_ayah: Optional[int] = None):
    """
    Play complete surah or specific range
    
    Args:
        surah_id: Surah number (1-114)
        reciter: Reciter name
        start_ayah: Starting ayah (default: 1)
        end_ayah: Ending ayah (default: None = till end)
    
    Example:
        await play_surah(1)  # Play complete Surah Al-Fatiha
        await play_surah(2, start_ayah=1, end_ayah=5)  # Play first 5 ayahs of Al-Baqarah
    """
    print(f"🎧 Playing Surah {surah_id} ({reciter})...")
    
    try:
        # Get all audio URLs
        audio_urls = await get_surah_audio_urls(surah_id, reciter)
        
        if not audio_urls:
            print("❌ No audio found")
            return
        
        # Determine range
        if end_ayah is None:
            end_ayah = len(audio_urls)
        
        end_ayah = min(end_ayah, len(audio_urls))
        
        print(f"📥 Playing ayahs {start_ayah} to {end_ayah}...")
        
        # Play each ayah
        for i in range(start_ayah - 1, end_ayah):
            print(f"\n▶️  Ayah {i + 1}/{end_ayah}")
            
            filename = f"surah_{surah_id}_ayah_{i + 1}.mp3"
            await download_audio(audio_urls[i], filename)
            
            play_audio_file(filename)
            
            # Cleanup
            if os.path.exists(filename):
                os.remove(filename)
        
        print("\n✅ Surah playback completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def play_ayatul_kursi(reciter: str = "alafasy"):
    """
    Play Ayatul Kursi (Surah 2, Ayah 255)
    
    Example:
        await play_ayatul_kursi()
        await play_ayatul_kursi("abdulbasit")
    """
    print("🎧 Playing Ayatul Kursi...")
    await play_ayah(2, 255, reciter)


async def play_surah_yaseen(reciter: str = "alafasy"):
    """
    Play complete Surah Yaseen (Surah 36)
    
    Example:
        await play_surah_yaseen()
    """
    print("🎧 Playing Surah Yaseen...")
    await play_surah(36, reciter)


async def play_last_3_surahs(reciter: str = "alafasy"):
    """
    Play last 3 Surahs (Al-Ikhlas, Al-Falaq, An-Nas)
    
    Example:
        await play_last_3_surahs()
    """
    print("🎧 Playing last 3 Surahs...")
    for surah_id in [112, 113, 114]:
        await play_surah(surah_id, reciter)
        print("\n" + "="*50 + "\n")


# ==================== SYNCHRONOUS WRAPPERS ====================
# Agar async nahi use karna to ye functions use karein

def play_ayah_sync(surah_id: int, ayah_number: int, reciter: str = "alafasy"):
    """Synchronous version of play_ayah"""
    asyncio.run(play_ayah(surah_id, ayah_number, reciter))


def play_surah_sync(surah_id: int, reciter: str = "alafasy", start_ayah: int = 1, end_ayah: Optional[int] = None):
    """Synchronous version of play_surah"""
    asyncio.run(play_surah(surah_id, reciter, start_ayah, end_ayah))


def play_ayatul_kursi_sync(reciter: str = "alafasy"):
    """Synchronous version of play_ayatul_kursi"""
    asyncio.run(play_ayatul_kursi(reciter))


def play_surah_yaseen_sync(reciter: str = "alafasy"):
    """Synchronous version of play_surah_yaseen"""
    asyncio.run(play_surah_yaseen(reciter))


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    print("=" * 50)
    print("🕌 QURAN AUDIO PLAYER")
    print("=" * 50)
    
    # Example 1: Play single ayah (Bismillah)
    print("\n1️⃣ Playing Bismillah...")
    play_ayah_sync(1, 1, "alafasy")
    
    # Example 2: Play Ayatul Kursi
    print("\n2️⃣ Playing Ayatul Kursi...")
    play_ayatul_kursi_sync("abdulbasit")
    
    # Example 3: Play complete Surah Al-Fatiha
    print("\n3️⃣ Playing Surah Al-Fatiha...")
    play_surah_sync(1, "alafasy")
    
    # Example 4: Play first 5 ayahs of Surah Al-Baqarah
    print("\n4️⃣ Playing first 5 ayahs of Al-Baqarah...")
    play_surah_sync(2, "sudais", start_ayah=1, end_ayah=5)








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