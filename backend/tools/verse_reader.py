# import httpx
# import re
# import logging
# from typing import Optional, Dict, Any, List

# logger = logging.getLogger(__name__)

# class QuranVerseError(Exception):
#     """Base exception for Quran verse operations"""
#     pass

# class InvalidSurahError(QuranVerseError):
#     """Raised when surah number is invalid"""
#     pass

# class InvalidAyahError(QuranVerseError):
#     """Raised when ayah number is invalid"""
#     pass

# class QuranVerseAPIError(QuranVerseError):
#     """Raised when API request fails"""
#     pass

# # Surah metadata (total ayahs per surah)
# SURAH_METADATA = {
#     1: {"name": "Al-Fatihah", "ayahs": 7},
#     2: {"name": "Al-Baqarah", "ayahs": 286},
#     3: {"name": "Ali 'Imran", "ayahs": 200},
#     4: {"name": "An-Nisa", "ayahs": 176},
#     5: {"name": "Al-Ma'idah", "ayahs": 120},
#     6: {"name": "Al-An'am", "ayahs": 165},
#     7: {"name": "Al-A'raf", "ayahs": 206},
#     8: {"name": "Al-Anfal", "ayahs": 75},
#     9: {"name": "At-Tawbah", "ayahs": 129},
#     10: {"name": "Yunus", "ayahs": 109},
#     11: {"name": "Hud", "ayahs": 123},
#     12: {"name": "Yusuf", "ayahs": 111},
#     13: {"name": "Ar-Ra'd", "ayahs": 43},
#     14: {"name": "Ibrahim", "ayahs": 52},
#     15: {"name": "Al-Hijr", "ayahs": 99},
#     16: {"name": "An-Nahl", "ayahs": 128},
#     17: {"name": "Al-Isra", "ayahs": 111},
#     18: {"name": "Al-Kahf", "ayahs": 110},
#     19: {"name": "Maryam", "ayahs": 98},
#     20: {"name": "Taha", "ayahs": 135},
#     21: {"name": "Al-Anbya", "ayahs": 112},
#     22: {"name": "Al-Hajj", "ayahs": 78},
#     23: {"name": "Al-Mu'minun", "ayahs": 118},
#     24: {"name": "An-Nur", "ayahs": 64},
#     25: {"name": "Al-Furqan", "ayahs": 77},
#     26: {"name": "Ash-Shu'ara", "ayahs": 227},
#     27: {"name": "An-Naml", "ayahs": 93},
#     28: {"name": "Al-Qasas", "ayahs": 88},
#     29: {"name": "Al-'Ankabut", "ayahs": 69},
#     30: {"name": "Ar-Rum", "ayahs": 60},
#     31: {"name": "Luqman", "ayahs": 34},
#     32: {"name": "As-Sajdah", "ayahs": 30},
#     33: {"name": "Al-Ahzab", "ayahs": 73},
#     34: {"name": "Saba", "ayahs": 54},
#     35: {"name": "Fatir", "ayahs": 45},
#     36: {"name": "Ya-Sin", "ayahs": 83},
#     37: {"name": "As-Saffat", "ayahs": 182},
#     38: {"name": "Sad", "ayahs": 88},
#     39: {"name": "Az-Zumar", "ayahs": 75},
#     40: {"name": "Ghafir", "ayahs": 85},
#     41: {"name": "Fussilat", "ayahs": 54},
#     42: {"name": "Ash-Shuraa", "ayahs": 53},
#     43: {"name": "Az-Zukhruf", "ayahs": 89},
#     44: {"name": "Ad-Dukhan", "ayahs": 59},
#     45: {"name": "Al-Jathiyah", "ayahs": 37},
#     46: {"name": "Al-Ahqaf", "ayahs": 35},
#     47: {"name": "Muhammad", "ayahs": 38},
#     48: {"name": "Al-Fath", "ayahs": 29},
#     49: {"name": "Al-Hujurat", "ayahs": 18},
#     50: {"name": "Qaf", "ayahs": 45},
#     51: {"name": "Adh-Dhariyat", "ayahs": 60},
#     52: {"name": "At-Tur", "ayahs": 49},
#     53: {"name": "An-Najm", "ayahs": 62},
#     54: {"name": "Al-Qamar", "ayahs": 55},
#     55: {"name": "Ar-Rahman", "ayahs": 78},
#     56: {"name": "Al-Waqi'ah", "ayahs": 96},
#     57: {"name": "Al-Hadid", "ayahs": 29},
#     58: {"name": "Al-Mujadila", "ayahs": 22},
#     59: {"name": "Al-Hashr", "ayahs": 24},
#     60: {"name": "Al-Mumtahanah", "ayahs": 13},
#     61: {"name": "As-Saf", "ayahs": 14},
#     62: {"name": "Al-Jumu'ah", "ayahs": 11},
#     63: {"name": "Al-Munafiqun", "ayahs": 11},
#     64: {"name": "At-Taghabun", "ayahs": 18},
#     65: {"name": "At-Talaq", "ayahs": 12},
#     66: {"name": "At-Tahrim", "ayahs": 12},
#     67: {"name": "Al-Mulk", "ayahs": 30},
#     68: {"name": "Al-Qalam", "ayahs": 52},
#     69: {"name": "Al-Haqqah", "ayahs": 52},
#     70: {"name": "Al-Ma'arij", "ayahs": 44},
#     71: {"name": "Nuh", "ayahs": 28},
#     72: {"name": "Al-Jinn", "ayahs": 28},
#     73: {"name": "Al-Muzzammil", "ayahs": 20},
#     74: {"name": "Al-Muddaththir", "ayahs": 56},
#     75: {"name": "Al-Qiyamah", "ayahs": 40},
#     76: {"name": "Al-Insan", "ayahs": 31},
#     77: {"name": "Al-Mursalat", "ayahs": 50},
#     78: {"name": "An-Naba", "ayahs": 40},
#     79: {"name": "An-Nazi'at", "ayahs": 46},
#     80: {"name": "Abasa", "ayahs": 42},
#     81: {"name": "At-Takwir", "ayahs": 29},
#     82: {"name": "Al-Infitar", "ayahs": 19},
#     83: {"name": "Al-Mutaffifin", "ayahs": 36},
#     84: {"name": "Al-Inshiqaq", "ayahs": 25},
#     85: {"name": "Al-Buruj", "ayahs": 22},
#     86: {"name": "At-Tariq", "ayahs": 17},
#     87: {"name": "Al-A'la", "ayahs": 19},
#     88: {"name": "Al-Ghashiyah", "ayahs": 26},
#     89: {"name": "Al-Fajr", "ayahs": 30},
#     90: {"name": "Al-Balad", "ayahs": 20},
#     91: {"name": "Ash-Shams", "ayahs": 15},
#     92: {"name": "Al-Layl", "ayahs": 21},
#     93: {"name": "Ad-Duhaa", "ayahs": 11},
#     94: {"name": "Ash-Sharh", "ayahs": 8},
#     95: {"name": "At-Tin", "ayahs": 8},
#     96: {"name": "Al-Alaq", "ayahs": 19},
#     97: {"name": "Al-Qadr", "ayahs": 5},
#     98: {"name": "Al-Bayyinah", "ayahs": 8},
#     99: {"name": "Az-Zalzalah", "ayahs": 8},
#     100: {"name": "Al-'Adiyat", "ayahs": 11},
#     101: {"name": "Al-Qari'ah", "ayahs": 11},
#     102: {"name": "At-Takathur", "ayahs": 8},
#     103: {"name": "Al-'Asr", "ayahs": 3},
#     104: {"name": "Al-Humazah", "ayahs": 9},
#     105: {"name": "Al-Fil", "ayahs": 5},
#     106: {"name": "Quraysh", "ayahs": 4},
#     107: {"name": "Al-Ma'un", "ayahs": 7},
#     108: {"name": "Al-Kawthar", "ayahs": 3},
#     109: {"name": "Al-Kafirun", "ayahs": 6},
#     110: {"name": "An-Nasr", "ayahs": 3},
#     111: {"name": "Al-Masad", "ayahs": 5},
#     112: {"name": "Al-Ikhlas", "ayahs": 4},
#     113: {"name": "Al-Falaq", "ayahs": 5},
#     114: {"name": "An-Nas", "ayahs": 6}
# }

