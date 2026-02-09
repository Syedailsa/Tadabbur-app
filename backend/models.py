
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime, date
from uuid import UUID

# ==================== AUTH MODELS ====================

class SignupRequest(BaseModel):
    firstname: str = Field(..., min_length=1, max_length=20)
    lastName: Optional[str] = None
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
    user_id: UUID
    firstname: str
    lastName: Optional[str] = None
    # lastName: str 

# ==================== NOTIFICATION MODELS ====================

class NotificationCreate(BaseModel):
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    recipientId: UUID

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    time: datetime
    is_read: bool = False

class MarkNotificationReadRequest(BaseModel):
    notification_id: Optional[str] = None
    mark_all: Optional[bool] = False

# ==================== BOOKMARK MODELS ====================

class BookmarkCreate(BaseModel):
    surah_name_eng: str = Field(..., description="Surah name in English")
    type: Literal["surah", "story"] =  Field(..., description="Type of bookmark: 'surah' or 'story'")
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
    type: Literal["surah", "story"]
    ayahNo: int
    totalAyah: int
    ayah: str
    time: datetime

class BookmarkDeleteRequest(BaseModel):
    bookmarkId: str
    
# # ==================== USER PROFILE MODELS ====================

class UserProfileResponse(BaseModel):
    """
    Production-ready profile response
    Single profileImageUrl field - simple and clear!
    """
    id: UUID
    firstname: str
    email: str
    profileImageUrl: Optional[str] = Field(None, description="URL to fetch profile image: /users/image/{id}")
    bio: Optional[str] = None
    lastName: Optional[str] = None
    dateofBirth: Optional[date] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = None
    gender: Optional[str] = None
    createdAt: datetime

class EditProfileRequest(BaseModel):
    """Simple edit request - no image field needed"""
    firstname: Optional[str] = Field(None, min_length=3, max_length=50)
    lastName: Optional[str] = None
    dateofBirth: Optional[date] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = None
    # email: Optional[EmailStr] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    imageUrl: Optional[str] = None

class EditProfileResponse(BaseModel):
    message: str
    status: str = "success"
    updatedFields: list
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ImageUploadRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image")
    filename: str

class ImageUploadResponse(BaseModel):
    message: str
    status: str = "success"
    profileImageUrl: str = Field(..., description="URL to fetch the image")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ==================== FEEDBACK MODELS ====================

class FeedbackCreate(BaseModel):
    userId: UUID
    message: str = Field(..., max_length=2000)
    rating: Literal["like", "dislike"]

class FeedbackResponse(BaseModel):
    id: UUID
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

class ImageDeleteRequest(BaseModel):
    """Request model for image deletion"""
    image_url: str = Field(..., description="URL path of the image to delete")












