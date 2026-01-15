import httpx
import re
import logging
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from enum import Enum
from data.data import comprehensive_surah_metadata
from tools.utils import get_surah_id_from_name, clean_surah_name

logger = logging.getLogger(__name__)

class QuranVerseError(Exception):
    """Base exception for Quran verse operations"""
    pass

class InvalidSurahError(QuranVerseError):
    pass

class InvalidAyahError(QuranVerseError):
    pass

class QuranVerseAPIError(QuranVerseError):
    pass

class Edition(str, Enum):
    UTHMANI = "quran-uthmani" 
    SIMPLE = "quran-simple"     
    SIMPLE_ENHANCED = "quran-simple-enhanced"  
    SAHIH_INTERNATIONAL = "en.sahih"
    PICKTHALL = "en.pickthall"
    YUSUF_ALI = "en.yusufali"
    ASAD = "en.asad"
    CLEAR_QURAN = "en.clearquran"
    ALAFASY = "ar.alafasy"
    HUSARY = "ar.husary"
    MINSHAWI = "ar.minshawi"

# SURAH_METADATA = {
#     meta["surah_number"]: {
#         "name_en": meta["englishName"],
#         "name_ar": "", # Assuming name_ar isn't in your specific data snippet, or use meta.get('name') if available
#         "ayahs": meta.get("numberOfAyahs", 286), 
#         "revelation": meta.get("revelationType", "Meccan")
#     }
#     for meta in comprehensive_surah_metadata
# }

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
    """Validate surah and ayah numbers"""
    if surah < 1 or surah > 114:
        raise InvalidSurahError(f"Invalid surah number: {surah}")
    
    if surah not in SURAH_METADATA:
        if surah > 114: raise InvalidSurahError(f"Surah {surah} metadata not found.")
    
    if surah in SURAH_METADATA:
        max_ayah = SURAH_METADATA[surah]["ayahs"]
        if ayah < 1 or ayah > max_ayah:
            raise InvalidAyahError(f"Invalid ayah: {ayah}. Surah {surah} has {max_ayah} ayahs.")

def get_quran_verse(
    surah: int, 
    ayah: int,
    arabic_edition: str = Edition.UTHMANI,
    translation_edition: str = "en.asad",
    include_audio: bool = False,
    audio_reciter: str = Edition.ALAFASY
) -> Dict[str, Any]:
    """
    Directly fetch verse data. Returns a Dictionary.
    Used by the Backend WebSocket to send data to the Frontend.
    """
    try:
        surah = int(surah)
        ayah = int(ayah)
    except (ValueError, TypeError):
        return {"success": False, "error": "Surah and Ayah must be numbers."}

    validate_surah_ayah(surah, ayah) 
    
    try:
        with httpx.Client(timeout=15.0) as client:
            arabic_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{arabic_edition}"
            arabic_response = client.get(arabic_url)
            arabic_response.raise_for_status()
            arabic_data = arabic_response.json()
            
            translation_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{translation_edition}"
            translation_response = client.get(translation_url)
            translation_response.raise_for_status()
            translation_data = translation_response.json()
            
            if arabic_data.get("code") != 200 or translation_data.get("code") != 200:
                raise QuranVerseAPIError("API returned non-200 status code")
            
            arabic_ayah = arabic_data["data"]
            trans_ayah = translation_data["data"]
            surah_meta_api = arabic_ayah["surah"]

            verse_data = {
                "success": True,
                "surah": surah,
                "ayah": ayah,
                "surah_name_en": surah_meta_api["englishName"],
                "surah_name_ar": surah_meta_api["name"],
                "total_ayahs": surah_meta_api.get("numberOfAyahs", 0),
                "revelation_type": surah_meta_api.get("revelationType", "Meccan"),
                
                "arabic_text": arabic_ayah["text"],
                "arabic_edition": arabic_edition,
                
                "translation_text": trans_ayah["text"],
                "translation_edition": translation_edition,
                "translator_name": trans_ayah.get("edition", {}).get("englishName", ""),
                
                "number_in_quran": arabic_ayah.get("numberInQuran"),
                "juz": arabic_ayah.get("juz"),
                "manzil": arabic_ayah.get("manzil"),
                "ruku": arabic_ayah.get("ruku"),
                "sajda": arabic_ayah.get("sajda", False),
                
                "images": {
                    "normal": f"https://cdn.islamic.network/quran/images/{surah}_{ayah}.png",
                    "high_resolution": f"https://cdn.islamic.network/quran/images/high-resolution/{surah}_{ayah}.png"
                },
                
                "can_go_previous": ayah > 1,
                "can_go_next": ayah < surah_meta_api.get("numberOfAyahs", 999),
            }
            
            if include_audio:
                audio_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{audio_reciter}"
                try:
                    audio_resp = client.get(audio_url)
                    audio_data = audio_resp.json()
                    if audio_data.get("code") == 200:
                        verse_data["audio"] = {
                            "url": audio_data["data"].get("audio"),
                            "reciter": audio_reciter,
                            "reciter_name": audio_data["data"].get("edition", {}).get("englishName", "")
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch audio for verse: {e}")
            
            logger.info(f"✅ Successfully fetched Surah {surah}:{ayah}")
            return verse_data
            
    except Exception as e:
        logger.error(f"Error fetching verse: {e}")
        return {"success": False, "error": str(e)}

@tool
def fetch_quran_verse(
    surah: int, 
    ayah: int,
    arabic_edition: str = "quran-uthmani",
    translation_edition: str = "en.sahih"
) -> str:
    """
    Fetch a specific Quran verse with Arabic text and English translation.
    Args:
        surah: Surah number (1-114)
        ayah: Ayah number within the surah
    """
    data = get_quran_verse(surah, ayah, arabic_edition, translation_edition, include_audio=False)
    
    if not data.get("success"):
        return f"Error: {data.get('error')}"
    
    return f"""
## 📖 {data['surah_name_en']} ({data['surah_name_ar']}) - Ayah {data['ayah']}
**Revelation:** {data['revelation_type']} | **Total Ayahs:** {data['total_ayahs']}
---
### 🕌 Arabic Text:
{data['arabic_text']}
---
### 📝 English Translation:
{data['translation_text']}
---
**Translator:** {data['translator_name']}
**Juz:** {data['juz']} | **Ruku:** {data['ruku']} | **Manzil:** {data['manzil']}
""".strip()

def word_to_number(word: str) -> Optional[int]:
    """Convert word numbers to integers"""
    word_numbers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    return word_numbers.get(word.lower())

def preprocess_text(text: str) -> str:
    """Replace word numbers with digits in text"""
    words = text.split()
    processed_words = []
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word)
        num = word_to_number(clean_word)
        if num is not None:
            processed_words.append(str(num))
        else:
            processed_words.append(word)
    return ' '.join(processed_words)