# def validate_surah_ayah(surah: int, ayah: int) -> None:
#     """Validate surah and ayah numbers"""
#     if surah < 1 or surah > 114:
#         raise InvalidSurahError(f"Invalid surah number: {surah}. Must be between 1 and 114.")
    
#     if surah not in SURAH_METADATA:
#         raise InvalidSurahError(f"Surah {surah} not found in metadata.")
    
#     max_ayah = SURAH_METADATA[surah]["ayahs"]
#     if ayah < 1 or ayah > max_ayah:
#         raise InvalidAyahError(
#             f"Invalid ayah number: {ayah}. Surah {surah} has {max_ayah} ayahs."
#         )

# async def fetch_quran_verse(surah: int, ayah: int) -> Dict[str, Any]:
#     """
#     Fetch a specific verse from Al-Quran API
    
#     Args:
#         surah: Surah number (1-114)
#         ayah: Ayah number
    
#     Returns:
#         Dict containing verse data with Arabic text, translation, and metadata
#     """
#     validate_surah_ayah(surah, ayah)
    
#     try:
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             # Fetch Arabic text
#             arabic_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}"
#             arabic_response = await client.get(arabic_url)
#             arabic_response.raise_for_status()
#             arabic_data = arabic_response.json()
            
#             # Fetch English translation
#             english_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.asad"
#             english_response = await client.get(english_url)
#             english_response.raise_for_status()
#             english_data = english_response.json()
            
#             if arabic_data["code"] != 200 or english_data["code"] != 200:
#                 raise QuranVerseAPIError("Failed to fetch verse data from API")
            
#             verse_data = {
#                 "success": True,
#                 "surah": surah,
#                 "ayah": ayah,
#                 "surah_name": SURAH_METADATA[surah]["name"],
#                 "total_ayahs": SURAH_METADATA[surah]["ayahs"],
#                 "arabic_text": arabic_data["data"]["text"],
#                 "english_text": english_data["data"]["text"],
#                 "number_in_quran": arabic_data["data"]["numberInQuran"],
#                 "number_in_surah": arabic_data["data"]["numberInSurah"],
#                 "juz": arabic_data["data"]["juz"],
#                 "can_go_previous": ayah > 1,
#                 "can_go_next": ayah < SURAH_METADATA[surah]["ayahs"]
#             }
            
#             logger.info(f"✅ Successfully fetched Surah {surah}:{ayah}")
#             return verse_data
            
#     except httpx.HTTPError as e:
#         logger.error(f"HTTP error fetching verse: {e}")
#         raise QuranVerseAPIError(f"Failed to connect to Quran API: {str(e)}")
#     except Exception as e:
#         logger.error(f"Unexpected error fetching verse: {e}")
#         raise QuranVerseAPIError(f"Unexpected error: {str(e)}")

# def parse_verse_request(text: str) -> Optional[Dict[str, int]]:
#     """
#     Parse user request to extract surah and ayah numbers
    
#     Examples:
#         "show me verse 2:255" -> {surah: 2, ayah: 255}
#         "read surah 1 ayah 1" -> {surah: 1, ayah: 1}
#         "verse 36 of surah 18" -> {surah: 18, ayah: 36}
#     """
#     text = text.lower()
    
#     # Pattern 1: surah:ayah format (2:255)
#     pattern1 = r'(?:surah\s*)?(\d+)\s*:\s*(\d+)'
#     match = re.search(pattern1, text)
#     if match:
#         return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
#     # Pattern 2: "surah X ayah Y" or "ayah Y surah X"
#     pattern2 = r'surah\s*(\d+)\s*(?:ayah|verse)\s*(\d+)'
#     match = re.search(pattern2, text)
#     if match:
#         return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
#     pattern3 = r'(?:ayah|verse)\s*(\d+)\s*(?:of\s*)?surah\s*(\d+)'
#     match = re.search(pattern3, text)
#     if match:
#         return {"surah": int(match.group(2)), "ayah": int(match.group(1))}
    
#     # Pattern 4: Just "verse X" (default to current surah if in context)
#     pattern4 = r'(?:verse|ayah)\s*(\d+)'
#     match = re.search(pattern4, text)
#     if match:
#         return {"surah": 1, "ayah": int(match.group(1))}  # Default to Al-Fatihah
    
#     return None

# async def get_verse_range(surah: int, start_ayah: int, end_ayah: int) -> List[Dict[str, Any]]:
#     """Fetch multiple verses in a range"""
#     validate_surah_ayah(surah, start_ayah)
#     validate_surah_ayah(surah, end_ayah)
    
#     if start_ayah > end_ayah:
#         raise InvalidAyahError("Start ayah must be less than or equal to end ayah")
    
#     verses = []
#     for ayah in range(start_ayah, end_ayah + 1):
#         verse = await fetch_quran_verse(surah, ayah)
#         verses.append(verse)
    
#     return verses



# import httpx
# import re
# import logging
# from typing import Optional, Dict, Any, List

# logger = logging.getLogger(__name__)

# class QuranVerseError(Exception):
#     """Base exception for Quran verse operations"""
#     pass

