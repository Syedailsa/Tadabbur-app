# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, EmailStr
# from datetime import datetime, timedelta
# import secrets

# from database import get_db_connection
# from utils import hash_password, generate_notification_id

# # ==================== MODELS ====================

# class ForgotPasswordRequest(BaseModel):
#     email: EmailStr

# class VerifyOTPRequest(BaseModel):
#     email: EmailStr
#     otp: str

# class ChangePasswordRequest(BaseModel):
#     email: EmailStr
#     otp: str
#     new_password: str

# class PasswordResetResponse(BaseModel):
#     message: str
#     status: str = "success"

# # ==================== ROUTER ====================

# password_reset_router = APIRouter(prefix="/auth", tags=["Password Reset"])

# # ==================== HELPER FUNCTIONS ====================

# def generate_otp() -> str:
#     """Generate 6-digit OTP"""
#     return str(secrets.randbelow(900000) + 100000)

# async def send_otp_email(email: str, otp: str) -> bool:
#     """Send OTP to user's email - Development Mode"""
#     print(f"\n{'='*60}")
#     print(f"🔐 PASSWORD RESET OTP")
#     print(f"📧 Email: {email}")
#     print(f"🔢 OTP Code: {otp}")
#     print(f"⏰ Valid for: 10 minutes")
#     print(f"{'='*60}\n")
#     return True

# # ==================== ENDPOINTS ====================

# # @password_reset_router.post("/forgot-password", response_model=PasswordResetResponse)
# # async def forgot_password(req: ForgotPasswordRequest):
# #     """
# #     Send OTP to email for password reset
    
# #     Body:
# #         email: user@example.com
    
# #     Response:
# #         message: OTP sent to your email
# #     """
# #     async with get_db_connection() as conn:
# #         # Check if user exists
# #         user = await conn.fetchrow("""
# #             SELECT user_id, username, email 
# #             FROM users WHERE email = $1
# #         """, req.email)
        
# #         if not user:
# #             return PasswordResetResponse(
# #                 message="If this email exists, an OTP has been sent",
# #                 status="success"
# #             )
        
# #         # Generate OTP
# #         otp = generate_otp()
# #         expires_at = datetime.utcnow() + timedelta(minutes=10)
        
# #         # Delete existing OTPs
# #         await conn.execute("""
# #             DELETE FROM password_reset_otps WHERE email = $1
# #         """, req.email)
        
# #         # Store OTP
# #         await conn.execute("""
# #             INSERT INTO password_reset_otps (email, otp, expires_at, created_at)
# #             VALUES ($1, $2, $3, NOW())
# #         """, req.email, otp, expires_at)
        
# #         # Send OTP
# #         await send_otp_email(req.email, otp)
        
# #         # Create notification
# #         notif_id = generate_notification_id()
# #         await conn.execute("""
# #             INSERT INTO notifications (notification_id, user_id, title, message, created_at)
# #             VALUES ($1, $2, $3, $4, NOW())
# #         """, notif_id, user['user_id'], 
# #             "Password Reset Requested",
# #             "An OTP has been sent to your email")
        
# #         return PasswordResetResponse(
# #             message="OTP sent to your email. Valid for 10 minutes.",
# #             status="success"
# #         )

# @password_reset_router.post("/forgot-password", response_model=PasswordResetResponse)
# async def forgot_password(req: ForgotPasswordRequest):
#     """
#     Send OTP for password reset
#     Only works for email/password accounts
#     """
#     async with get_db_connection() as conn:
#         # Check if email/password user
#         user = await conn.fetchrow("""
#             SELECT user_id, username, email 
#             FROM users WHERE email = $1
#         """, req.email)
        
#         # Check if Google user
#         google_user = await conn.fetchrow("""
#             SELECT email FROM google_users WHERE email = $1
#         """, req.email)
        
#         # If Google user, inform them
#         if google_user and not user:
#             raise HTTPException(
#                 status_code=400,
#                 detail="This email is registered with Google. Please use 'Sign in with Google' to access your account."
#             )
        
