
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

# ==================== ROUTERS ====================

quran_router = APIRouter(prefix="/surah", tags=["Quran Content"])
parah_router = APIRouter(prefix="/parah", tags=["Parah"])
story_router = APIRouter(prefix="/stories", tags=["Stories"])

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











# from fastapi import APIRouter, HTTPException
# from typing import List
# from pydantic import BaseModel
# from database import get_db_connection

# # ==================== MODELS ====================

# class SurahBasic(BaseModel):
#     number: int
#     name: str
#     englishName: str
#     englishNameTranslation: str
#     numberOfAyahs: int
#     revelationType: str

# class AyahDetail(BaseModel):
#     number: int
#     text_arabic: str
#     text_english: str
#     numberInSurah: int
#     surah_number: int
#     surah_name: str

# # ==================== ROUTER ====================

# quran_local_router = APIRouter(prefix="/surah", tags=["Quran Content - Local DB"])

# # ==================== STEP 1: DATABASE TABLES ====================

# async def create_quran_tables():
#     """
#     Yeh tables database mein banane honge
#     """
#     async with get_db_connection() as conn:
#         # SURAHS TABLE
#         await conn.execute("""
#             CREATE TABLE IF NOT EXISTS surahs (
#                 number INTEGER PRIMARY KEY,
#                 name_arabic TEXT NOT NULL,
#                 name_english TEXT NOT NULL,
#                 name_translation TEXT NOT NULL,
#                 total_ayahs INTEGER NOT NULL,
#                 revelation_type TEXT NOT NULL CHECK(revelation_type IN ('Meccan', 'Medinan')),
#                 created_at TIMESTAMP DEFAULT NOW()
#             )
#         """)
        
#         # AYAHS TABLE
#         await conn.execute("""
#             CREATE TABLE IF NOT EXISTS ayahs (
#                 id SERIAL PRIMARY KEY,
#                 ayah_number INTEGER NOT NULL,
#                 surah_number INTEGER NOT NULL,
#                 number_in_surah INTEGER NOT NULL,
#                 text_arabic TEXT NOT NULL,
#                 text_english TEXT NOT NULL,
#                 text_urdu TEXT,
#                 created_at TIMESTAMP DEFAULT NOW(),
#                 FOREIGN KEY (surah_number) REFERENCES surahs(number),
#                 UNIQUE(surah_number, number_in_surah)
#             )
#         """)
        
#         # INDEXES for faster queries
#         await conn.execute("""
#             CREATE INDEX IF NOT EXISTS idx_ayahs_surah 
#             ON ayahs(surah_number, number_in_surah)
#         """)
        
#         print("✅ Quran tables created")

# # ==================== ENDPOINTS ====================

# @quran_local_router.get("", response_model=List[SurahBasic])
# async def get_all_surahs_local():
#     """
#     Get all Surahs from LOCAL database
    
#     Returns:
#         List of 114 Surahs
#     """
#     async with get_db_connection() as conn:
#         rows = await conn.fetch("""
#             SELECT 
#                 number,
#                 name_arabic as name,
#                 name_english as "englishName",
#                 name_translation as "englishNameTranslation",
#                 total_ayahs as "numberOfAyahs",
#                 revelation_type as "revelationType"
#             FROM surahs
#             ORDER BY number
#         """)
        
#         if not rows:
#             raise HTTPException(
#                 status_code=404, 
#                 detail="No surahs found. Database needs to be populated."
#             )
        
#         return [dict(row) for row in rows]


# @quran_local_router.get("/{surahId}")
# async def get_surah_by_id_local(surahId: int):
#     """
#     Get specific Surah with all ayahs from LOCAL database
    
#     Args:
#         surahId: Surah number (1-114)
#     """
#     if surahId < 1 or surahId > 114:
#         raise HTTPException(status_code=400, detail="Invalid Surah ID (1-114)")
    
#     async with get_db_connection() as conn:
#         # Get Surah info
#         surah = await conn.fetchrow("""
#             SELECT 
#                 number,
#                 name_arabic as name,
#                 name_english as "englishName",
#                 name_translation as "englishNameTranslation",
#                 total_ayahs as "numberOfAyahs",
#                 revelation_type as "revelationType"
#             FROM surahs
#             WHERE number = $1
#         """, surahId)
        
#         if not surah:
#             raise HTTPException(status_code=404, detail="Surah not found")
        