# class InvalidSurahError(QuranVerseError):
#     """Raised when surah number is invalid"""
#     pass

# class InvalidAyahError(QuranVerseError):
#     """Raised when ayah number is invalid"""
#     pass

# class QuranVerseAPIError(QuranVerseError):
#     """Raised when API request fails"""
#     pass

# # Surah metadata (total ayahs per surah)
# SURAH_METADATA = {
#     1: {"name": "Al-Fatihah", "ayahs": 7},
#     2: {"name": "Al-Baqarah", "ayahs": 286},
#     3: {"name": "Ali 'Imran", "ayahs": 200},
#     4: {"name": "An-Nisa", "ayahs": 176},
#     5: {"name": "Al-Ma'idah", "ayahs": 120},
#     6: {"name": "Al-An'am", "ayahs": 165},
#     7: {"name": "Al-A'raf", "ayahs": 206},
#     8: {"name": "Al-Anfal", "ayahs": 75},
#     9: {"name": "At-Tawbah", "ayahs": 129},
#     10: {"name": "Yunus", "ayahs": 109},
#     11: {"name": "Hud", "ayahs": 123},
#     12: {"name": "Yusuf", "ayahs": 111},
#     13: {"name": "Ar-Ra'd", "ayahs": 43},
#     14: {"name": "Ibrahim", "ayahs": 52},
#     15: {"name": "Al-Hijr", "ayahs": 99},
#     16: {"name": "An-Nahl", "ayahs": 128},
#     17: {"name": "Al-Isra", "ayahs": 111},
#     18: {"name": "Al-Kahf", "ayahs": 110},
#     19: {"name": "Maryam", "ayahs": 98},
#     20: {"name": "Taha", "ayahs": 135},
#     21: {"name": "Al-Anbya", "ayahs": 112},
#     22: {"name": "Al-Hajj", "ayahs": 78},
#     23: {"name": "Al-Mu'minun", "ayahs": 118},
#     24: {"name": "An-Nur", "ayahs": 64},
#     25: {"name": "Al-Furqan", "ayahs": 77},
#     26: {"name": "Ash-Shu'ara", "ayahs": 227},
#     27: {"name": "An-Naml", "ayahs": 93},
#     28: {"name": "Al-Qasas", "ayahs": 88},
#     29: {"name": "Al-'Ankabut", "ayahs": 69},
#     30: {"name": "Ar-Rum", "ayahs": 60},
#     31: {"name": "Luqman", "ayahs": 34},
#     32: {"name": "As-Sajdah", "ayahs": 30},
#     33: {"name": "Al-Ahzab", "ayahs": 73},
#     34: {"name": "Saba", "ayahs": 54},
#     35: {"name": "Fatir", "ayahs": 45},
#     36: {"name": "Ya-Sin", "ayahs": 83},
#     37: {"name": "As-Saffat", "ayahs": 182},
#     38: {"name": "Sad", "ayahs": 88},
#     39: {"name": "Az-Zumar", "ayahs": 75},
#     40: {"name": "Ghafir", "ayahs": 85},
#     41: {"name": "Fussilat", "ayahs": 54},
#     42: {"name": "Ash-Shuraa", "ayahs": 53},
#     43: {"name": "Az-Zukhruf", "ayahs": 89},
#     44: {"name": "Ad-Dukhan", "ayahs": 59},
#     45: {"name": "Al-Jathiyah", "ayahs": 37},
#     46: {"name": "Al-Ahqaf", "ayahs": 35},
#     47: {"name": "Muhammad", "ayahs": 38},
#     48: {"name": "Al-Fath", "ayahs": 29},
#     49: {"name": "Al-Hujurat", "ayahs": 18},
#     50: {"name": "Qaf", "ayahs": 45},
#     51: {"name": "Adh-Dhariyat", "ayahs": 60},
#     52: {"name": "At-Tur", "ayahs": 49},
#     53: {"name": "An-Najm", "ayahs": 62},
#     54: {"name": "Al-Qamar", "ayahs": 55},
#     55: {"name": "Ar-Rahman", "ayahs": 78},
#     56: {"name": "Al-Waqi'ah", "ayahs": 96},
#     57: {"name": "Al-Hadid", "ayahs": 29},
#     58: {"name": "Al-Mujadila", "ayahs": 22},
#     59: {"name": "Al-Hashr", "ayahs": 24},
#     60: {"name": "Al-Mumtahanah", "ayahs": 13},
#     61: {"name": "As-Saf", "ayahs": 14},
#     62: {"name": "Al-Jumu'ah", "ayahs": 11},
#     63: {"name": "Al-Munafiqun", "ayahs": 11},
#     64: {"name": "At-Taghabun", "ayahs": 18},
#     65: {"name": "At-Talaq", "ayahs": 12},
#     66: {"name": "At-Tahrim", "ayahs": 12},
#     67: {"name": "Al-Mulk", "ayahs": 30},
#     68: {"name": "Al-Qalam", "ayahs": 52},
#     69: {"name": "Al-Haqqah", "ayahs": 52},
#     70: {"name": "Al-Ma'arij", "ayahs": 44},
#     71: {"name": "Nuh", "ayahs": 28},
#     72: {"name": "Al-Jinn", "ayahs": 28},
#     73: {"name": "Al-Muzzammil", "ayahs": 20},
#     74: {"name": "Al-Muddaththir", "ayahs": 56},
#     75: {"name": "Al-Qiyamah", "ayahs": 40},
#     76: {"name": "Al-Insan", "ayahs": 31},
#     77: {"name": "Al-Mursalat", "ayahs": 50},
#     78: {"name": "An-Naba", "ayahs": 40},
#     79: {"name": "An-Nazi'at", "ayahs": 46},
#     80: {"name": "Abasa", "ayahs": 42},
#     81: {"name": "At-Takwir", "ayahs": 29},
#     82: {"name": "Al-Infitar", "ayahs": 19},
#     83: {"name": "Al-Mutaffifin", "ayahs": 36},
#     84: {"name": "Al-Inshiqaq", "ayahs": 25},
#     85: {"name": "Al-Buruj", "ayahs": 22},
#     86: {"name": "At-Tariq", "ayahs": 17},
#     87: {"name": "Al-A'la", "ayahs": 19},
#     88: {"name": "Al-Ghashiyah", "ayahs": 26},
#     89: {"name": "Al-Fajr", "ayahs": 30},
#     90: {"name": "Al-Balad", "ayahs": 20},
#     91: {"name": "Ash-Shams", "ayahs": 15},
#     92: {"name": "Al-Layl", "ayahs": 21},
#     93: {"name": "Ad-Duhaa", "ayahs": 11},
#     94: {"name": "Ash-Sharh", "ayahs": 8},
#     95: {"name": "At-Tin", "ayahs": 8},
#     96: {"name": "Al-Alaq", "ayahs": 19},
#     97: {"name": "Al-Qadr", "ayahs": 5},
#     98: {"name": "Al-Bayyinah", "ayahs": 8},
#     99: {"name": "Az-Zalzalah", "ayahs": 8},
#     100: {"name": "Al-'Adiyat", "ayahs": 11},
#     101: {"name": "Al-Qari'ah", "ayahs": 11},
#     102: {"name": "At-Takathur", "ayahs": 8},
#     103: {"name": "Al-'Asr", "ayahs": 3},
#     104: {"name": "Al-Humazah", "ayahs": 9},
#     105: {"name": "Al-Fil", "ayahs": 5},
#     106: {"name": "Quraysh", "ayahs": 4},
#     107: {"name": "Al-Ma'un", "ayahs": 7},
#     108: {"name": "Al-Kawthar", "ayahs": 3},
#     109: {"name": "Al-Kafirun", "ayahs": 6},
#     110: {"name": "An-Nasr", "ayahs": 3},
#     111: {"name": "Al-Masad", "ayahs": 5},
#     112: {"name": "Al-Ikhlas", "ayahs": 4},
#     113: {"name": "Al-Falaq", "ayahs": 5},
#     114: {"name": "An-Nas", "ayahs": 6}
# }

