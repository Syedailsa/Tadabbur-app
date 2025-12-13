from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from typing import List

# Local imports (same folder mein hain)
from models import *
from utils import (
    hash_password, verify_password, create_access_token,
    verify_google_token, generate_user_id, generate_notification_id,
    generate_bookmark_id, generate_feedback_id, get_current_user
)
from database import get_db_connection

# Ensure BookmarkDeleteRequest is defined in models.py or define it here if missing
try:
    from models import BookmarkDeleteRequest
except ImportError:
    from pydantic import BaseModel
    class BookmarkDeleteRequest(BaseModel):
        bookmarkId: str

# ==================== AUTH ROUTER ====================

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/signup", response_model=AuthResponse)
async def signup(req: SignupRequest):
    """Register new user with email & password"""
    async with get_db_connection() as conn:
        # Check if user exists
        existing = await conn.fetchrow(
            "SELECT email FROM users WHERE email = $1 OR username = $2",
            req.email, req.username
        )
        
        if existing:
            raise HTTPException(status_code=400, detail="Email or username already registered")
        
        # Create user
        user_id = generate_user_id()
        pwd_hash = hash_password(req.password)
        
        await conn.execute("""
            INSERT INTO users (user_id, username, email, password_hash, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, user_id, req.username, req.email, pwd_hash)
        
        # Generate token
        token = create_access_token(user_id, req.username)
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
            username=req.username
        )

@auth_router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login with email & password"""
    async with get_db_connection() as conn:
        user = await conn.fetchrow("""
            SELECT user_id, username, password_hash 
            FROM users WHERE email = $1
        """, req.email)
        
        if not user or not verify_password(req.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate token
        token = create_access_token(user['user_id'], user['username'])
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
            username=user['username']
        )

@auth_router.post("/google-signin", response_model=AuthResponse)
async def google_signin(req: GoogleSignInRequest):
    """Sign in with Google OAuth"""
    google_data = await verify_google_token(req.token)
    
    async with get_db_connection() as conn:
        user = await conn.fetchrow("""
            SELECT user_id, username, email 
            FROM google_users WHERE google_id = $1
        """, google_data['google_id'])
        
        if not user:
            # Create new user
            user_id = generate_user_id()
            username = google_data['name'] or google_data['email'].split('@')[0]
            
            # Ensure unique username
            counter = 1
            base_username = username
            while await conn.fetchrow("SELECT 1 FROM google_users WHERE username = $1", username):
                username = f"{base_username}{counter}"
                counter += 1
            
            await conn.execute("""
                INSERT INTO google_users (user_id, google_id, email, username, profile_picture)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, google_data['google_id'], google_data['email'], 
                username, google_data.get('picture'))
            
            user = {'user_id': user_id, 'username': username, 'email': google_data['email']}
        
        token = create_access_token(user['user_id'], user['username'])
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
            username=user['username']
        )

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
    """Get all notifications for authenticated user"""
    async with get_db_connection() as conn:
        rows = await conn.fetch("""
            SELECT notification_id as id, title, message, is_read, created_at as time
            FROM notifications WHERE user_id = $1
            ORDER BY created_at DESC
        """, user['user_id'])
    
    return [dict(row) for row in rows]

# ==================== BOOKMARKS ROUTER ====================

bookmark_router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

@bookmark_router.post("", response_model=BookmarkResponse)
async def create_bookmark(req: BookmarkCreate, user: dict = Depends(get_current_user)):
    """Save bookmark for user"""
    bookmark_id = generate_bookmark_id()
    created_time = datetime.now()
    
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
                bookmark_id, user_id, item_id, type, 
                surah_name, surah_no, ayah_no, total_ayah, ayah, 
                created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, bookmark_id, user['user_id'], req.itemId, req.type,
            req.surah_name, req.surah_no, req.ayah_no, req.total_ayah, req.ayah,
            created_time)
        # Auto notification
        notif_id = generate_notification_id()
        await conn.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, notif_id, user['user_id'], "Bookmark Saved",
            f"You saved {req.surah_name}, Ayah {req.ayah_no} to your bookmarks", created_time)
    
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
                item_id as "itemId", 
                type,
                surah_name as "surahName",
                surah_no as "surahNo",
                ayah_no as "ayahNo",
                total_ayah as "totalAyah",
                ayah,
                created_at as time
            FROM bookmarks 
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, user['user_id'])
    
    return [dict(row) for row in rows]

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

@profile_router.get("/me", response_model=UserProfile)
async def get_my_profile(user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    async with get_db_connection() as conn:
        profile = await conn.fetchrow("""
             SELECT 
                user_id as id,
                username,
                email,
                profile_picture as "profilePicture",
                bio,
                created_at as "createdAt",
                last_name as "lastName",
                date_of_birth as "dateofBirth",
                address,
                phone_number as "phoneNumber"
            FROM users 
            WHERE user_id = $1
        """, user['user_id'])
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
    
    return dict(profile)

@profile_router.put("/profile", response_model=SuccessResponse)
async def update_profile(req: ProfileUpdate, user: dict = Depends(get_current_user)):
    """Update user profile"""
    updates = []
    values = []
    
    if req.username:
        updates.append(f"username = ${len(values) + 1}")
        values.append(req.username)
    if req.lastName:
        updates.append(f"lastname = ${len(values) + 1}")
        values.append(req.lastName)
    if req.address:
        updates.append(f"address = ${len(values) + 1}")
        values.append(req.address)
    if req.dateofBirth:
        updates.append(f"date_of_birth = ${len(values) + 1}")
        values.append(req.dateofBirth)
    if req.phoneNumber:
        updates.append(f"phone_number = ${len(values) + 1}")
        values.append(req.phoneNumber)
    if req.email:
        updates.append(f"email = ${len(values) + 1}")
        values.append(req.email)
    if req.profilePicture:
        updates.append(f"profile_picture = ${len(values) + 1}")
        values.append(req.profilePicture)
    if req.bio is not None:
        updates.append(f"bio = ${len(values) + 1}")
        values.append(req.bio)
    if req.gender:
        updates.append(f"gender = ${len(values) + 1}")
        values.append(req.gender)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("updated_at = NOW()")
    values.append(user['user_id'])
    
    query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ${len(values)}"
    
    async with get_db_connection() as conn:
        await conn.execute(query, *values)
    
    return SuccessResponse(message="Profile updated successfully")

# ==================== EDIT PROFILE ROUTER ====================

profile_router = APIRouter(prefix="/users", tags=["User Profile"])

@profile_router.put("/edit-profile", response_model=EditProfileResponse)
async def edit_profile(req: EditProfileRequest, user: dict = Depends(get_current_user)):
    """
    Edit Profile API - Only 6 fields can be updated:
    1. email
    2. image (profile_picture)
    3. username
    4. contact (phone_number)
    5. dateOfBirth (date_of_birth)
    6. gender
    """
    
    updates = []
    values = []
    updated_fields = []
    
    async with get_db_connection() as conn:
        
        # 1. EMAIL
        if req.email:
            # Check duplicate email
            existing = await conn.fetchrow(
                "SELECT user_id FROM users WHERE email = $1 AND user_id != $2",
                req.email, user['user_id']
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            
            updates.append(f"email = ${len(values) + 1}")
            values.append(req.email)
            updated_fields.append("email")
        
        # 2. USERNAME
        if req.username:
            # Check duplicate username
            existing = await conn.fetchrow(
                "SELECT user_id FROM users WHERE username = $1 AND user_id != $2",
                req.username, user['user_id']
            )
            if existing:
                raise HTTPException(status_code=400, detail="Username already taken")
            
            updates.append(f"username = ${len(values) + 1}")
            values.append(req.username)
            updated_fields.append("username")
        
        # 3. IMAGE (Profile Picture)
        if req.image:
            updates.append(f"profile_picture = ${len(values) + 1}")
            values.append(req.image)
            updated_fields.append("image")
        
        # 4. CONTACT (Phone Number)
        if req.contact:
            updates.append(f"phone_number = ${len(values) + 1}")
            values.append(req.contact)
            updated_fields.append("contact")
        
        # 5. DATE OF BIRTH
        if req.dateOfBirth:
            updates.append(f"date_of_birth = ${len(values) + 1}")
            values.append(req.dateOfBirth)
            updated_fields.append("dateOfBirth")
        
        # 6. GENDER
        if req.gender:
            updates.append(f"gender = ${len(values) + 1}")
            values.append(req.gender)
            updated_fields.append("gender")
        
        # Check if at least one field to update
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at timestamp
        updates.append("updated_at = NOW()")
        values.append(user['user_id'])
        
        # Build and execute UPDATE query
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ${len(values)}"
        
        await conn.execute(query, *values)
    
    return EditProfileResponse(
        message="Profile updated successfully",
        updatedFields=updated_fields,
        timestamp=datetime.utcnow()
    )

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