#         if not user:
#             # Security: Don't reveal if email exists
#             return PasswordResetResponse(
#                 message="If this email exists, an OTP has been sent",
#                 status="success"
#             )
        
#         # Generate OTP
#         otp = generate_otp()
#         expires_at = datetime.utcnow() + timedelta(minutes=10)
        
#         # Delete existing OTPs
#         await conn.execute("""
#             DELETE FROM password_reset_otps WHERE email = $1
#         """, req.email)
        
#         # Store OTP
#         await conn.execute("""
#             INSERT INTO password_reset_otps (email, otp, expires_at, created_at)
#             VALUES ($1, $2, $3, NOW())
#         """, req.email, otp, expires_at)
        
#         # Send OTP
#         await send_otp_email(req.email, otp)
        
#         # Create notification
#         notif_id = generate_notification_id()
#         await conn.execute("""
#             INSERT INTO notifications (notification_id, user_id, title, message, created_at)
#             VALUES ($1, $2, $3, $4, NOW())
#         """, notif_id, user['user_id'], 
#             "Password Reset Requested",
#             "An OTP has been sent to your email")
        
#         return PasswordResetResponse(
#             message="OTP sent to your email. Valid for 10 minutes.",
#             status="success"
#         )
    
# @password_reset_router.post("/verify-otp", response_model=PasswordResetResponse)
# async def verify_otp(req: VerifyOTPRequest):
#     """
#     Verify OTP code
    
#     Body:
#         email: user@example.com
#         otp: 123456
#     """
#     async with get_db_connection() as conn:
#         otp_record = await conn.fetchrow("""
#             SELECT otp, expires_at, verified 
#             FROM password_reset_otps 
#             WHERE email = $1
#             ORDER BY created_at DESC
#             LIMIT 1
#         """, req.email)
        
#         if not otp_record:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No OTP request found. Please request a new OTP."
#             )
        
#         if otp_record['verified']:
#             raise HTTPException(
#                 status_code=400,
#                 detail="OTP already used. Please request a new one."
#             )
        
#         if datetime.utcnow() > otp_record['expires_at']:
#             raise HTTPException(
#                 status_code=400,
#                 detail="OTP expired. Please request a new one."
#             )
        
#         if otp_record['otp'] != req.otp:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid OTP. Please try again."
#             )
        
#         # Mark as verified
#         await conn.execute("""
#             UPDATE password_reset_otps 
#             SET verified = TRUE 
#             WHERE email = $1
#         """, req.email)
        
#         return PasswordResetResponse(
#             message="OTP verified successfully. You can now reset your password.",
#             status="success"
#         )


# @password_reset_router.post("/change-password", response_model=PasswordResetResponse)
# async def change_password(req: ChangePasswordRequest):
#     """
#     Change password using verified OTP
    
#     Body:
#         email: user@example.com
#         otp: 123456
#         new_password: newpassword123
#     """
#     if len(req.new_password) < 8:
#         raise HTTPException(
#             status_code=400,
#             detail="Password must be at least 8 characters long"
#         )
    
#     async with get_db_connection() as conn:
#         otp_record = await conn.fetchrow("""
#             SELECT otp, expires_at, verified 
#             FROM password_reset_otps 
#             WHERE email = $1
#             ORDER BY created_at DESC
#             LIMIT 1
#         """, req.email)
        
#         if not otp_record:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No OTP found. Please request a new one."
#             )
        
#         if not otp_record['verified']:
#             raise HTTPException(
#                 status_code=400,
#                 detail="OTP not verified. Please verify OTP first."
#             )
        
#         if datetime.utcnow() > otp_record['expires_at']:
#             raise HTTPException(
#                 status_code=400,
#                 detail="OTP expired. Please request a new one."
#             )
        
#         if otp_record['otp'] != req.otp:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid OTP."
#             )
        
#         # Get user
#         user = await conn.fetchrow("""
#             SELECT user_id, username 
#             FROM users WHERE email = $1
#         """, req.email)
        