# def validate_surah_ayah(surah: int, ayah: int) -> None:
#     """Validate surah and ayah numbers"""
#     if surah < 1 or surah > 114:
#         raise InvalidSurahError(f"Invalid surah number: {surah}. Must be between 1 and 114.")
    
#     if surah not in SURAH_METADATA:
#         raise InvalidSurahError(f"Surah {surah} not found in metadata.")
    
#     max_ayah = SURAH_METADATA[surah]["ayahs"]
#     if ayah < 1 or ayah > max_ayah:
#         raise InvalidAyahError(
#             f"Invalid ayah number: {ayah}. Surah {surah} has {max_ayah} ayahs."
#         )

# async def fetch_quran_verse(surah: int, ayah: int) -> Dict[str, Any]:
#     """
#     Fetch a specific verse from Al-Quran API
    
#     Args:
#         surah: Surah number (1-114)
#         ayah: Ayah number
    
#     Returns:
#         Dict containing verse data with Arabic text, translation, and metadata
#     """
#     validate_surah_ayah(surah, ayah)
    
#     try:
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             # Fetch Arabic text
#             arabic_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}"
#             arabic_response = await client.get(arabic_url)
#             arabic_response.raise_for_status()
#             arabic_data = arabic_response.json()
            
#             # Fetch English translation
#             english_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.asad"
#             english_response = await client.get(english_url)
#             english_response.raise_for_status()
#             english_data = english_response.json()
            
#             if arabic_data["code"] != 200 or english_data["code"] != 200:
#                 raise QuranVerseAPIError("Failed to fetch verse data from API")
            
#             # Generate verse image URLs from Quran.com CDN
#             verse_images = {
#                 "small": f"https://cdn.quran.com/images/w/400_s{surah}_{ayah}.png",
#                 "medium": f"https://cdn.quran.com/images/w/800_s{surah}_{ayah}.png",
#                 "large": f"https://cdn.quran.com/images/w/1200_s{surah}_{ayah}.png",
#                 "xlarge": f"https://cdn.quran.com/images/w/1600_s{surah}_{ayah}.png"
#             }
            
#             verse_data = {
#                 "success": True,
#                 "surah": surah,
#                 "ayah": ayah,
#                 "surah_name": SURAH_METADATA[surah]["name"],
#                 "total_ayahs": SURAH_METADATA[surah]["ayahs"],
#                 "arabic_text": arabic_data["data"]["text"],
#                 "english_text": english_data["data"]["text"],
#                 "number_in_quran": arabic_data["data"]["numberInQuran"],
#                 "number_in_surah": arabic_data["data"]["numberInSurah"],
#                 "juz": arabic_data["data"]["juz"],
#                 "images": verse_images,
#                 "can_go_previous": ayah > 1,
#                 "can_go_next": ayah < SURAH_METADATA[surah]["ayahs"]
#             }
            
#             logger.info(f"✅ Successfully fetched Surah {surah}:{ayah}")
#             return verse_data
            
#     except httpx.HTTPError as e:
#         logger.error(f"HTTP error fetching verse: {e}")
#         raise QuranVerseAPIError(f"Failed to connect to Quran API: {str(e)}")
#     except Exception as e:
#         logger.error(f"Unexpected error fetching verse: {e}")
#         raise QuranVerseAPIError(f"Unexpected error: {str(e)}")

# def parse_verse_request(text: str) -> Optional[Dict[str, int]]:
#     """
#     Parse user request to extract surah and ayah numbers
    
#     Examples:
#         "show me verse 2:255" -> {surah: 2, ayah: 255}
#         "read surah 1 ayah 1" -> {surah: 1, ayah: 1}
#         "verse 36 of surah 18" -> {surah: 18, ayah: 36}
#     """
#     text = text.lower()
    
#     # Pattern 1: surah:ayah format (2:255)
#     pattern1 = r'(?:surah\s*)?(\d+)\s*:\s*(\d+)'
#     match = re.search(pattern1, text)
#     if match:
#         return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
#     # Pattern 2: "surah X ayah Y" or "ayah Y surah X"
#     pattern2 = r'surah\s*(\d+)\s*(?:ayah|verse)\s*(\d+)'
#     match = re.search(pattern2, text)
#     if match:
#         return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
#     pattern3 = r'(?:ayah|verse)\s*(\d+)\s*(?:of\s*)?surah\s*(\d+)'
#     match = re.search(pattern3, text)
#     if match:
#         return {"surah": int(match.group(2)), "ayah": int(match.group(1))}
    
#     # Pattern 4: Just "verse X" (default to current surah if in context)
#     pattern4 = r'(?:verse|ayah)\s*(\d+)'
#     match = re.search(pattern4, text)
#     if match:
#         return {"surah": 1, "ayah": int(match.group(1))}  # Default to Al-Fatihah
    
#     return None

# async def get_verse_range(surah: int, start_ayah: int, end_ayah: int) -> List[Dict[str, Any]]:
#     """Fetch multiple verses in a range"""
#     validate_surah_ayah(surah, start_ayah)
#     validate_surah_ayah(surah, end_ayah)
    
#     if start_ayah > end_ayah:
#         raise InvalidAyahError("Start ayah must be less than or equal to end ayah")
    
#     verses = []
#     for ayah in range(start_ayah, end_ayah + 1):
#         verse = await fetch_quran_verse(surah, ayah)
#         verses.append(verse)
    
