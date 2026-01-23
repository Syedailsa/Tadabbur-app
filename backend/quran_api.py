from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import httpx
from pydantic import BaseModel
from pathlib import Path

# ==================== MODELS ====================

class SurahBasic(BaseModel):
    """Basic Surah info"""
    number: int
    name: str
    englishName: str
    englishNameTranslation: str
    numberOfAyahs: int
    revelationType: str

class SurahDetail(BaseModel):
    """Detailed Surah with all ayahs"""
    number: int
    name: str
    englishName: str
    englishNameTranslation: str
    numberOfAyahs: int
    revelationType: str
    ayahs: List[dict]

class AyahDetail(BaseModel):
    """Single Ayah"""
    number: int
    text: str
    numberInSurah: int
    surah: dict

class ParahBasic(BaseModel):
    """Parah info"""
    number: int
    name: str
    start: str
    end: str

class Story(BaseModel):
    """Story model"""
    id: str
    title: str
    description: str
    content: str
    category: Optional[str] = None
    created_at: str

class ReciterInfo(BaseModel):
    """Reciter information"""
    identifier: str
    name: str
    englishName: str
    language: str
    format: str

class AudioAyah(BaseModel):
    """Ayah with audio"""
    number: int
    numberInSurah: int
    text: str
    audio: str
    audioSecondary: Optional[List[str]] = []

class SurahWithAudio(BaseModel):
    """Surah with audio for all ayahs"""
    number: int
    name: str
    englishName: str
    englishNameTranslation: str
    numberOfAyahs: int
    revelationType: str
    ayahs: List[AudioAyah]

# ==================== ROUTERS ====================

quran_router = APIRouter(prefix="/surah", tags=["Quran Content"])
parah_router = APIRouter(prefix="/parah", tags=["Parah"])
story_router = APIRouter(prefix="/stories", tags=["Stories"])
audio_router = APIRouter(prefix="/audio", tags=["Quran Audio"])


# ==================== QURAN APIs ====================

#  Using External API alquran.cloud
QURAN_API_BASE = "https://api.alquran.cloud/v1"

