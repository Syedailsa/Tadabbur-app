import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from datetime import datetime, timedelta
from models import BookmarkDeleteRequest
from typing import List, Optional
import base64
import logging
from fastapi.responses import StreamingResponse
import os
from supabase import create_client, Client
from fastapi import File, UploadFile
from fastapi import Form

# Local imports

from models import *

from utils.authentication import (
    hash_password, verify_password, create_access_token,
    verify_google_token, generate_notification_id,
    generate_bookmark_id, generate_feedback_id, get_current_user
)
from utils.generate_uuid import generate_uuid
from database import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== SUPABASE SETUP ====================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "profile-images")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info(f"Supabase client created: {supabase is not None}")

profile_router = APIRouter(prefix="/users", tags=["User Profile"])

# ==================== AUTH ROUTER ====================

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/signup", response_model=AuthResponse)
async def signup(req: SignupRequest):
    """Register new user with email & password"""
    async with get_db_connection() as conn:
        # Check if user exists
        existing = await conn.fetchrow(
            "SELECT email FROM users WHERE email = $1 OR firstname = $2",
            req.email, req.firstname
        )

        if existing:
            raise HTTPException(status_code=400, detail="Email or firstname already registered")

        # Create user
        user_id = generate_uuid()
        pwd_hash = hash_password(req.password)

        await conn.execute("""
            INSERT INTO users (user_id, firstname, email, password_hash, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, user_id, req.firstname, req.email, pwd_hash)

        # Generate token
        token = create_access_token(user_id, req.firstname)
        login_time = datetime.utcnow()

        # Save token
        expires_at = login_time + timedelta(hours=24*7)
        await conn.execute("""
            INSERT INTO auth_tokens (user_id, token, expires_at)
            VALUES ($1, $2, $3)
        """, user_id, token, expires_at)

        return AuthResponse(
            token=token,
            message="Signup successful",
            loginTime=login_time,
            user_id=user_id,
            firstname=req.firstname
        )

@auth_router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login with email & password"""
    async with get_db_connection() as conn:
        user = await conn.fetchrow("""
            SELECT user_id, firstname, password_hash
            FROM users WHERE email = $1
        """, req.email)
        
        if not user or not verify_password(req.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate token
        token = create_access_token(user['user_id'], user['firstname'])
        login_time = datetime.utcnow()

        # Save token
        expires_at = login_time + timedelta(hours=24*7)
        await conn.execute("""
            INSERT INTO auth_tokens (user_id, token, expires_at)
            VALUES ($1, $2, $3)
        """, user['user_id'], token, expires_at)

        # Auto notification
        notif_id = generate_notification_id()
        await conn.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, notif_id, user['user_id'], "Login Successful",
            "You logged into your account", login_time)

        return AuthResponse(
            token=token,
            message="Login successful",
            loginTime=login_time,
            user_id=user['user_id'],
            firstname=user['firstname']
        )

@auth_router.post("/google-signin", response_model=AuthResponse)
async def google_signin(req: GoogleSignInRequest):
    """Sign in with Google OAuth"""
    
    google_data = await verify_google_token(req.token)
    
    async with get_db_connection() as conn:
        user = await conn.fetchrow("""
            SELECT user_id, firstname, email
            FROM google_users WHERE google_id = $1
        """, google_data['google_id'])
        
        if not user:
            # Create new user
            user_id = generate_uuid()
            username = google_data['name'] or google_data['email'].split('@')[0]
            
            # Ensure unique firstname
            counter = 1
            base_username = username
            while await conn.fetchrow("SELECT 1 FROM google_users WHERE firstname = $1", username):
                username = f"{base_username}{counter}"
                counter += 1
            
            await conn.execute("""
                INSERT INTO google_users (user_id, google_id, email, firstname, profile_image_url)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, google_data['google_id'], google_data['email'],
                username, google_data.get('picture'))

            user = {'user_id': user_id, 'firstname': username, 'email': google_data['email']}
        
        token = create_access_token(user['user_id'], user['firstname'])
        login_time = datetime.utcnow()

        # Auto notification
        notif_id = generate_notification_id()
        await conn.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, notif_id, user['user_id'], "Login Successful",
            "You logged into your account via Google", login_time)

        return AuthResponse(
            token=token,
            message="Google sign-in successful",
            loginTime=login_time,
            user_id=user['user_id'],
            firstname=user['firstname']
        )

# ==================== PERSONALIZATION ROUTER ====================

personalization_router = APIRouter(prefix="/personalization", tags=["Personalization"])

@personalization_router.post("/save", response_model=PersonalizationResponse)
async def save_personalization(
    req: PersonalizationRequest, 
    user: dict = Depends(get_current_user)
):
    """
    Save user personalization (username & age)
    Only needs to be done once per user
    """
    try:
        async with get_db_connection() as conn:
            # Check if user is Google user
            is_google = await conn.fetchval(
                "SELECT 1 FROM google_users WHERE user_id = $1", 
                user['user_id']
            )
            
            if is_google:
                # Update Google user
                await conn.execute("""
                    UPDATE google_users 
                    SET username = $1, age = $2, is_personalized = TRUE
                    WHERE user_id = $3
                """, req.username, req.age, user['user_id'])
            else:
                # Update regular user
                await conn.execute("""
                    UPDATE users 
                    SET username = $1, age = $2, is_personalized = TRUE, updated_at = NOW()
                    WHERE user_id = $3
                """, req.username, req.age, user['user_id'])
            
            logger.info(f"✅ Personalization saved for user {user['user_id']}: {req.username}, age {req.age}")
            
            return PersonalizationResponse(
                message="Personalization saved successfully",
                username=req.username,
                age=req.age,
                is_personalized=True,
                timestamp=datetime.utcnow()
            )
            
    except Exception as e:
        logger.error(f"❌ Personalization save error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save personalization: {str(e)}")


@personalization_router.get("/status", response_model=PersonalizationResponse)
async def get_personalization_status(user: dict = Depends(get_current_user)):
    """
    Check if user has completed personalization
    Returns username, age, and is_personalized flag
    """
    try:
        async with get_db_connection() as conn:
            # Try Google users first
            result = await conn.fetchrow("""
                SELECT username, age, COALESCE(is_personalized, FALSE) as is_personalized
                FROM google_users
                WHERE user_id = $1
            """, user['user_id'])
            
            if not result:
                # Try regular users
                result = await conn.fetchrow("""
                    SELECT username, age, COALESCE(is_personalized, FALSE) as is_personalized
                    FROM users
                    WHERE user_id = $1
                """, user['user_id'])
            
            if not result:
                raise HTTPException(status_code=404, detail="User not found")
            
            return PersonalizationResponse(
                message="Personalization status retrieved",
                username=result['username'],
                age=result['age'],
                is_personalized=result['is_personalized'],
                timestamp=datetime.utcnow()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get personalization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get personalization: {str(e)}")

        
# ==================== NOTIFICATIONS ROUTER ====================

notif_router = APIRouter(prefix="/notifications", tags=["Notifications"])

@notif_router.post("/send", response_model=SuccessResponse)
async def send_notification(req: NotificationCreate, user: dict = Depends(get_current_user)):
    """Send notification to a user"""
    notif_id = generate_notification_id()
    
    async with get_db_connection() as conn:
        await conn.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, notif_id, req.recipientId, req.title, req.message)
    
    return SuccessResponse(message="Notification sent successfully")

@notif_router.get("", response_model=List[NotificationResponse])
async def get_notifications(user: dict = Depends(get_current_user)):
    """
    Get all notifications and automatically mark them as read
    """
    async with get_db_connection() as conn:
        # 1. Fetch notifications
        rows = await conn.fetch("""
            SELECT notification_id as id, title, message, COALESCE(is_read, FALSE) as is_read, created_at as time
            FROM notifications WHERE user_id = $1
            ORDER BY created_at DESC
        """, user['user_id'])

        # 2. Automatically mark them as read in the background
        await conn.execute("""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE user_id = $1 AND (is_read = FALSE OR is_read IS NULL)
        """, user['user_id'])

    return [dict(row) for row in rows]

@notif_router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: str, user: dict = Depends(get_current_user)):
    """Get a specific notification by ID"""
    async with get_db_connection() as conn:
        row = await conn.fetchrow("""
            SELECT notification_id as id, title, message, COALESCE(is_read, FALSE) as is_read, created_at as time
            FROM notifications WHERE notification_id = $1 AND user_id = $2
        """, notification_id, user['user_id'])

        if not row:
            raise HTTPException(status_code=404, detail="Notification not found")

    return dict(row)

# ==================== SINGLE PUT ENDPOINT ====================

@notif_router.put("/mark-read", response_model=SuccessResponse)
async def mark_notifications_as_read(
    req: MarkNotificationReadRequest,
    user: dict = Depends(get_current_user)
):
    """
    Mark notification(s) as read
    - Pass notification_id to mark single notification
    - Pass mark_all=true to mark all notifications as read
    """
    async with get_db_connection() as conn:
        if req.mark_all:
            # Mark all notifications as read
            result = await conn.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE user_id = $1 AND (is_read = FALSE OR is_read IS NULL)
            """, user['user_id'])
            
            return SuccessResponse(
                message="All notifications marked as read",
                timestamp=datetime.utcnow()
            )
        
        elif req.notification_id:
            # Mark single notification as read
            result = await conn.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE notification_id = $1 AND user_id = $2
            """, req.notification_id, user['user_id'])
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Notification not found")
            
            return SuccessResponse(
                message="Notification marked as read",
                timestamp=datetime.utcnow()
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either notification_id or mark_all must be provided"
            )

# # ==================== BOOKMARKS ROUTER ====================

bookmark_router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

@bookmark_router.post("", response_model=BookmarkResponse)
async def create_bookmark(req: BookmarkCreate, user: dict = Depends(get_current_user)):
    """Save bookmark for user"""
    bookmark_id = generate_bookmark_id()
    created_time = datetime.utcnow()

    async with get_db_connection() as conn:
        # Check duplicate
        existing = await conn.fetchrow("""
            SELECT bookmark_id FROM bookmarks
            WHERE user_id = $1 AND surah_no = $2 AND ayah_no = $3
        """, user['user_id'], req.surah_no, req.ayah_no)

        if existing:
            raise HTTPException(status_code=400, detail="Already bookmarked")

        # Create bookmark
        await conn.execute("""
            INSERT INTO bookmarks (
                bookmark_id, user_id, type,
                surah_name_eng, surah_name_arb, surah_no, ayah_no, total_ayah, ayah,
                created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, bookmark_id, user['user_id'],
            req.type, req.surah_name_eng, req.surah_name_arb, req.surah_no, req.ayah_no, req.total_ayah, req.ayah,
            created_time)
        # Auto notification
        notif_id = generate_notification_id()
        await conn.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, notif_id, user['user_id'], "Bookmark Saved",
            f"You saved {req.surah_name_eng}, Ayah {req.ayah_no} to your bookmarks", created_time)

    return BookmarkResponse(
        message="Bookmark saved successfully",
        bookmarkId=bookmark_id,
        time=created_time
    )

