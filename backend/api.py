from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from models import BookmarkDeleteRequest
from typing import List

# Local imports
from models import *
from utils import (
    hash_password, verify_password, create_access_token,
    verify_google_token, generate_user_id, generate_notification_id,
    generate_bookmark_id, generate_feedback_id, get_current_user
)
from database import get_db_connection

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
        user_id = generate_user_id()
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
            user_id = generate_user_id()
            username = google_data['name'] or google_data['email'].split('@')[0]
            
            # Ensure unique firstname
            counter = 1
            base_username = username
            while await conn.fetchrow("SELECT 1 FROM google_users WHERE firstname = $1", username):
                username = f"{base_username}{counter}"
                counter += 1
            
            await conn.execute("""
                INSERT INTO google_users (user_id, google_id, email, firstname, profile_picture)
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
            SELECT notification_id as id, title, message, COALESCE(is_read, FALSE) as is_read, created_at as time
            FROM notifications WHERE user_id = $1
            ORDER BY created_at DESC
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

@profile_router.get("/me", response_model=UserProfile)
async def get_my_profile(user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    async with get_db_connection() as conn:
        # Try google_users first
        profile = await conn.fetchrow("""
             SELECT
                user_id as id,
                firstname,
                email,
                profile_picture as "image",
                NULL as bio,
                created_at as "createdAt",
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
                    profile_picture as "image",
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

    print("Profile", profile)
    return dict(profile)


@profile_router.put("/edit-profile", response_model=EditProfileResponse)
async def edit_profile(req: EditProfileRequest, user: dict = Depends(get_current_user)):
    """
    Edit Profile API - Fields that can be updated:
    For regular users: email, image, firstname, last_name, contact, dateOfBirth, gender, bio, address
    For Google users: email, image, firstname
    """

    async with get_db_connection() as conn:
        # Check if user is Google user
        google_user = await conn.fetchrow("SELECT user_id FROM google_users WHERE user_id = $1", user['user_id'])
        is_google = google_user is not None

        updates = []
        values = []
        updated_fields = []

        if is_google:
            # For Google users, only process email, firstname, image (ignore others)

            # 1. EMAIL
            if req.email:
                existing = await conn.fetchrow(
                    "SELECT user_id FROM google_users WHERE email = $1 AND user_id != $2",
                    req.email, user['user_id']
                )
                if existing:
                    raise HTTPException(status_code=400, detail="Email already in use")

                updates.append(f"email = ${len(values) + 1}")
                values.append(req.email)
                updated_fields.append("email")

            # 2. FIRSTNAME
            if req.firstname:
                existing = await conn.fetchrow(
                    "SELECT user_id FROM google_users WHERE firstname = $1 AND user_id != $2",
                    req.firstname, user['user_id']
                )
                if existing:
                    raise HTTPException(status_code=400, detail="Firstname already taken")

                updates.append(f"firstname = ${len(values) + 1}")
                values.append(req.firstname)
                updated_fields.append("firstname")

            # 3. IMAGE
            if req.image:
                updates.append(f"profile_picture = ${len(values) + 1}")
                values.append(req.image)
                updated_fields.append("image")

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            values.append(user['user_id'])
            query = f"UPDATE google_users SET {', '.join(updates)} WHERE user_id = ${len(values)}"
            await conn.execute(query, *values)

        else:
            # For regular users
            # 1. EMAIL
            if req.email:
                existing = await conn.fetchrow(
                    "SELECT user_id FROM users WHERE email = $1 AND user_id != $2",
                    req.email, user['user_id']
                )
                if existing:
                    raise HTTPException(status_code=400, detail="Email already in use")

                updates.append(f"email = ${len(values) + 1}")
                values.append(req.email)
                updated_fields.append("email")

            # 2. FIRSTNAME
            if req.firstname:
                existing = await conn.fetchrow(
                    "SELECT user_id FROM users WHERE firstname = $1 AND user_id != $2",
                    req.firstname, user['user_id']
                )
                if existing:
                    raise HTTPException(status_code=400, detail="Firstname already taken")

                updates.append(f"firstname = ${len(values) + 1}")
                values.append(req.firstname)
                updated_fields.append("firstname")

            # 2. lastname
            if req.last_name:
                updates.append(f"last_name = ${len(values) + 1}")
                values.append(req.last_name)
                updated_fields.append("last_name")

            # 3. IMAGE
            if req.image:
                updates.append(f"profile_picture = ${len(values) + 1}")
                values.append(req.image)
                updated_fields.append("image")

            # 4. CONTACT
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

            # 7. BIO
            if req.bio is not None:
                updates.append(f"bio = ${len(values) + 1}")
                values.append(req.bio)
                updated_fields.append("bio")

            # 8. LAST NAME
            if req.last_name is not None:
                updates.append(f"last_name = ${len(values) + 1}")
                values.append(req.last_name)
                updated_fields.append("last_name")

            # 9. ADDRESS
            if req.address is not None:
                updates.append(f"address = ${len(values) + 1}")
                values.append(req.address)
                updated_fields.append("address")

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            updates.append("updated_at = NOW()")
            values.append(user['user_id'])
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