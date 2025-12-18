

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime, date

# ==================== AUTH MODELS ====================

class SignupRequest(BaseModel):
    firstname: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator('firstname')
    def firstname_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Firstname must be alphanumeric')
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
    firstname: str

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
    surah_name_eng: str = Field(..., description="Surah name in English")
    surah_name_arb: str = Field(..., description="Surah name in Arabic")
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
    surahNameEng: str
    surahNameArb: str
    surahNo: int
    ayahNo: int
    totalAyah: int
    ayah: str
    time: datetime

class BookmarkDeleteRequest(BaseModel):
    bookmarkId: str
    
# ==================== USER PROFILE MODELS ====================

class ProfileUpdate(BaseModel):
    """Update profile with specific fields only"""
    firstname: Optional[str] = Field(None, min_length=3, max_length=50)
    lastName: Optional[str] = None
    dateofBirth: Optional[date] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = Field(None, alias="contact")   # Accept 'contact' in request
    email: Optional[EmailStr] = None
    profilePicture: Optional[str] = Field(None, alias="image")  # Accept 'image' in request
    bio: Optional[str] = None

    class Config:
        populate_by_name = True

class UserProfile(BaseModel):
    id: str
    firstname: str
    email: str
    profilePicture: Optional[str] = Field(None, alias= "image")
    bio: Optional[str] = None
    lastName: Optional[str] = None
    dateofBirth: Optional[date] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = None
    gender: Optional[str] = None
    createdAt: datetime

class EditProfileRequest(BaseModel):
    """Edit Profile - Fields that can be updated"""
    email: Optional[EmailStr] = None
    image: Optional[str] = Field(None, description="Profile picture URL")
    firstname: Optional[str] = Field(None, min_length=3, max_length=50)
    last_name: Optional[str] = Field(None, min_length=3, max_length=50)
    contact: Optional[str] = Field(None, description="Phone number")
    dateOfBirth: Optional[date] = None
    gender: Optional[Literal["Male", "Female", "Other"]] = None
    bio: Optional[str] = Field(None, description="User bio")

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