#         # Get all ayahs
#         ayahs = await conn.fetch("""
#             SELECT 
#                 ayah_number as number,
#                 number_in_surah as "numberInSurah",
#                 text_arabic,
#                 text_english
#             FROM ayahs
#             WHERE surah_number = $1
#             ORDER BY number_in_surah
#         """, surahId)
        
#         return {
#             **dict(surah),
#             "ayahs": [dict(a) for a in ayahs]
#         }


# @quran_local_router.get("/{surahId}/ayah/{ayahNumber}")
# async def get_specific_ayah_local(surahId: int, ayahNumber: int):
#     """
#     Get specific Ayah from LOCAL database
    
#     Args:
#         surahId: Surah number (1-114)
#         ayahNumber: Ayah number within surah
#     """
#     if surahId < 1 or surahId > 114:
#         raise HTTPException(status_code=400, detail="Invalid Surah ID")
    
#     async with get_db_connection() as conn:
#         ayah = await conn.fetchrow("""
#             SELECT 
#                 a.ayah_number as number,
#                 a.number_in_surah as "numberInSurah",
#                 a.text_arabic,
#                 a.text_english,
#                 s.number as surah_number,
#                 s.name_arabic as surah_name,
#                 s.name_english as surah_name_english
#             FROM ayahs a
#             JOIN surahs s ON a.surah_number = s.number
#             WHERE a.surah_number = $1 AND a.number_in_surah = $2
#         """, surahId, ayahNumber)
        
#         if not ayah:
#             raise HTTPException(status_code=404, detail="Ayah not found")
        
#         return {
#             "number": ayah["number"],
#             "numberInSurah": ayah["numberInSurah"],
#             "text_arabic": ayah["text_arabic"],
#             "text_english": ayah["text_english"],
#             "surah": {
#                 "number": ayah["surah_number"],
#                 "name": ayah["surah_name"],
#                 "englishName": ayah["surah_name_english"]
#             }
#         }


# # ==================== DATA POPULATION (One-time setup) ====================

# async def populate_quran_data():
#     """
#     YEH FUNCTION ek baar run karna hoga database populate karne ke liye
    
#     Data source options:
#     1. Download from: https://github.com/islamic-network/quran.com-api
#     2. Use CSV file
#     3. Manually insert
    
#     Example: Insert sample data
#     """
#     async with get_db_connection() as conn:
#         # Check if already populated
#         count = await conn.fetchval("SELECT COUNT(*) FROM surahs")
#         if count > 0:
#             print("⚠️ Database already populated")
#             return
        
#         # Sample: Insert first few Surahs (you need to add all 114)
#         sample_surahs = [
#             (1, "الفاتحة", "Al-Fatihah", "The Opening", 7, "Meccan"),
#             (2, "البقرة", "Al-Baqarah", "The Cow", 286, "Medinan"),
#             (3, "آل عمران", "Aal-E-Imran", "The Family of Imran", 200, "Medinan"),
#             # ... Add all 114 surahs
#         ]
        
#         for surah in sample_surahs:
#             await conn.execute("""
#                 INSERT INTO surahs (number, name_arabic, name_english, name_translation, total_ayahs, revelation_type)
#                 VALUES ($1, $2, $3, $4, $5, $6)
#                 ON CONFLICT (number) DO NOTHING
#             """, *surah)
        
#         # Sample: Insert ayahs for Surah Al-Fatihah
#         sample_ayahs = [
#             (1, 1, 1, "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "In the name of Allah, the Entirely Merciful, the Especially Merciful."),
#             (2, 1, 2, "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "All praise is due to Allah, Lord of the worlds."),
#             # ... Add remaining ayahs
#         ]
        
#         for ayah in sample_ayahs:
#             await conn.execute("""
#                 INSERT INTO ayahs (ayah_number, surah_number, number_in_surah, text_arabic, text_english)
#                 VALUES ($1, $2, $3, $4, $5)
#                 ON CONFLICT (surah_number, number_in_surah) DO NOTHING
#             """, *ayah)
        
#         print("✅ Sample Quran data inserted")


# # ==================== HOW TO USE ====================
# """
# USAGE IN MAIN.PY:

# 1. Import router:
#    from quran_api_local import quran_local_router, create_quran_tables, populate_quran_data

# 2. Register router:
#    app.include_router(quran_local_router)

# 3. In lifespan startup:
#    await create_quran_tables()
#    await populate_quran_data()  # One-time only

# 4. Ready to use!
# """