from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal, Union
from datetime import datetime, date
from typing import List
import uuid

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
    user_id: uuid.UUID
    firstname: str


class SajdaVerse(BaseModel):
    id: Optional[int] = Field(None, description="The id of the sajda verse")
    recommended: Optional[bool] = Field(None, description = "Sajda recommended or not")
    obligatory: Optional[bool] = Field(None, description="Sajda obligatory or not")

class Verse(BaseModel):
    number: Optional[int] = None
    audio: Optional[str] = None
    audioSecondary: Optional[List[str]] = None
    text: Optional[str] = None
    numberInSurah: Optional[int] = None
    juz: Optional[int] = None
    manzil: Optional[int] = None
    ruku: Optional[int] = None
    hizbQuarter: Optional[int] = None
    sajda: Optional[Union[bool, SajdaVerse]] = None
    verse_image_url: Optional[str] = None


class Surah(BaseModel):
    number: Optional[int] = Field(..., description="The number of the Surah")
    name: Optional[str] = Field(..., description="The name of the Surah")
    englishName: Optional[str] = Field(None, description="The english name of the surah")
    englishNameTranslation: Optional[str] = Field(
        None, description="The translation of the english name of the surah"
    )
    revelationType: Optional[Literal["Meccan", "Medinan"]] = Field(
        None, description="The type of Revelation: Meccan or Medinan"
    )
    ayahs: Optional[List[Verse]] = Field(
        None, description="List of verses in the Surah"
    )

class VerseImageData(BaseModel):
    surah_name: str = Field(..., description = "The name of the surah")
    surah_englishName: str = Field(..., description = "The engish name of the surah")
    verse_number_in_surah: int = Field(..., description = "The verse number relative to the Surah")
    text: str = Field(None, description = "The english translation of the verse" )
    verse_image_url: str = Field(None, description = "The verse image URL")


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
    id: str
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
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    gender: Optional[str] = None

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

class ImageDeleteRequest(BaseModel):
    """Request model for image deletion"""
    image_url: str = Field(..., description="URL path of the image to delete")