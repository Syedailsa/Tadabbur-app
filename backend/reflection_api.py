from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import secrets

from database import get_db_connection
from utils import get_current_user

# ==================== MODELS ====================

class RecentReflectionSave(BaseModel):
    surah_name_eng: str
    surah_name_arabic: str
    surah_no: int = Field(..., ge=1, le=114)
    total_ayah: int
    last_ayah_read: Optional[int] = None

class RecentReflectionResponse(BaseModel):
    id: str
    user_id: str
    surah_name_eng: str
    surah_name_arabic: str
    surah_no: int
    total_ayah: int
    last_ayah_read: Optional[int]
    last_read_at: datetime
    created_at: datetime

class SaveResponse(BaseModel):
    message: str
    status: str = "success"
    reflection_id: str
    timestamp: datetime

# ==================== ROUTER ====================

reflection_router = APIRouter(prefix="/recent-reflection", tags=["Recent Reflection"])

# ==================== HELPER ====================

def generate_reflection_id() -> str:
    return f"ref_{secrets.token_hex(8)}"

# ==================== ENDPOINTS ====================

@reflection_router.post("/save", response_model=SaveResponse)
async def save_recent_reflection(
    req: RecentReflectionSave,
    user: dict = Depends(get_current_user)
):
    """
    Save reflection (append-only)

    Headers:
        Authorization: Bearer {token}

    Body:
        surah_name_eng: Al-Fatihah
        surah_name_arabic: الفاتحة
        surah_no: 1
        total_ayah: 7
        last_ayah_read: 5
    """
    async with get_db_connection() as conn:
        reflection_id = generate_reflection_id()
        current_time = datetime.utcnow()

        await conn.execute("""
            INSERT INTO recent_reflections (
                reflection_id,
                user_id,
                surah_name_eng,
                surah_name_arabic,
                surah_no,
                total_ayah,
                last_ayah_read,
                last_read_at,
                created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            reflection_id,
            user["user_id"],
            req.surah_name_eng,
            req.surah_name_arabic,
            req.surah_no,
            req.total_ayah,
            req.last_ayah_read,
            current_time,
            current_time
        )

        return SaveResponse(
            message="Reflection saved successfully",
            status="success",
            reflection_id=reflection_id,
            timestamp=current_time
        )


@reflection_router.get("", response_model=Optional[RecentReflectionResponse])
async def get_recent_reflection(user: dict = Depends(get_current_user)):
    """
    Get last read position
    
    Headers:
        Authorization: Bearer {token}
    
    Returns:
        Recent reflection data or null
    """
    async with get_db_connection() as conn:
        reflection = await conn.fetchrow("""
            SELECT 
                reflection_id as id,
                user_id,
                surah_name_eng,
                surah_name_arabic,
                surah_no,
                total_ayah,
                last_ayah_read,
                last_read_at,
                created_at
            FROM recent_reflections 
            WHERE user_id = $1
        """, user['user_id'])
        
        if not reflection:
            return None
        
        return dict(reflection)