@quran_router.get("", response_model=List[SurahBasic])
async def get_all_surahs():
    """
    Get list of all 114 Surahs
    
    Returns basic info: number, name, translation, ayah count
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QURAN_API_BASE}/surah",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                surahs = data.get("data", [])
                
                # Format response
                return [
                    {
                        "number": s["number"],
                        "name": s["name"],
                        "englishName": s["englishName"],
                        "englishNameTranslation": s["englishNameTranslation"],
                        "numberOfAyahs": s["numberOfAyahs"],
                        "revelationType": s["revelationType"]
                    }
                    for s in surahs
                ]
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch surahs")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quran API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@quran_router.get("/{surahId}")
async def get_surah_by_id(surahId: int):
    """
    Get specific Surah with all ayahs
    
    Args:
        surahId: Surah number (1-114)
    
    Returns:
        Surah details with all ayahs in Arabic and translation
    """
    if surahId < 1 or surahId > 114:
        raise HTTPException(status_code=400, detail="Invalid Surah ID. Must be 1-114")
    
    try:
        async with httpx.AsyncClient() as client:
            # Get Arabic text
            arabic_response = await client.get(
                f"{QURAN_API_BASE}/surah/{surahId}",
                timeout=10.0
            )
            
            # Get English translation (using Sahih International)
            english_response = await client.get(
                f"{QURAN_API_BASE}/surah/{surahId}/en.asad",
                timeout=10.0
            )
            
            if arabic_response.status_code == 200 and english_response.status_code == 200:
                arabic_data = arabic_response.json()["data"]
                english_data = english_response.json()["data"]
                
                # Combine Arabic + Translation
                combined_ayahs = []
                for i, ayah in enumerate(arabic_data["ayahs"]):
                    combined_ayahs.append({
                        "number": ayah["number"],
                        "numberInSurah": ayah["numberInSurah"],
                        "text_arabic": ayah["text"],
                        "text_english": english_data["ayahs"][i]["text"]
                    })
                
                return {
                    "number": arabic_data["number"],
                    "name": arabic_data["name"],
                    "englishName": arabic_data["englishName"],
                    "englishNameTranslation": arabic_data["englishNameTranslation"],
                    "numberOfAyahs": arabic_data["numberOfAyahs"],
                    "revelationType": arabic_data["revelationType"],
                    "ayahs": combined_ayahs
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch surah")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quran API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@quran_router.get("/{surahId}/ayah/{ayahNumber}")
async def get_specific_ayah(surahId: int, ayahNumber: int):
    """
    Get specific Ayah from a Surah
    
    Args:
        surahId: Surah number (1-114)
        ayahNumber: Ayah number within surah
    
    Returns:
        Single ayah with Arabic text and translation
    """
    if surahId < 1 or surahId > 114:
        raise HTTPException(status_code=400, detail="Invalid Surah ID")
    
    try:
        async with httpx.AsyncClient() as client:
            # Get specific ayah (Arabic)
            arabic_response = await client.get(
                f"{QURAN_API_BASE}/ayah/{surahId}:{ayahNumber}",
                timeout=10.0
            )
            
            # Get translation
            english_response = await client.get(
                f"{QURAN_API_BASE}/ayah/{surahId}:{ayahNumber}/en.asad",
                timeout=10.0
            )
            
            if arabic_response.status_code == 200 and english_response.status_code == 200:
                arabic_data = arabic_response.json()["data"]
                english_data = english_response.json()["data"]
                
                return {
                    "number": arabic_data["number"],
                    "numberInSurah": arabic_data["numberInSurah"],
                    "text_arabic": arabic_data["text"],
                    "text_english": english_data["text"],
                    "surah": {
                        "number": arabic_data["surah"]["number"],
                        "name": arabic_data["surah"]["name"],
                        "englishName": arabic_data["surah"]["englishName"]
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="Ayah not found")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quran API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ==================== PARAH APIs ====================

# Parah mapping (30 Juz)
PARAH_DATA = [
    {"number": 1, "name": "Alif Lam Meem", "start": "1:1", "end": "2:141"},
    {"number": 2, "name": "Sayaqool", "start": "2:142", "end": "2:252"},
    {"number": 3, "name": "Tilkal Rusul", "start": "2:253", "end": "3:92"},
    {"number": 4, "name": "Lan Tana Lu", "start": "3:93", "end": "4:23"},
    {"number": 5, "name": "Wal Muhsanat", "start": "4:24", "end": "4:147"},
    {"number": 6, "name": "La Yuhibbullah", "start": "4:148", "end": "5:81"},
    {"number": 7, "name": "Wa Iza Samiu", "start": "5:82", "end": "6:110"},
    {"number": 8, "name": "Wa Lau Annana", "start": "6:111", "end": "7:87"},
    {"number": 9, "name": "Qalal Malao", "start": "7:88", "end": "8:40"},
    {"number": 10, "name": "Wa Alamoo", "start": "8:41", "end": "9:92"},
    {"number": 11, "name": "Yatazeroon", "start": "9:93", "end": "11:5"},
    {"number": 12, "name": "Wa Mamin Daabba", "start": "11:6", "end": "12:52"},
    {"number": 13, "name": "Wa Ma Ubrioo", "start": "12:53", "end": "14:52"},
    {"number": 14, "name": "Rubama", "start": "15:1", "end": "16:128"},
    {"number": 15, "name": "Subhanallazi", "start": "17:1", "end": "18:74"},
    {"number": 16, "name": "Qala Alam", "start": "18:75", "end": "20:135"},
    {"number": 17, "name": "Iqtaraba", "start": "21:1", "end": "22:78"},
    {"number": 18, "name": "Qad Aflaha", "start": "23:1", "end": "25:20"},
    {"number": 19, "name": "Wa Qalallazina", "start": "25:21", "end": "27:55"},
    {"number": 20, "name": "Amman Khalaqa", "start": "27:56", "end": "29:45"},
    {"number": 21, "name": "Utlu Ma Oohi", "start": "29:46", "end": "33:30"},
    {"number": 22, "name": "Wa Manyaqnut", "start": "33:31", "end": "36:27"},
    {"number": 23, "name": "Wa Mali", "start": "36:28", "end": "39:31"},
    {"number": 24, "name": "Faman Azlam", "start": "39:32", "end": "41:46"},
    {"number": 25, "name": "Ilayhi Yuraddo", "start": "41:47", "end": "45:37"},
    {"number": 26, "name": "Ha Meem", "start": "46:1", "end": "51:30"},
    {"number": 27, "name": "Qala Fama Khatbukum", "start": "51:31", "end": "57:29"},
    {"number": 28, "name": "Qad Samia", "start": "58:1", "end": "66:12"},
    {"number": 29, "name": "Tabarakal Lazi", "start": "67:1", "end": "77:50"},
    {"number": 30, "name": "Amma Yatasa aloon", "start": "78:1", "end": "114:6"}
]

@parah_router.get("", response_model=List[ParahBasic])
async def get_all_parah():
    """
    Get list of all 30 Parah (Juz)
    
    Returns:
        List of all Parah with name and ayah range
    """
    return PARAH_DATA


# ==================== STORIES APIs ====================

# Hardcoded stories (temporary)
SAMPLE_STORIES = [
    {
        "id": "story_1",
        "title": "Prophet Yusuf (AS) - The Dreamer",
        "description": "The inspiring story of Prophet Yusuf and his journey from slavery to leadership",
        "content": "Prophet Yusuf (AS) was the beloved son of Prophet Yaqub (AS)...",
        "category": "Prophets",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": "story_2",
        "title": "People of the Cave (Ashab al-Kahf)",
        "description": "The miraculous story of the youth who slept for 300 years",
        "content": "A group of young believers fled persecution...",
        "category": "Miracles",
        "created_at": "2024-01-02T00:00:00"
    },
    {
        "id": "story_3",
        "title": "Prophet Musa (AS) and Pharaoh",
        "description": "The confrontation between truth and tyranny",
        "content": "Prophet Musa (AS) was sent to Pharaoh with clear signs...",
        "category": "Prophets",
        "created_at": "2024-01-03T00:00:00"
    }
]

@story_router.get("", response_model=List[Story])
async def get_all_stories():
    """
    Get all Islamic stories
    
    Returns:
        List of stories with title, description, and content
    """
    
    return SAMPLE_STORIES
    

@story_router.get("/{story_id}", response_model=Story)
async def get_story_by_id(story_id: str):
    """
    Get specific story by ID
    
    Args:
        story_id: Story identifier
    
    Returns:
        Story details
    """
    story = next((s for s in SAMPLE_STORIES if s["id"] == story_id), None)
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return story


POPULAR_RECITERS = [
    {"identifier": "ar.alafasy", "name": "Mishary Rashid Alafasy", "language": "Arabic"},
    {"identifier": "ar.abdulbasitmurattal", "name": "Abdul Basit (Murattal)", "language": "Arabic"},
    {"identifier": "ar.abdurrahmaansudais", "name": "Abdur-Rahman As-Sudais", "language": "Arabic"},
    {"identifier": "ar.shaatree", "name": "Abu Bakr Ash-Shaatree", "language": "Arabic"},
    {"identifier": "ar.husary", "name": "Mahmoud Khalil Al-Husary", "language": "Arabic"},
    {"identifier": "ar.minshawi", "name": "Mohamed Siddiq Al-Minshawi", "language": "Arabic"},
]


@audio_router.get("/reciters", response_model=List[dict])
async def get_available_reciters():
    """
    Get list of available Quran reciters
    
    Returns:
        List of reciters with their identifiers
    """
    return POPULAR_RECITERS


@audio_router.get("/surah/{surahId}")
async def get_surah_audio(
    surahId: int,
    reciter: str = "ar.alafasy"
):
    """
    Get Surah with audio for all ayahs
    
    Args:
        surahId: Surah number (1-114)
        reciter: Reciter identifier (default: ar.alafasy - Mishary Alafasy)
    
    Available reciters:
        - ar.alafasy (Mishary Rashid Alafasy)
        - ar.abdulbasitmurattal (Abdul Basit)
        - ar.abdurrahmaansudais (Abdur-Rahman As-Sudais)
        - ar.shaatree (Abu Bakr Ash-Shaatree)
        - ar.husary (Mahmoud Khalil Al-Husary)
        - ar.minshawi (Mohamed Siddiq Al-Minshawi)
    
    Returns:
        Surah with audio URLs for each ayah
    """
    if surahId < 1 or surahId > 114:
        raise HTTPException(status_code=400, detail="Invalid Surah ID. Must be 1-114")
    
    try:
        async with httpx.AsyncClient() as client:
            
            # Get surah with audio
            response = await client.get(
                f"{QURAN_API_BASE}/surah/{surahId}/{reciter}",
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                
                return {
                    "number": data["number"],
                    "name": data["name"],
                    "englishName": data["englishName"],
                    "englishNameTranslation": data["englishNameTranslation"],
                    "numberOfAyahs": data["numberOfAyahs"],
                    "revelationType": data["revelationType"],
                    "reciter": reciter,
                    "ayahs": [
                        {
                            "number": ayah["number"],
                            "numberInSurah": ayah["numberInSurah"],
                            "text": ayah["text"],
                            "audio": ayah.get("audio", ""),
                            "audioSecondary": ayah.get("audioSecondary", [])
                        }
                        for ayah in data["ayahs"]
                    ]
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch audio")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quran API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@audio_router.get("/ayah/{surahId}/{ayahNumber}")
async def get_ayah_audio(
    surahId: int,
    ayahNumber: int,
    reciter: str = "ar.alafasy"
):
    """
    Get specific Ayah with audio
    
    Args:
        surahId: Surah number (1-114)
        ayahNumber: Ayah number within surah
        reciter: Reciter identifier (default: ar.alafasy)
    
    Returns:
        Single ayah with audio URL
    """
    if surahId < 1 or surahId > 114:
        raise HTTPException(status_code=400, detail="Invalid Surah ID")
    
    try:
        async with httpx.AsyncClient() as client:
            # Get specific ayah with audio
            response = await client.get(
                f"{QURAN_API_BASE}/ayah/{surahId}:{ayahNumber}/{reciter}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                
                return {
                    "number": data["number"],
                    "numberInSurah": data["numberInSurah"],
                    "text": data["text"],
                    "audio": data.get("audio", ""),
                    "audioSecondary": data.get("audioSecondary", []),
                    "surah": {
                        "number": data["surah"]["number"],
                        "name": data["surah"]["name"],
                        "englishName": data["surah"]["englishName"]
                    },
                    "reciter": reciter
                }
            else:
                raise HTTPException(status_code=404, detail="Ayah not found")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quran API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@audio_router.get("/full-surah-audio/{surahId}")
async def get_full_surah_single_audio(
    surahId: int,
    reciter: str = "ar.alafasy"
):
    """
    Get complete Surah as single audio file (if available)
    
    Args:
        surahId: Surah number (1-114)
        reciter: Reciter identifier
    
    Returns:
        Surah info with single audio URL for complete recitation
    """
    if surahId < 1 or surahId > 114:
        raise HTTPException(status_code=400, detail="Invalid Surah ID. Must be 1-114")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QURAN_API_BASE}/surah/{surahId}/{reciter}",
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                
                # Get first ayah's audio as reference
                first_audio = data["ayahs"][0].get("audio", "") if data["ayahs"] else ""
                
                return {
                    "number": data["number"],
                    "name": data["name"],
                    "englishName": data["englishName"],
                    "englishNameTranslation": data["englishNameTranslation"],
                    "numberOfAyahs": data["numberOfAyahs"],
                    "reciter": reciter,
                    "audioUrl": first_audio,
                    "note": "This is ayah-by-ayah audio. For full surah audio, play ayahs sequentially."
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch audio")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quran API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@audio_router.get("/juz/{juzNumber}")
async def get_juz_audio(
    juzNumber: int,
    reciter: str = "ar.alafasy"
):
    """
    Get Juz/Para with audio
    
    Args:
        juzNumber: Juz number (1-30)
        reciter: Reciter identifier
    
    Returns:
        All ayahs in the Juz with audio URLs
    """
    if juzNumber < 1 or juzNumber > 30:
        raise HTTPException(status_code=400, detail="Invalid Juz number. Must be 1-30")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QURAN_API_BASE}/juz/{juzNumber}/{reciter}",
                timeout=20.0
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                
                return {
                    "juzNumber": data["number"],
                    "reciter": reciter,
                    "ayahs": [
                        {
                            "number": ayah["number"],
                            "text": ayah["text"],
                            "audio": ayah.get("audio", ""),
                            "surah": {
                                "number": ayah["surah"]["number"],
                                "name": ayah["surah"]["name"],
                                "englishName": ayah["surah"]["englishName"]
                            }
                        }
                        for ayah in data["ayahs"]
                    ]
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch Juz audio")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quran API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