#         if not user:
#             raise HTTPException(
#                 status_code=404,
#                 detail="User not found"
#             )
        
#         # Update password
#         new_pwd_hash = hash_password(req.new_password)
#         await conn.execute("""
#             UPDATE users 
#             SET password_hash = $1, updated_at = NOW() 
#             WHERE email = $2
#         """, new_pwd_hash, req.email)
        
#         # Delete used OTP
#         await conn.execute("""
#             DELETE FROM password_reset_otps WHERE email = $1
#         """, req.email)
        
#         # Create notification
#         notif_id = generate_notification_id()
#         await conn.execute("""
#             INSERT INTO notifications (notification_id, user_id, title, message, created_at)
#             VALUES ($1, $2, $3, $4, NOW())
#         """, notif_id, user['user_id'],
#             "Password Changed",
#             "Your password has been successfully changed")
        
#         return PasswordResetResponse(
#             message="Password changed successfully. You can now login with your new password.",
#             status="success"
#         )


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import secrets
import os

from database import get_db_connection
from utils import hash_password, generate_notification_id

# ==================== MODELS ====================

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ChangePasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str
    status: str = "success"

# ==================== ROUTER ====================

password_reset_router = APIRouter(prefix="/auth", tags=["Password Reset"])

# ==================== HELPER FUNCTIONS ====================

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(secrets.randbelow(900000) + 100000)

async def send_otp_email(email: str, otp: str, username: str = "User") -> bool:
    """
    Send OTP to user's email
    - In development: prints to console
    - In production: sends actual email via SMTP
    """
    
    # Check if in production mode
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    if SMTP_USER and SMTP_PASSWORD:
        # Production: Send actual email
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
            SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
            FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Reset OTP - Tadabbur Agent"
            message["From"] = FROM_EMAIL
            message["To"] = email
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                  <h2 style="color: #2c5282;">Password Reset Request</h2>
                  <p>Hello {username},</p>
                  <p>You requested to reset your password for Tadabbur Agent. Use the OTP below:</p>
                  <div style="background-color: #edf2f7; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #2c5282; letter-spacing: 5px; margin: 0; font-size: 36px;">{otp}</h1>
                  </div>
                  <p style="color: #e53e3e;"><strong>⏰ This OTP will expire in 10 minutes.</strong></p>
                  <p style="color: #718096;">If you didn't request this, please ignore this email and your password will remain unchanged.</p>
                  <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                  <p style="color: #718096; font-size: 12px;">Tadabbur Agent - Quranic Reflection Platform</p>
                </div>
              </body>
            </html>
            """
            
            part = MIMEText(html, "html")
            message.attach(part)
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(message)
            
            print(f"✅ Email sent to {email}")
            return True
            
        except Exception as e:
            print(f"❌ Email send failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send OTP email. Please try again later."
            )
    else:
        # Development: Print to console
        print(f"\n{'='*60}")
        print(f"🔐 PASSWORD RESET OTP (Development Mode)")
        print(f"📧 Email: {email}")
        print(f"👤 Username: {username}")
        print(f"🔢 OTP Code: {otp}")
        print(f"⏰ Valid for: 10 minutes")
        print(f"{'='*60}\n")
        return True

# ==================== ENDPOINTS ====================

@password_reset_router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(req: ForgotPasswordRequest):
    """
    Step 1: Request OTP for password reset
    
    - Only works for email/password accounts
    - Google users must use "Sign in with Google"
    - Sends 6-digit OTP valid for 10 minutes
    
    Body:
    ```json
    {
        "email": "user@example.com"
    }
    ```
    """
    async with get_db_connection() as conn:
        # Check if email/password user exists
        user = await conn.fetchrow("""
            SELECT user_id, username, email 
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
            # Security: Don't reveal if email exists
            return PasswordResetResponse(
                message="If this email is registered, an OTP has been sent",
                status="success"
            )
        
        # Generate OTP
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Delete existing OTPs for this email
        await conn.execute("""
            DELETE FROM password_reset_otps WHERE email = $1
        """, req.email)
        
        # Store new OTP
        await conn.execute("""
            INSERT INTO password_reset_otps (email, otp, expires_at, created_at)
            VALUES ($1, $2, $3, NOW())
        """, req.email, otp, expires_at)
        
        # Send OTP via email
        await send_otp_email(req.email, otp, user['username'])
        
        # Create notification
        notif_id = generate_notification_id()
        await conn.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, notif_id, user['user_id'], 
            "Password Reset Requested",
            "An OTP has been sent to your email for password reset")
        
        return PasswordResetResponse(
            message=f"OTP sent to {req.email}. Valid for 10 minutes.",
            status="success"
        )

    