#     return verses



import httpx
import re
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
# from enum import Enum

logger = logging.getLogger(__name__)

class QuranVerseError(Exception):
    """Base exception for Quran verse operations"""
    pass

class InvalidSurahError(QuranVerseError):
    """Raised when surah number is invalid"""
    pass

class InvalidAyahError(QuranVerseError):
    """Raised when ayah number is invalid"""
    pass

class QuranVerseAPIError(QuranVerseError):
    """Raised when API request fails"""
    pass

class Edition(str, Enum):
    """Available Quran editions"""
    # Arabic editions
    UTHMANI = "quran-uthmani"  # Uthmani script (most common)
    SIMPLE = "quran-simple"     # Simple clean text
    SIMPLE_ENHANCED = "quran-simple-enhanced"  # With diacritics
    
    # English translations
    SAHIH_INTERNATIONAL = "en.sahih"
    PICKTHALL = "en.pickthall"
    YUSUF_ALI = "en.yusufali"
    ASAD = "en.asad"
    CLEAR_QURAN = "en.clearquran"
    
    # Audio reciters
    ALAFASY = "ar.alafasy"
    HUSARY = "ar.husary"
    MINSHAWI = "ar.minshawi"

# Complete Surah metadata with English and Arabic names
SURAH_METADATA = {
    1: {"name_en": "Al-Fatihah", "name_ar": "الفاتحة", "ayahs": 7, "revelation": "Meccan"},
    2: {"name_en": "Al-Baqarah", "name_ar": "البقرة", "ayahs": 286, "revelation": "Medinan"},
    3: {"name_en": "Ali 'Imran", "name_ar": "آل عمران", "ayahs": 200, "revelation": "Medinan"},
    4: {"name_en": "An-Nisa", "name_ar": "النساء", "ayahs": 176, "revelation": "Medinan"},
    5: {"name_en": "Al-Ma'idah", "name_ar": "المائدة", "ayahs": 120, "revelation": "Medinan"},
    6: {"name_en": "Al-An'am", "name_ar": "الأنعام", "ayahs": 165, "revelation": "Meccan"},
    7: {"name_en": "Al-A'raf", "name_ar": "الأعراف", "ayahs": 206, "revelation": "Meccan"},
    8: {"name_en": "Al-Anfal", "name_ar": "الأنفال", "ayahs": 75, "revelation": "Medinan"},
    9: {"name_en": "At-Tawbah", "name_ar": "التوبة", "ayahs": 129, "revelation": "Medinan"},
    10: {"name_en": "Yunus", "name_ar": "يونس", "ayahs": 109, "revelation": "Meccan"},
    11: {"name_en": "Hud", "name_ar": "هود", "ayahs": 123, "revelation": "Meccan"},
    12: {"name_en": "Yusuf", "name_ar": "يوسف", "ayahs": 111, "revelation": "Meccan"},
    13: {"name_en": "Ar-Ra'd", "name_ar": "الرعد", "ayahs": 43, "revelation": "Medinan"},
    14: {"name_en": "Ibrahim", "name_ar": "ابراهيم", "ayahs": 52, "revelation": "Meccan"},
    15: {"name_en": "Al-Hijr", "name_ar": "الحجر", "ayahs": 99, "revelation": "Meccan"},
    16: {"name_en": "An-Nahl", "name_ar": "النحل", "ayahs": 128, "revelation": "Meccan"},
    17: {"name_en": "Al-Isra", "name_ar": "الإسراء", "ayahs": 111, "revelation": "Meccan"},
    18: {"name_en": "Al-Kahf", "name_ar": "الكهف", "ayahs": 110, "revelation": "Meccan"},
    19: {"name_en": "Maryam", "name_ar": "مريم", "ayahs": 98, "revelation": "Meccan"},
    20: {"name_en": "Taha", "name_ar": "طه", "ayahs": 135, "revelation": "Meccan"},
    21: {"name_en": "Al-Anbya", "name_ar": "الأنبياء", "ayahs": 112, "revelation": "Meccan"},
    22: {"name_en": "Al-Hajj", "name_ar": "الحج", "ayahs": 78, "revelation": "Medinan"},
    23: {"name_en": "Al-Mu'minun", "name_ar": "المؤمنون", "ayahs": 118, "revelation": "Meccan"},
    24: {"name_en": "An-Nur", "name_ar": "النور", "ayahs": 64, "revelation": "Medinan"},
    25: {"name_en": "Al-Furqan", "name_ar": "الفرقان", "ayahs": 77, "revelation": "Meccan"},
    26: {"name_en": "Ash-Shu'ara", "name_ar": "الشعراء", "ayahs": 227, "revelation": "Meccan"},
    27: {"name_en": "An-Naml", "name_ar": "النمل", "ayahs": 93, "revelation": "Meccan"},
    28: {"name_en": "Al-Qasas", "name_ar": "القصص", "ayahs": 88, "revelation": "Meccan"},
    29: {"name_en": "Al-'Ankabut", "name_ar": "العنكبوت", "ayahs": 69, "revelation": "Meccan"},
    30: {"name_en": "Ar-Rum", "name_ar": "الروم", "ayahs": 60, "revelation": "Meccan"},
    31: {"name_en": "Luqman", "name_ar": "لقمان", "ayahs": 34, "revelation": "Meccan"},
    32: {"name_en": "As-Sajdah", "name_ar": "السجدة", "ayahs": 30, "revelation": "Meccan"},
    33: {"name_en": "Al-Ahzab", "name_ar": "الأحزاب", "ayahs": 73, "revelation": "Medinan"},
    34: {"name_en": "Saba", "name_ar": "سبإ", "ayahs": 54, "revelation": "Meccan"},
    35: {"name_en": "Fatir", "name_ar": "فاطر", "ayahs": 45, "revelation": "Meccan"},
    36: {"name_en": "Ya-Sin", "name_ar": "يس", "ayahs": 83, "revelation": "Meccan"},
    37: {"name_en": "As-Saffat", "name_ar": "الصافات", "ayahs": 182, "revelation": "Meccan"},
    38: {"name_en": "Sad", "name_ar": "ص", "ayahs": 88, "revelation": "Meccan"},
    39: {"name_en": "Az-Zumar", "name_ar": "الزمر", "ayahs": 75, "revelation": "Meccan"},
    40: {"name_en": "Ghafir", "name_ar": "غافر", "ayahs": 85, "revelation": "Meccan"},
    41: {"name_en": "Fussilat", "name_ar": "فصلت", "ayahs": 54, "revelation": "Meccan"},
    42: {"name_en": "Ash-Shuraa", "name_ar": "الشورى", "ayahs": 53, "revelation": "Meccan"},
    43: {"name_en": "Az-Zukhruf", "name_ar": "الزخرف", "ayahs": 89, "revelation": "Meccan"},
    44: {"name_en": "Ad-Dukhan", "name_ar": "الدخان", "ayahs": 59, "revelation": "Meccan"},
    45: {"name_en": "Al-Jathiyah", "name_ar": "الجاثية", "ayahs": 37, "revelation": "Meccan"},
    46: {"name_en": "Al-Ahqaf", "name_ar": "الأحقاف", "ayahs": 35, "revelation": "Meccan"},
    47: {"name_en": "Muhammad", "name_ar": "محمد", "ayahs": 38, "revelation": "Medinan"},
    48: {"name_en": "Al-Fath", "name_ar": "الفتح", "ayahs": 29, "revelation": "Medinan"},
    49: {"name_en": "Al-Hujurat", "name_ar": "الحجرات", "ayahs": 18, "revelation": "Medinan"},
    50: {"name_en": "Qaf", "name_ar": "ق", "ayahs": 45, "revelation": "Meccan"},
    51: {"name_en": "Adh-Dhariyat", "name_ar": "الذاريات", "ayahs": 60, "revelation": "Meccan"},
    52: {"name_en": "At-Tur", "name_ar": "الطور", "ayahs": 49, "revelation": "Meccan"},
    53: {"name_en": "An-Najm", "name_ar": "النجم", "ayahs": 62, "revelation": "Meccan"},
    54: {"name_en": "Al-Qamar", "name_ar": "القمر", "ayahs": 55, "revelation": "Meccan"},
    55: {"name_en": "Ar-Rahman", "name_ar": "الرحمن", "ayahs": 78, "revelation": "Medinan"},
    56: {"name_en": "Al-Waqi'ah", "name_ar": "الواقعة", "ayahs": 96, "revelation": "Meccan"},
    57: {"name_en": "Al-Hadid", "name_ar": "الحديد", "ayahs": 29, "revelation": "Medinan"},
    58: {"name_en": "Al-Mujadila", "name_ar": "المجادلة", "ayahs": 22, "revelation": "Medinan"},
    59: {"name_en": "Al-Hashr", "name_ar": "الحشر", "ayahs": 24, "revelation": "Medinan"},
    60: {"name_en": "Al-Mumtahanah", "name_ar": "الممتحنة", "ayahs": 13, "revelation": "Medinan"},
    61: {"name_en": "As-Saf", "name_ar": "الصف", "ayahs": 14, "revelation": "Medinan"},
    62: {"name_en": "Al-Jumu'ah", "name_ar": "الجمعة", "ayahs": 11, "revelation": "Medinan"},
    63: {"name_en": "Al-Munafiqun", "name_ar": "المنافقون", "ayahs": 11, "revelation": "Medinan"},
    64: {"name_en": "At-Taghabun", "name_ar": "التغابن", "ayahs": 18, "revelation": "Medinan"},
    65: {"name_en": "At-Talaq", "name_ar": "الطلاق", "ayahs": 12, "revelation": "Medinan"},
    66: {"name_en": "At-Tahrim", "name_ar": "التحريم", "ayahs": 12, "revelation": "Medinan"},
    67: {"name_en": "Al-Mulk", "name_ar": "الملك", "ayahs": 30, "revelation": "Meccan"},
    68: {"name_en": "Al-Qalam", "name_ar": "القلم", "ayahs": 52, "revelation": "Meccan"},
    69: {"name_en": "Al-Haqqah", "name_ar": "الحاقة", "ayahs": 52, "revelation": "Meccan"},
    70: {"name_en": "Al-Ma'arij", "name_ar": "المعارج", "ayahs": 44, "revelation": "Meccan"},
    71: {"name_en": "Nuh", "name_ar": "نوح", "ayahs": 28, "revelation": "Meccan"},
    72: {"name_en": "Al-Jinn", "name_ar": "الجن", "ayahs": 28, "revelation": "Meccan"},
    73: {"name_en": "Al-Muzzammil", "name_ar": "المزمل", "ayahs": 20, "revelation": "Meccan"},
    74: {"name_en": "Al-Muddaththir", "name_ar": "المدثر", "ayahs": 56, "revelation": "Meccan"},
    75: {"name_en": "Al-Qiyamah", "name_ar": "القيامة", "ayahs": 40, "revelation": "Meccan"},
    76: {"name_en": "Al-Insan", "name_ar": "الانسان", "ayahs": 31, "revelation": "Medinan"},
    77: {"name_en": "Al-Mursalat", "name_ar": "المرسلات", "ayahs": 50, "revelation": "Meccan"},
    78: {"name_en": "An-Naba", "name_ar": "النبإ", "ayahs": 40, "revelation": "Meccan"},
    79: {"name_en": "An-Nazi'at", "name_ar": "النازعات", "ayahs": 46, "revelation": "Meccan"},
    80: {"name_en": "Abasa", "name_ar": "عبس", "ayahs": 42, "revelation": "Meccan"},
    81: {"name_en": "At-Takwir", "name_ar": "التكوير", "ayahs": 29, "revelation": "Meccan"},
    82: {"name_en": "Al-Infitar", "name_ar": "الإنفطار", "ayahs": 19, "revelation": "Meccan"},
    83: {"name_en": "Al-Mutaffifin", "name_ar": "المطففين", "ayahs": 36, "revelation": "Meccan"},
    84: {"name_en": "Al-Inshiqaq", "name_ar": "الإنشقاق", "ayahs": 25, "revelation": "Meccan"},
    85: {"name_en": "Al-Buruj", "name_ar": "البروج", "ayahs": 22, "revelation": "Meccan"},
    86: {"name_en": "At-Tariq", "name_ar": "الطارق", "ayahs": 17, "revelation": "Meccan"},
    87: {"name_en": "Al-A'la", "name_ar": "الأعلى", "ayahs": 19, "revelation": "Meccan"},
    88: {"name_en": "Al-Ghashiyah", "name_ar": "الغاشية", "ayahs": 26, "revelation": "Meccan"},
    89: {"name_en": "Al-Fajr", "name_ar": "الفجر", "ayahs": 30, "revelation": "Meccan"},
    90: {"name_en": "Al-Balad", "name_ar": "البلد", "ayahs": 20, "revelation": "Meccan"},
    91: {"name_en": "Ash-Shams", "name_ar": "الشمس", "ayahs": 15, "revelation": "Meccan"},
    92: {"name_en": "Al-Layl", "name_ar": "الليل", "ayahs": 21, "revelation": "Meccan"},
    93: {"name_en": "Ad-Duhaa", "name_ar": "الضحى", "ayahs": 11, "revelation": "Meccan"},
    94: {"name_en": "Ash-Sharh", "name_ar": "الشرح", "ayahs": 8, "revelation": "Meccan"},
    95: {"name_en": "At-Tin", "name_ar": "التين", "ayahs": 8, "revelation": "Meccan"},
    96: {"name_en": "Al-Alaq", "name_ar": "العلق", "ayahs": 19, "revelation": "Meccan"},
    97: {"name_en": "Al-Qadr", "name_ar": "القدر", "ayahs": 5, "revelation": "Meccan"},
    98: {"name_en": "Al-Bayyinah", "name_ar": "البينة", "ayahs": 8, "revelation": "Medinan"},
    99: {"name_en": "Az-Zalzalah", "name_ar": "الزلزلة", "ayahs": 8, "revelation": "Medinan"},
    100: {"name_en": "Al-'Adiyat", "name_ar": "العاديات", "ayahs": 11, "revelation": "Meccan"},
    101: {"name_en": "Al-Qari'ah", "name_ar": "القارعة", "ayahs": 11, "revelation": "Meccan"},
    102: {"name_en": "At-Takathur", "name_ar": "التكاثر", "ayahs": 8, "revelation": "Meccan"},
    103: {"name_en": "Al-'Asr", "name_ar": "العصر", "ayahs": 3, "revelation": "Meccan"},
    104: {"name_en": "Al-Humazah", "name_ar": "الهمزة", "ayahs": 9, "revelation": "Meccan"},
    105: {"name_en": "Al-Fil", "name_ar": "الفيل", "ayahs": 5, "revelation": "Meccan"},
    106: {"name_en": "Quraysh", "name_ar": "قريش", "ayahs": 4, "revelation": "Meccan"},
    107: {"name_en": "Al-Ma'un", "name_ar": "الماعون", "ayahs": 7, "revelation": "Meccan"},
    108: {"name_en": "Al-Kawthar", "name_ar": "الكوثر", "ayahs": 3, "revelation": "Meccan"},
    109: {"name_en": "Al-Kafirun", "name_ar": "الكافرون", "ayahs": 6, "revelation": "Meccan"},
    110: {"name_en": "An-Nasr", "name_ar": "النصر", "ayahs": 3, "revelation": "Medinan"},
    111: {"name_en": "Al-Masad", "name_ar": "المسد", "ayahs": 5, "revelation": "Meccan"},
    112: {"name_en": "Al-Ikhlas", "name_ar": "الإخلاص", "ayahs": 4, "revelation": "Meccan"},
    113: {"name_en": "Al-Falaq", "name_ar": "الفلق", "ayahs": 5, "revelation": "Meccan"},
    114: {"name_en": "An-Nas", "name_ar": "الناس", "ayahs": 6, "revelation": "Meccan"}
}

