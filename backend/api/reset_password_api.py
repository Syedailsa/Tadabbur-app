from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import os

from data.database import get_db_connection
from utils.authentication import hash_password, generate_notification_id, send_otp_email
import random

# ==================== MODELS ====================

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResendOTPRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str
    status: str = "success"

# ==================== ROUTER ====================

password_reset_router = APIRouter(prefix="/auth", tags=["Password Reset"])

# ==================== HELPER FUNCTIONS ====================

def generate_4digit_otp() -> str:
    """Generate 4-digit OTP"""
    return str(random.randint(1000, 9999))

async def save_otp_to_db(email: str, otp: str):
    """Save OTP to database with 10 minute expiry"""
    async with get_db_connection() as conn:
        # Delete any existing OTPs for this email
        
        await conn.execute("""
            DELETE FROM password_reset_otps WHERE email = $1
        """, email)
        
        # Insert new OTP with 10 minute expiry
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        await conn.execute("""
            INSERT INTO password_reset_otps (email, otp, expires_at, created_at, verified)
            VALUES ($1, $2, $3, NOW(), FALSE)
        """, email, otp, expires_at)

async def verify_otp_from_db(email: str, otp: str):
    """Verify OTP from database and check expiry"""
    async with get_db_connection() as conn:
        result = await conn.fetchrow("""
            SELECT otp, expires_at FROM password_reset_otps 
            WHERE email = $1 AND otp = $2
        """, email, otp)
        
        if not result:
            return False
        
        # Check if OTP is expired
        if datetime.utcnow() > result['expires_at']:
            # Delete expired OTP
            await conn.execute("""
                DELETE FROM password_reset_otps WHERE email = $1
            """, email)
            return False
        
        return True

# ==================== ENDPOINTS ====================

@password_reset_router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(req: ForgotPasswordRequest):
    """
    Send OTP to email for password reset
    
    Body:
    ```json
    {
        "email": "user@example.com"
    }
    ```
    
    - Generates 4-digit OTP
    - OTP expires in 10 minutes
    - Sends OTP to user's email
    """
    async with get_db_connection() as conn:
        # Check if email exists in users table
        user = await conn.fetchrow("""
            SELECT user_id, firstname, email
            FROM users WHERE email = $1
        """, req.email)
        
        # Check if it's a Google user
        google_user = await conn.fetchrow("""
            SELECT email FROM google_users WHERE email = $1
        """, req.email)
        
        if google_user and not user:
            raise HTTPException(
                status_code=400,
                detail="This email is registered with Google. Please use 'Sign in with Google' to access your account."
            )
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="No account found with this email address"
            )
        
        # Generate 4-digit OTP
        otp = generate_4digit_otp()
        
        # Save OTP to database
        await save_otp_to_db(req.email, otp)
        
        # Send OTP via email
        await send_otp_email(req.email, otp, user['firstname'])
        
        return PasswordResetResponse(
            message=f"OTP has been sent to {req.email}. Please check your email.",
            status="success"
        )


@password_reset_router.post("/verify-otp", response_model=PasswordResetResponse)
async def verify_otp(req: VerifyOTPRequest):
    """
    Verify OTP sent to email
    
    Body:
    ```json
    {
        "email": "user@example.com",
        "otp": "1234"
    }
    ```
    
    - Verifies 4-digit OTP
    - Checks if OTP is expired (10 minutes)
    """
    # Verify OTP from database
    is_valid = await verify_otp_from_db(req.email, req.otp)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP. Please request a new one."
        )
    
    async with get_db_connection() as conn:
        await conn.execute("""
            UPDATE password_reset_otps 
            SET verified = TRUE 
            WHERE email = $1 AND otp = $2
        """, req.email, req.otp)
    
    return PasswordResetResponse(
        message="OTP verified successfully. You can now change your password.",
        status="success"
    )


@password_reset_router.post("/resend-otp", response_model=PasswordResetResponse)
async def resend_otp(req: ResendOTPRequest):
    """
    Resend OTP to email
    
    Body:
    ```json
    {
        "email": "user@example.com"
    }
    ```
    
    - Generates new 4-digit OTP
    - Invalidates previous OTP
    - Sends new OTP to email
    """
    async with get_db_connection() as conn:
        # Check if email exists
        user = await conn.fetchrow("""
            SELECT user_id, firstname, email
            FROM users WHERE email = $1
        """, req.email)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="No account found with this email address"
            )
        
        # Generate new 4-digit OTP
        otp = generate_4digit_otp()
        
        # Save new OTP to database (this will delete old one)
        await save_otp_to_db(req.email, otp)
        
        # Send OTP via email
        await send_otp_email(req.email, otp, user['firstname'])
        
        return PasswordResetResponse(
            message=f"New OTP has been sent to {req.email}",
            status="success"
        )


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

        # Security Check - Must verify OTP was validated first
        otp_record = await conn.fetchrow("""
            SELECT verified FROM password_reset_otps 
            WHERE email = $1 AND verified = TRUE
        """, req.email)

        if not otp_record:
            raise HTTPException(status_code=401, detail="Unauthorized: Please verify OTP first before changing password.")
        
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