@password_reset_router.post("/verify-otp", response_model=PasswordResetResponse)
async def verify_otp(req: VerifyOTPRequest):
    """
    Step 2: Verify OTP code
    
    Body:
    ```json
    {
        "email": "user@example.com",
        "otp": "123456"
    }
    ```
    """
    async with get_db_connection() as conn:
        otp_record = await conn.fetchrow("""
            SELECT otp, expires_at, verified 
            FROM password_reset_otps 
            WHERE email = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, req.email)
        
        if not otp_record:
            raise HTTPException(
                status_code=404,
                detail="No OTP request found. Please request a new OTP."
            )
        
        if otp_record['verified']:
            raise HTTPException(
                status_code=400,
                detail="OTP already used. Please request a new one."
            )
        
        if datetime.utcnow() > otp_record['expires_at']:
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request a new one."
            )
        
        if otp_record['otp'] != req.otp:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP. Please check and try again."
            )
        
        # Mark as verified
        await conn.execute("""
            UPDATE password_reset_otps 
            SET verified = TRUE 
            WHERE email = $1 AND otp = $2
        """, req.email, req.otp)
        
        return PasswordResetResponse(
            message="OTP verified successfully. You can now reset your password.",
            status="success"
        )


@password_reset_router.post("/change-password", response_model=PasswordResetResponse)
async def change_password(req: ChangePasswordRequest):
    """
    Step 3: Change password using verified OTP
    
    Body:
    ```json
    {
        "email": "user@example.com",
        "otp": "123456",
        "new_password": "NewSecurePass123!"
    }
    ```
    
    Requirements:
    - Password must be at least 8 characters
    - OTP must be verified first
    """
    # Validate password length
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )
    
    async with get_db_connection() as conn:
        # Check OTP record
        otp_record = await conn.fetchrow("""
            SELECT otp, expires_at, verified 
            FROM password_reset_otps 
            WHERE email = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, req.email)
        
        if not otp_record:
            raise HTTPException(
                status_code=404,
                detail="No OTP found. Please start the password reset process again."
            )
        
        if not otp_record['verified']:
            raise HTTPException(
                status_code=400,
                detail="OTP not verified. Please verify OTP first."
            )
        
        if datetime.utcnow() > otp_record['expires_at']:
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request a new one."
            )
        
        if otp_record['otp'] != req.otp:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP."
            )
        
        # Get user
        user = await conn.fetchrow("""
            SELECT user_id, username 
            FROM users WHERE email = $1
        """, req.email)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Hash new password
        new_pwd_hash = hash_password(req.new_password)
        
        # Update password
        await conn.execute("""
            UPDATE users 
            SET password_hash = $1, updated_at = NOW() 
            WHERE email = $2
        """, new_pwd_hash, req.email)
        
        # Delete used OTP
        await conn.execute("""
            DELETE FROM password_reset_otps WHERE email = $1
        """, req.email)
        
        # Invalidate all existing tokens for security
        await conn.execute("""
            DELETE FROM auth_tokens WHERE user_id = $1
        """, user['user_id'])
        
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


@password_reset_router.post("/resend-otp", response_model=PasswordResetResponse)
async def resend_otp(req: ForgotPasswordRequest):
    """
    Resend OTP if user didn't receive it or it expired
    
    Body:
    ```json
    {
        "email": "user@example.com"
    }
    ```
    """
    # Reuse forgot_password logic
    return await forgot_password(req)