def validate_surah_ayah(surah: int, ayah: int) -> None:
    """Validate surah and ayah numbers with detailed error messages"""
    if surah < 1 or surah > 114:
        raise InvalidSurahError(
            f"Invalid surah number: {surah}. Must be between 1 and 114. "
            f"The Quran has 114 surahs."
        )
    
    if surah not in SURAH_METADATA:
        raise InvalidSurahError(f"Surah {surah} metadata not found.")
    
    max_ayah = SURAH_METADATA[surah]["ayahs"]
    surah_name = SURAH_METADATA[surah]["name_en"]
    
    if ayah < 1 or ayah > max_ayah:
        raise InvalidAyahError(
            f"Invalid ayah number: {ayah}. Surah {surah} ({surah_name}) has "
            f"{max_ayah} ayah{'s' if max_ayah > 1 else ''}. "
            f"Please enter a number between 1 and {max_ayah}."
        )

async def fetch_quran_verse(
    surah: int, 
    ayah: int,
    arabic_edition: str = Edition.UTHMANI,
    translation_edition: str = Edition.SAHIH_INTERNATIONAL,
    include_audio: bool = False,
    audio_reciter: str = Edition.ALAFASY
) -> Dict[str, Any]:
    """
    Fetch a specific verse with multiple editions and optional audio
    
    Args:
        surah: Surah number (1-114)
        ayah: Ayah number
        arabic_edition: Arabic text edition (default: Uthmani)
        translation_edition: Translation edition (default: Sahih International)
        include_audio: Whether to include audio URL
        audio_reciter: Reciter for audio (default: Alafasy)
    
    Returns:
        Complete verse data with text, translation, metadata, and optional audio
    """
    validate_surah_ayah(surah, ayah)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch Arabic text
            arabic_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{arabic_edition}"
            arabic_response = await client.get(arabic_url)
            arabic_response.raise_for_status()
            arabic_data = arabic_response.json()
            
            # Fetch translation
            translation_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{translation_edition}"
            translation_response = await client.get(translation_url)
            translation_response.raise_for_status()
            translation_data = translation_response.json()
            
            # Validate API responses
            if arabic_data.get("code") != 200 or translation_data.get("code") != 200:
                raise QuranVerseAPIError("API returned non-200 status code")
            
            # Extract data
            arabic_ayah = arabic_data["data"]
            trans_ayah = translation_data["data"]
            
            # Get surah metadata
            surah_meta = SURAH_METADATA[surah]
            
            # Build verse data
            verse_data = {
                "success": True,
                "surah": surah,
                "ayah": ayah,
                "surah_name_en": surah_meta["name_en"],
                "surah_name_ar": surah_meta["name_ar"],
                "total_ayahs": surah_meta["ayahs"],
                "revelation_type": surah_meta["revelation"],
                
                # Arabic text
                "arabic_text": arabic_ayah["text"],
                "arabic_edition": arabic_edition,
                
                # Translation
                "translation_text": trans_ayah["text"],
                "translation_edition": translation_edition,
                "translator_name": trans_ayah.get("edition", {}).get("englishName", ""),
                
                # Metadata
                "number_in_quran": arabic_ayah.get("numberInQuran", arabic_ayah.get("numberInSurah", 0)),
                "number_in_surah": arabic_ayah.get("numberInSurah", arabic_ayah.get("number", 0)),
                "juz": arabic_ayah.get("juz", 0),
                "manzil": arabic_ayah.get("manzil", 0),
                "ruku": arabic_ayah.get("ruku", 0),
                "hizb_quarter": arabic_ayah.get("hizbQuarter", 0),
                "sajda": arabic_ayah.get("sajda", False),
                
                # Images
                "images": {
                    "normal": f"https://cdn.islamic.network/quran/images/{surah}_{ayah}.png",
                    "high_resolution": f"https://cdn.islamic.network/quran/images/high-resolution/{surah}_{ayah}.png"
                },

                # Navigation
                "can_go_previous": ayah > 1,
                "can_go_next": ayah < surah_meta["ayahs"],
                "previous": {"surah": surah, "ayah": ayah - 1} if ayah > 1 else None,
                "next": {"surah": surah, "ayah": ayah + 1} if ayah < surah_meta["ayahs"] else None,
            }
            
            # Add audio if requested
            if include_audio:
                audio_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{audio_reciter}"
                try:
                    audio_response = await client.get(audio_url)
                    audio_response.raise_for_status()
                    audio_data = audio_response.json()
                    
                    if audio_data.get("code") == 200:
                        verse_data["audio"] = {
                            "url": audio_data["data"].get("audio"),
                            "reciter": audio_reciter,
                            "reciter_name": audio_data["data"].get("edition", {}).get("englishName", "")
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch audio: {e}")
                    verse_data["audio"] = None
            
            logger.info(f"✅ Successfully fetched Surah {surah}:{ayah}")
            return verse_data
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} error: {e}")
        raise QuranVerseAPIError(
            f"Failed to fetch verse from API (HTTP {e.response.status_code}). "
            f"Please check your internet connection and try again."
        )
    except httpx.RequestError as e:
        logger.error(f"Network error: {e}")
        raise QuranVerseAPIError(
            f"Network error: {str(e)}. Please check your internet connection."
        )
    except Exception as e:
        logger.exception(f"Unexpected error fetching verse")
        raise QuranVerseAPIError(f"Unexpected error: {str(e)}")

