
from rapidfuzz import process, fuzz

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

