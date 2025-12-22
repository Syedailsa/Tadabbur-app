from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import os

from database import get_db_connection
from utils import hash_password, generate_notification_id

# ==================== MODELS ====================

class ChangePasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str
    status: str = "success"

# ==================== ROUTER ====================

password_reset_router = APIRouter(prefix="/auth", tags=["Password Reset"])

# ==================== HELPER FUNCTIONS ====================

# ==================== ENDPOINTS ====================


@password_reset_router.post("/change-password", response_model=PasswordResetResponse)
async def change_password(req: ChangePasswordRequest):
    """
    Change password directly with email

    Body:
    ```json
    {
        "email": "user@example.com",
        "new_password": "NewSecurePass123!"
    }
    ```

    Requirements:
    - Password must be at least 8 characters
    - Email must be registered
    """
    # Validate password length
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )

    async with get_db_connection() as conn:
        # Check if email/password user exists
        user = await conn.fetchrow("""
            SELECT user_id, firstname, email
            FROM users WHERE email = $1
        """, req.email)
        
        # Check if Google user
        google_user = await conn.fetchrow("""
            SELECT email FROM google_users WHERE email = $1
        """, req.email)
        
        # If Google user, inform them
        if google_user and not user:
            raise HTTPException(
                status_code=400,
                detail="This email is registered with Google. Please use 'Sign in with Google' to access your account."
            )
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found with this email address"
            )

        # Hash new password
        new_pwd_hash = hash_password(req.new_password)

        # Update password
        await conn.execute("""
            UPDATE users
            SET password_hash = $1, updated_at = NOW()
            WHERE email = $2
        """, new_pwd_hash, req.email)
        
        # Invalidate all existing tokens for security
        await conn.execute("""
            DELETE FROM auth_tokens WHERE user_id = $1
        """, user['user_id'])
        
        # Delete any existing password reset OTPs
        await conn.execute("""
            DELETE FROM password_reset_otps WHERE email = $1
        """, req.email)
        
        # Create success notification
        notif_id = generate_notification_id()
        await conn.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, notif_id, user['user_id'],
            "Password Changed Successfully",
            "Your password has been changed. All sessions have been logged out for security.")
        
        return PasswordResetResponse(
            message="Password changed successfully. Please login with your new password.",
            status="success"
        )