def word_to_number(word: str) -> Optional[int]:
    """Convert word numbers to integers"""
    word_numbers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
        "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10
    }
    return word_numbers.get(word.lower())

def preprocess_text(text: str) -> str:
    """Replace word numbers with digits in text"""
    words = text.split()
    processed_words = []
    for word in words:
        # Remove punctuation for matching
        clean_word = re.sub(r'[^\w]', '', word)
        num = word_to_number(clean_word)
        if num is not None:
            processed_words.append(str(num))
        else:
            processed_words.append(word)
    return ' '.join(processed_words)

def parse_verse_request(text: str) -> Optional[Dict[str, int]]:
    """
    Intelligently parse user request to extract surah and ayah numbers

    Supports formats:
    - "2:255" or "surah 2 ayah 255"
    - "verse 36 of surah 18"
    - "Al-Baqarah verse 255"
    - "show me ayat al kursi" (known verses)
    - Word numbers: "verse two of surah fatiha"
    """
    text = text.lower().strip()
    text = preprocess_text(text)
    
    # Known verses mapping
    known_verses = {
        "ayat al kursi": {"surah": 2, "ayah": 255},
        "ayatul kursi": {"surah": 2, "ayah": 255},
        "throne verse": {"surah": 2, "ayah": 255},
        "light verse": {"surah": 24, "ayah": 35},
        "ayat an nur": {"surah": 24, "ayah": 35},
    }
    
    for key, value in known_verses.items():
        if key in text:
            return value
    
    # Pattern 1: surah:ayah (e.g., "2:255")
    pattern1 = r'(?:surah\s*)?(\d+)\s*:\s*(\d+)'
    match = re.search(pattern1, text)
    if match:
        return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
    # Pattern 2: "surah X ayah Y"
    pattern2 = r'surah\s*(\d+)\s*(?:ayah|verse|ayat)\s*(\d+)'
    match = re.search(pattern2, text)
    if match:
        return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
    # Pattern 3: "ayah Y of/from surah X"
    pattern3 = r'(?:ayah|verse|ayat)\s*(\d+)\s*(?:of|from|in)\s*surah\s*(\d+)'
    match = re.search(pattern3, text)
    if match:
        return {"surah": int(match.group(2)), "ayah": int(match.group(1))}
    
    # Pattern 4: Surah name + verse number
    for surah_num, meta in SURAH_METADATA.items():
        name_en = meta["name_en"].lower().replace("-", "").replace("'", "")
        # Check if surah name is in text or any significant word from text is in surah name
        if name_en in text or any(word in name_en for word in text.split() if len(word) > 3):
            verse_pattern = r'(?:verse|ayah|ayat)\s*(\d+)'
            verse_match = re.search(verse_pattern, text)
            if verse_match:
                return {"surah": surah_num, "ayah": int(verse_match.group(1))}
    
    return None

