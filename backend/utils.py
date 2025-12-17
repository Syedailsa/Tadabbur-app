import os
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  

# ========= PASSWORD HASHING ==========

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        salt, pwd_hash = hashed.split('$')
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except:
        return False

# ==================== JWT TOKEN MANAGEMENT ====================

def create_access_token(user_id: str, firstname: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "firstname": firstname,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== GOOGLE OAUTH ====================

async def verify_google_token(token: str) -> dict:
    """
    REAL Google OAuth2 Token Verification
    Uses Google's official library – 100% secure & production ready
    """
    if not token:
        raise HTTPException(status_code=400, detail="Google token is required")

    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Server error: GOOGLE_CLIENT_ID not configured")

    try:
        # Verify token with Google
        claim = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience=GOOGLE_CLIENT_ID
        )

        # Extra security checks 
        if claim['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError("Invalid token issuer")
        
        if claim.get('email_verified') is not True:
            raise HTTPException(status_code=401, detail="Please verify your email with Google")

        return {
            "google_id": claim['sub'],
            "email": claim['email'],
            "name": claim.get('name'),
            "given_name": claim.get('given_name'),
            "family_name": claim.get('family_name'),
            "picture": claim.get('picture'),
            "email_verified": claim.get('email_verified', False),
        }

    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Google authentication failed. Please try again.")

# ==================== OTP FUNCTIONS ====================

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

async def send_otp_email(email: str, otp: str, username: str = "User"):
    """
    Send OTP via email using SMTP
    Configure SMTP settings in .env file
    """
    # Email configuration from environment
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
    
    if not SMTP_USER or not SMTP_PASSWORD:
        # Development mode - print to console
        print(f"\n{'='*60}")
        print(f"🔐 PASSWORD RESET OTP (Development Mode)")
        print(f"📧 Email: {email}")
        print(f"👤 Username: {username}")
        print(f"🔢 OTP Code: {otp}")
        print(f"⏰ Valid for: 10 minutes")
        print(f"{'='*60}\n")
        return True
    
    # Create email
    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset OTP - Tadabbur Agent"
    message["From"] = FROM_EMAIL
    message["To"] = email
    
    # HTML email template
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
          <h2 style="color: #2c5282;">Password Reset Request</h2>
          <p>Hello {username},</p>
          <p>You requested to reset your password for Tadabbur Agent. Use the OTP below:</p>
          <div style="background-color: #edf2f7; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
            <h1 style="color: #2c5282; letter-spacing: 5px; margin: 0;">{otp}</h1>
          </div>
          <p style="color: #e53e3e;"><strong>This OTP will expire in 10 minutes.</strong></p>
          <p>If you didn't request this, please ignore this email.</p>
          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
          <p style="color: #718096; font-size: 12px;">Tadabbur Agent - Quranic Reflection Platform</p>
        </div>
      </body>
    </html>
    """
    
    part = MIMEText(html, "html")
    message.attach(part)
    
    # Send email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
        print(f"✅ Email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Email send failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP email. Please try again later."
        )

# ==================== ID GENERATORS ====================

def generate_user_id() -> str:
    return f"user_{secrets.token_hex(8)}"

def generate_notification_id() -> str:
    return f"notif_{secrets.token_hex(8)}"

def generate_bookmark_id() -> str:
    return f"bookmark_{secrets.token_hex(8)}"

def generate_feedback_id() -> str:
    return f"feedback_{secrets.token_hex(8)}"

# ==================== AUTH DEPENDENCY ====================

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify JWT token from Authorization header
    Returns user data if valid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    return payload

# ========== HELPER FUNCTIONS ============

def generate_user_id() -> str:
    return f"user_{secrets.token_hex(8)}"

def generate_notification_id() -> str:
    return f"notif_{secrets.token_hex(8)}"

def generate_bookmark_id() -> str:
    return f"bm_{secrets.token_hex(8)}"

def generate_feedback_id() -> str:
    return f"fb_{secrets.token_hex(8)}"
