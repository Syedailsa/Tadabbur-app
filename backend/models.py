

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime, date

# ==================== AUTH MODELS ====================

class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleSignInRequest(BaseModel):
    token: str = Field(..., description="Google OAuth token")

class AuthResponse(BaseModel):
    token: str
    message: str
    loginTime: datetime
    user_id: str
    username: str

# ==================== NOTIFICATION MODELS ====================

class NotificationCreate(BaseModel):
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    recipientId: str

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    time: datetime
    is_read: bool = False

# ==================== BOOKMARK MODELS ====================

class BookmarkCreate(BaseModel):
    itemId: str
    type: str = Field(..., description="e.g., 'ayah', 'story', 'tafsir'")
    surah_name: str = Field(..., description="Surah name in English")
    surah_no: int = Field(..., ge=1, le=114, description="Surah number (1-114)")
    ayah_no: int = Field(..., ge=1, description="Ayah number")
    total_ayah: int = Field(..., ge=1, description="Total ayahs in surah")
    ayah: str = Field(..., description="Arabic text of the ayah")

class BookmarkResponse(BaseModel):
    message: str
    bookmarkId: str
    time: datetime

class BookmarkItem(BaseModel):
    bookmarkId: str
    itemId: str
    type: str
    surahName: str
    surahNo: int
    ayahNo: int
    totalAyah: int
    ayah: str
    time: datetime
    
# ==================== USER PROFILE MODELS ====================

class ProfileUpdate(BaseModel):
    """Update profile with specific fields only"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    profilePicture: Optional[str] = Field(None, alias="image")  # Accept 'image' in request
    phoneNumber: Optional[str] = Field(None, alias="contact")   # Accept 'contact' in request
    dateofBirth: Optional[date] = None
    gender: Optional[Literal["Male", "Female", "Other"]] = None
    
    class Config:
        populate_by_name = True

class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    profilePicture: Optional[str] = None
    bio: Optional[str] = None
    lastName: Optional[str] = None
    dateofBirth: Optional[date] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = None
    gender: Optional[str] = None
    createdAt: datetime

class EditProfileRequest(BaseModel):
    """Edit Profile - Only these 6 fields"""
    email: Optional[EmailStr] = None
    image: Optional[str] = Field(None, description="Profile picture URL")
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    contact: Optional[str] = Field(None, description="Phone number")
    dateOfBirth: Optional[date] = None
    gender: Optional[Literal["Male", "Female", "Other"]] = None

class EditProfileResponse(BaseModel):
    message: str
    status: str = "success"
    updatedFields: list
    timestamp: datetime = Field(default_factory=datetime.utcnow)



# ==================== FEEDBACK MODELS ====================

class FeedbackCreate(BaseModel):
    userId: str
    message: str = Field(..., max_length=2000)
    rating: Literal["like", "dislike"]

class FeedbackResponse(BaseModel):
    id: str
    message: str
    status: str
    createdAt: datetime

# ==================== QURAN CONTENT MODELS ====================

class SurahResponse(BaseModel):
    id: int
    name: str
    transliteration: str
    total_ayahs: int
    revelation_type: str

class AyahResponse(BaseModel):
    ayah_number: int
    text_arabic: str
    text_translation: str
    surah_id: int
    surah_name: str

# ==================== COMMON RESPONSE MODELS ====================

class SuccessResponse(BaseModel):
    message: str
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    error: str
    status: str = "error"
    timestamp: datetime = Field(default_factory=datetime.utcnow)