def parse_verse_request(text: str) -> Optional[Dict[str, int]]:
    """Intelligently parse user request to extract surah and ayah numbers"""
    text = text.lower().strip()
    text = preprocess_text(text)
    
    known_verses = {
        "ayat al kursi": {"surah": 2, "ayah": 255},
        "ayatul kursi": {"surah": 2, "ayah": 255},
    }
    
    for key, value in known_verses.items():
        if key in text:
            return value
    
    patterns = [
        r'(?:surah\s*)?(\d+)\s*:\s*(\d+)',  # 2:255
        r'surah\s*(\d+)\s*(?:ayah|verse|ayat)\s*(\d+)', # surah 2 ayah 255
        r'(?:ayah|verse|ayat)\s*(\d+)\s*(?:of|from|in)\s*surah\s*(\d+)' # ayah 255 of surah 2
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if "of surah" in text or "from surah" in text:
                return {"surah": int(match.group(2)), "ayah": int(match.group(1))}
            return {"surah": int(match.group(1)), "ayah": int(match.group(2))}
    
    return None

def get_verse_range(
    surah: int, 
    start_ayah: int, 
    end_ayah: int,
    arabic_edition: str = Edition.UTHMANI,
    translation_edition: str = Edition.SAHIH_INTERNATIONAL
) -> List[Dict[str, Any]]:
    """Fetch multiple verses in a range"""
    validate_surah_ayah(surah, start_ayah)
    validate_surah_ayah(surah, end_ayah)
    
    if start_ayah > end_ayah:
        raise InvalidAyahError(f"Start ayah ({start_ayah}) must be <= end ayah ({end_ayah})")
    
    verses = []
    for ayah_num in range(start_ayah, end_ayah + 1):
        try:
            verse = get_quran_verse(
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

def extract_verse_data(response_text: str) -> Optional[dict]:
    if not response_text:
        return None
    
    clean_text = clean_surah_name(response_text)
    
    verse_indicators = ["surah", "ayah", "verse", "chapter"]
    has_indicator = any(indicator in clean_text.lower() for indicator in verse_indicators)
    
    if has_indicator:
        import re
        
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', response_text))
        
        surah_match = re.search(r'(?:Surah|surah|Chapter)\s+([^\(\)\d,:]+)', clean_text)
        ayah_match = re.search(r'(?:Ayah|ayah|Verse|verse)[sS]?\s*(\d+)', clean_text)
        chapter_num_match = re.search(r'\((\d+)\)', clean_text)
        
        if (surah_match or chapter_num_match) and has_arabic:
            surah_number = None
            surah_name_raw = "Unknown"
            
            if surah_match:
                surah_name_raw = clean_surah_name(surah_match.group(1))
                
                surah_number = get_surah_id_from_name(surah_name_raw)
            
            if not surah_number and chapter_num_match:
                surah_number = int(chapter_num_match.group(1))
            
            if not surah_number and surah_name_raw != "Unknown":
                best_match_name = normalize_surah(surah_name_raw, surah_name_english_array)
                if best_match_name:
                    for meta in comprehensive_surah_metadata:
                        if meta.get("englishName") == best_match_name:
                            surah_number = int(meta.get("surah_number"))
                            break

            extracted_ayah = int(ayah_match.group(1)) if ayah_match else 1
            
            if not surah_number:
                logging.warning(f"[EXTRACT_VERSE] Failed to identify Surah from '{surah_name_raw}'.")
                surah_number = 2 if extracted_ayah > 7 else 1

            logging.info(f"[EXTRACT_VERSE] Extracted: Surah {surah_number}, Ayah {extracted_ayah}")

            return {
                "has_verse": True,
                "surah_name": surah_name_raw,
                "surah_number": surah_number, 
                "surah_name_ar": "", 
                "ayah_number": extracted_ayah,
                "full_response": response_text,
                "contains_arabic": has_arabic
            }
    
    return None