@bookmark_router.get("", response_model=List[BookmarkItem])
async def get_bookmarks(user: dict = Depends(get_current_user)):
    """Get all bookmarks for current user"""
    async with get_db_connection() as conn:
        rows = await conn.fetch("""
            SELECT
                bookmark_id as "bookmarkId",
                COALESCE(surah_name_eng, 'Unknown') as "surahNameEng",
                COALESCE(surah_name_arb, 'Unknown') as "surahNameArb",
                surah_no as "surahNo",
                type,
                ayah_no as "ayahNo",
                total_ayah as "totalAyah",
                COALESCE(ayah, '') as ayah,
                created_at as time
            FROM bookmarks
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, user['user_id'])

    
    print("Rows", rows)
    return [dict(row) for row in rows]

@bookmark_router.get("/{bookmark_id}", response_model=BookmarkItem)
async def get_bookmark(bookmark_id: str, user: dict = Depends(get_current_user)):
    """Get a specific bookmark by ID"""
    async with get_db_connection() as conn:
        row = await conn.fetchrow("""
            SELECT
                bookmark_id as "bookmarkId",
                COALESCE(surah_name_eng, 'Unknown') as "surahNameEng",
                COALESCE(surah_name_arb, 'Unknown') as "surahNameArb",
                surah_no as "surahNo",
                type,
                ayah_no as "ayahNo",
                total_ayah as "totalAyah",
                COALESCE(ayah, '') as ayah,
                created_at as time
            FROM bookmarks WHERE bookmark_id = $1 AND user_id = $2
        """, bookmark_id, user['user_id'])

        if not row:
            raise HTTPException(status_code=404, detail="Bookmark not found")

    return dict(row)

@bookmark_router.delete("", response_model=SuccessResponse)
async def delete_bookmark(req: BookmarkDeleteRequest, user: dict = Depends(get_current_user)):
    """Delete a bookmark"""
    async with get_db_connection() as conn:
        result = await conn.execute("""
            DELETE FROM bookmarks 
            WHERE bookmark_id = $1 AND user_id = $2
        """, req.bookmarkId, user['user_id'])
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Bookmark not found")
    
    return SuccessResponse(message="Bookmark deleted", timestamp=datetime.utcnow())


# ==================== PROFILE ROUTER ====================

profile_router = APIRouter(prefix="/users", tags=["User Profile"])

@profile_router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(user: dict = Depends(get_current_user)):
    """
    Get current user's profile
    
    Returns profileImageUrl: "/users/image/123"
    Frontend calls: GET /users/image/123 to display image
    
    
    """
    async with get_db_connection() as conn:
        # Try google_users first
        profile = await conn.fetchrow("""
            SELECT
                user_id as id,
                firstname,
                email,
                profile_image_url as "profileImageUrl",
                created_at as "createdAt",
                NULL as bio,
                NULL as "lastName",
                NULL as "dateofBirth",
                NULL as address,
                NULL as "phoneNumber",
                NULL as gender
            FROM google_users
            WHERE user_id = $1
        """, user['user_id'])

        if not profile:
            # Try users table
            profile = await conn.fetchrow("""
                SELECT
                    user_id as id,
                    firstname,
                    email,
                    profile_image_url as "profileImageUrl",
                    bio,
                    created_at as "createdAt",
                    last_name as "lastName",
                    date_of_birth as "dateofBirth",
                    address,
                    phone_number as "phoneNumber",
                    gender
                FROM users
                WHERE user_id = $1
            """, user['user_id'])

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        logger.info(f"Profile fetched for user {user['user_id']}")
        return dict(profile)


@profile_router.put("/edit-profile", response_model=EditProfileResponse)
async def edit_profile(
    file: Optional[UploadFile] = File(None),
    firstname: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    dateofBirth: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """
    
    
    All fields are optional - send only what you want to update
    """
    try:
        # Parse dateofBirth if provided
        parsed_dateofBirth = None
        if dateofBirth:
            try:
                parsed_dateofBirth = datetime.strptime(dateofBirth, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        async with get_db_connection() as conn:
            # Check if user is Google user
            is_google = await conn.fetchval(
                "SELECT 1 FROM google_users WHERE user_id = $1", 
                user['user_id']
            )

            updates = []
            values = []
            updated_fields = []

            # ==================== HANDLE IMAGE UPLOAD ====================
            if file and file.filename:
                # Validate file type
                allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg", "image/avif"]
                if file.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid file type. Only JPG, PNG, WebP, and AVIF are allowed."
                    )

                # Validate file size
                MAX_SIZE = 5 * 1024 * 1024  # 5MB
                image_data = await file.read()

                if len(image_data) > MAX_SIZE:
                    raise HTTPException(status_code=400, detail="Image too large (max 5MB)")

                logger.info(f"📸 Uploading image: {len(image_data)} bytes, type: {file.content_type}")

                # Generate unique filename
                file_ext = file.filename.split('.')[-1].lower()
                unique_filename = f"{user['user_id']}/{uuid.uuid4()}.{file_ext}"

                # Get old image URL to delete
                old_image_url = await conn.fetchval(
                    f"SELECT profile_image_url FROM {'google_users' if is_google else 'users'} WHERE user_id = $1",
                    user['user_id']
                )

                # Delete old image from Supabase Storage if exists
                if old_image_url and SUPABASE_STORAGE_BUCKET in old_image_url:
                    try:
                        old_path = old_image_url.split(f'{SUPABASE_STORAGE_BUCKET}/')[-1]
                        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([old_path])
                        logger.info(f"🗑️ Deleted old image: {old_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to delete old image: {str(e)}")

                # Upload to Supabase Storage
                try:
                    supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
                        path=unique_filename,
                        file=image_data,
                        file_options={
                            "content-type": file.content_type,
                            "cache-control": "3600",
                            "upsert": "true"
                        }
                    )
                    logger.info(f"✅ Uploaded to Supabase: {unique_filename}")
                except Exception as e:
                    logger.error(f"❌ Supabase upload failed: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload to Supabase Storage: {str(e)}"
                    )

                # Get public URL
                public_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(unique_filename)

                # Add to update query
                updates.append(f"profile_image_url = ${len(values) + 1}")
                values.append(public_url)
                updated_fields.append("profileImage")

                logger.info(f"🔗 New image URL: {public_url}")

            # ==================== HANDLE TEXT FIELDS ====================
            if is_google:
                # Google users: email, firstname only
                if email:
                    existing = await conn.fetchrow(
                        "SELECT user_id FROM google_users WHERE email = $1 AND user_id != $2",
                        email, user['user_id']
                    )
                    if existing:
                        raise HTTPException(status_code=400, detail="Email already in use")
                    updates.append(f"email = ${len(values) + 1}")
                    values.append(email)
                    updated_fields.append("email")

                if firstname:
                    updates.append(f"firstname = ${len(values) + 1}")

                    
                    values.append(firstname)
                    updated_fields.append("firstname")

                if not updates:
                    raise HTTPException(status_code=400, detail="No fields to update")

                values.append(user['user_id'])
                query = f"UPDATE google_users SET {', '.join(updates)} WHERE user_id = ${len(values)}"
                await conn.execute(query, *values)

            else:
                # Regular users: all fields
                if email:
                    existing = await conn.fetchrow(
                        "SELECT user_id FROM users WHERE email = $1 AND user_id != $2",
                        email, user['user_id']
                    )
                    if existing:
                        raise HTTPException(status_code=400, detail="Email already in use")
                    updates.append(f"email = ${len(values) + 1}")
                    values.append(email)
                    updated_fields.append("email")

                if firstname:
                    updates.append(f"firstname = ${len(values) + 1}")
                    values.append(firstname)
                    updated_fields.append("firstname")

                if lastName is not None:
                    updates.append(f"last_name = ${len(values) + 1}")
                    values.append(lastName)
                    updated_fields.append("lastName")

                if phoneNumber:
                    updates.append(f"phone_number = ${len(values) + 1}")
                    values.append(phoneNumber)
                    updated_fields.append("phoneNumber")

                if parsed_dateofBirth:
                    updates.append(f"date_of_birth = ${len(values) + 1}")
                    values.append(parsed_dateofBirth)
                    updated_fields.append("dateofBirth")

                if gender:
                    updates.append(f"gender = ${len(values) + 1}")
                    values.append(gender)
                    updated_fields.append("gender")

                if bio is not None:
                    updates.append(f"bio = ${len(values) + 1}")
                    values.append(bio)
                    updated_fields.append("bio")

                if address is not None:
                    updates.append(f"address = ${len(values) + 1}")
                    values.append(address)
                    updated_fields.append("address")

                if not updates:
                    raise HTTPException(status_code=400, detail="No fields to update")

                updates.append("updated_at = NOW()")
                values.append(user['user_id'])
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ${len(values)}"
                await conn.execute(query, *values)

        logger.info(f"✅ Profile updated for user {user['user_id']}: {updated_fields}")
        
        return EditProfileResponse(
            message="Profile updated successfully",
            updatedFields=updated_fields,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Edit profile error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")
    


# ==================== IMAGE ENDPOINTS ====================

@profile_router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_profile_image(
    file: UploadFile = File(...), 
    user: dict = Depends(get_current_user)
):
    """
        ✅ Upload profile image to Supabase Storage
        
        Flow:
        1. Validate file type & size
        2. Upload to Supabase Storage bucket
        3. Get public CDN URL
        4. Save URL in database (not image data!)
        5. Return URL to frontend
    """
    try:
        # 1. Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg", "image/avif"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPG, PNG, WebP, and AVIF are allowed."
            )

        # 2. Read and validate file size
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        image_data = await file.read()

        if len(image_data) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="Image too large (max 5MB)")

        logger.info(f"File size: {len(image_data)} bytes, content-type: {file.content_type}")

        # 3. Generate unique filename
        file_ext = file.filename.split('.')[-1].lower()
        unique_filename = f"{user['user_id']}/{uuid.uuid4()}.{file_ext}"

        logger.info(f"Uploading to Supabase: {unique_filename}")
        
        async with get_db_connection() as conn:
            # 4. Check if user is Google user
            is_google = await conn.fetchval(
                "SELECT 1 FROM google_users WHERE user_id = $1", 
                user['user_id']
            )
            
            # 5. Get old image URL to delete
            old_image_url = await conn.fetchval(
                f"SELECT profile_image_url FROM {'google_users' if is_google else 'users'} WHERE user_id = $1",
                user['user_id']
            )
            
            # 6. Delete old image from Supabase Storage if exists
            if old_image_url and SUPABASE_STORAGE_BUCKET in old_image_url:
                try:
                    # Extract path from URL
                    # Format: https://...supabase.co/storage/v1/object/public/profile-images/user_id/uuid.ext
                    old_path = old_image_url.split(f'{SUPABASE_STORAGE_BUCKET}/')[-1]
                    
                    supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([old_path])
                    logger.info(f"🗑️ Deleted old image: {old_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete old image: {str(e)}")
            
            # 7. Upload to Supabase Storage
            try:
                response = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
                    path=unique_filename,
                    file=image_data,
                    file_options={
                        "content-type": file.content_type,
                        "cache-control": "3600",
                        "upsert": "true"  # Replace if exists
                    }
                )
                logger.info(f"Uploaded to Supabase: {unique_filename}")
            except Exception as e:
                logger.error(f"Supabase upload failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload to Supabase Storage: {str(e)}"
                )

            # 8. Get public URL
            public_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(unique_filename)

            logger.info(f"Public URL: {public_url}")

            # 9. Save URL in database (not image data!)
            if is_google:
                await conn.execute(
                    "UPDATE google_users SET profile_image_url = $1 WHERE user_id = $2",
                    public_url, user['user_id']
                )
            else:
                await conn.execute(
                    "UPDATE users SET profile_image_url = $1, updated_at = NOW() WHERE user_id = $2",
                    public_url, user['user_id']
                )

            logger.info(f"Database updated with URL for user {user['user_id']}")
        
        return ImageUploadResponse(
            message="Profile image uploaded successfully",
            status="success",
            profileImageUrl=public_url,  # Return full CDN URL
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@profile_router.get("/image/{user_id}")
async def get_profile_image_redirect(user_id: str):
    """
    Get user's profile image URL (redirects to Supabase CDN)
    
    This is a helper endpoint - in production, frontend should use
    the profileImageUrl directly from GET /users/me
    """
    try:
        async with get_db_connection() as conn:
            # Check Google users first
            image_url = await conn.fetchval(
                "SELECT profile_image_url FROM google_users WHERE user_id = $1",
                user_id
            )
            
            if not image_url:
                # Check regular users
                image_url = await conn.fetchval(
                    "SELECT profile_image_url FROM users WHERE user_id = $1",
                    user_id
                )
            
            if not image_url:
                raise HTTPException(status_code=404, detail="No profile image found")
            
            # Return JSON with URL (or redirect)
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=image_url)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching image URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch image")


@profile_router.delete("/delete-image", response_model=SuccessResponse)
async def delete_profile_image(user: dict = Depends(get_current_user)):
    """
    ✅ Delete profile image from Supabase Storage
    """
    try:
        async with get_db_connection() as conn:
            is_google = await conn.fetchval(
                "SELECT 1 FROM google_users WHERE user_id = $1", 
                user['user_id']
            )
            
            # Get current image URL
            image_url = await conn.fetchval(
                f"SELECT profile_image_url FROM {'google_users' if is_google else 'users'} WHERE user_id = $1",
                user['user_id']
            )
            
            if not image_url:
                raise HTTPException(status_code=404, detail="No profile image to delete")
            
            # Extract path from Supabase URL
            if SUPABASE_STORAGE_BUCKET in image_url:
                try:
                    image_path = image_url.split(f'{SUPABASE_STORAGE_BUCKET}/')[-1]
                    logger.info(f"Deleting from Supabase: {image_path}")

                    # Delete from Supabase Storage
                    supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([image_path])
                    logger.info(f"Deleted from Supabase: {image_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete from Supabase: {str(e)}")
            
            # Clear from database
            if is_google:
                await conn.execute(
                    "UPDATE google_users SET profile_image_url = NULL WHERE user_id = $1",
                    user['user_id']
                )
            else:
                await conn.execute(
                    "UPDATE users SET profile_image_url = NULL, updated_at = NOW() WHERE user_id = $1",
                    user['user_id']
                )
            
            logger.info(f"✅ Profile image deleted for user {user['user_id']}")
            
            return SuccessResponse(
                message="Profile image deleted successfully",
                timestamp=datetime.utcnow()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete image")

# ==================== FEEDBACK ROUTER ====================

feedback_router = APIRouter(prefix="/feedback", tags=["Feedback"])

@feedback_router.post("", response_model=FeedbackResponse)
async def submit_feedback(req: FeedbackCreate, user: dict = Depends(get_current_user)):
    """Submit user feedback"""
    feedback_id = generate_feedback_id()
    created_time = datetime.utcnow()
    
    async with get_db_connection() as conn:
        await conn.execute("""
            INSERT INTO feedback (feedback_id, user_id, message, rating, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, feedback_id, user['user_id'], req.message, req.rating, created_time)
    
    return FeedbackResponse(
        id=feedback_id,
        message="Feedback submitted successfully",
        status="received",
        createdAt=created_time
    )