async def get_verse_range(
    surah: int, 
    start_ayah: int, 
    end_ayah: int,
    arabic_edition: str = Edition.UTHMANI,
    translation_edition: str = Edition.SAHIH_INTERNATIONAL
) -> List[Dict[str, Any]]:
    """
    Fetch multiple verses in a range
    
    Args:
        surah: Surah number
        start_ayah: Starting ayah
        end_ayah: Ending ayah (inclusive)
        arabic_edition: Arabic text edition
        translation_edition: Translation edition
    
    Returns:
        List of verse data dictionaries
    """
    validate_surah_ayah(surah, start_ayah)
    validate_surah_ayah(surah, end_ayah)
    
    if start_ayah > end_ayah:
        raise InvalidAyahError(
            f"Start ayah ({start_ayah}) must be less than or equal to end ayah ({end_ayah})"
        )
    
    verses = []
    for ayah_num in range(start_ayah, end_ayah + 1):
        try:
            verse = await fetch_quran_verse(
                surah=surah,
                ayah=ayah_num,
                arabic_edition=arabic_edition,
                translation_edition=translation_edition,
                include_audio=False
            )
            verses.append(verse)
        except Exception as e:
            logger.error(f"Failed to fetch ayah {ayah_num}: {e}")
            continue
    
    return verses

def get_available_editions() -> Dict[str, List[str]]:
    """Get all available editions grouped by type"""
    return {
        "arabic": [
            Edition.UTHMANI,
            Edition.SIMPLE,
            Edition.SIMPLE_ENHANCED
        ],
        "english_translations": [
            Edition.SAHIH_INTERNATIONAL,
            Edition.PICKTHALL,
            Edition.YUSUF_ALI,
            Edition.ASAD,
            Edition.CLEAR_QURAN
        ],
        "audio_reciters": [
            Edition.ALAFASY,
            Edition.HUSARY,
            Edition.MINSHAWI
        ]
    }

def get_surah_info(surah: int) -> Dict[str, Any]:
    """Get complete information about a surah"""
    if surah < 1 or surah > 114:
        raise InvalidSurahError(f"Invalid surah number: {surah}")
    
    meta = SURAH_METADATA[surah]
    return {
        "number": surah,
        "name_en": meta["name_en"],
        "name_ar": meta["name_ar"],
        "total_ayahs": meta["ayahs"],
        "revelation_type": meta["revelation"],
        "revelation_place": "Mecca" if meta["revelation"] == "Meccan" else "Medina"
    }