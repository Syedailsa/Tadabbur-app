

# import os
# import secrets
# import hashlib
# import jwt
# from datetime import datetime, timedelta
# from fastapi import HTTPException, Header
# from typing import Optional
# from google.oauth2 import id_token
# from google.auth.transport import requests

# SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
# ALGORITHM = "HS256"
# TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

# # GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# # ==================== PASSWORD HASHING ====================

# def hash_password(password: str) -> str:
#     """Hash password using SHA-256 with salt"""
#     salt = secrets.token_hex(16)
#     pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
#     return f"{salt}${pwd_hash}"

# def verify_password(password: str, hashed: str) -> bool:
#     """Verify password against hash"""
#     try:
#         salt, pwd_hash = hashed.split('$')
#         return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
#     except:
#         return False

# # ==================== JWT TOKEN MANAGEMENT ====================

# def create_access_token(user_id: str, username: str) -> str:
#     """Create JWT access token"""
#     expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
#     payload = {
#         "user_id": user_id,
#         "username": username,
#         "exp": expire,
#         "iat": datetime.utcnow()
#     }
#     return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# def decode_token(token: str) -> dict:
#     """Decode and verify JWT token"""
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# # ==================== GOOGLE OAUTH ====================

# async def verify_google_token(token: str) -> dict:
#     """
#     Verify Google OAuth token and extract user info
    
#     Returns:
#         {
#             'google_id': '...',
#             'email': '...',
#             'name': '...',
#             'picture': '...'
#         }
#     """
#     try:
#         # Verify the token with Google
#         idinfo = id_token.verify_oauth2_token(
#             token, 
#             requests.Request(), 
#             GOOGLE_CLIENT_ID
#         )
        
#         # Token is valid, extract user info
#         return {
#             'google_id': idinfo['sub'],
#             'email': idinfo['email'],
#             'name': idinfo.get('name', ''),
#             'picture': idinfo.get('picture', '')
#         }
#     except ValueError:
#         raise HTTPException(status_code=401, detail="Invalid Google token")

# # ==================== AUTH DEPENDENCY ====================

# async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
#     """
#     FastAPI dependency to get current authenticated user
    
#     Usage in endpoint:
#         @app.get("/protected")
#         async def protected_route(user: dict = Depends(get_current_user)):
#             return {"user_id": user["user_id"]}
#     """
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header missing")
    
#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Invalid authorization format")
    
#     token = authorization.replace("Bearer ", "")
#     payload = decode_token(token)
    
#     return payload  # Returns {'user_id': '...', 'username': '...'}

# # ==================== HELPER FUNCTIONS ====================

# def generate_user_id() -> str:
#     """Generate unique user ID"""
#     return f"user_{secrets.token_hex(8)}"

# def generate_notification_id() -> str:
#     """Generate unique notification ID"""
#     return f"notif_{secrets.token_hex(8)}"

# def generate_bookmark_id() -> str:
#     """Generate unique bookmark ID"""
#     return f"bm_{secrets.token_hex(8)}"

# def generate_feedback_id() -> str:
#     """Generate unique feedback ID"""
#     return f"fb_{secrets.token_hex(8)}"





import os
import secrets
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  

# ==================== PASSWORD HASHING ====================

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

def create_access_token(user_id: str, username: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "username": username,
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

# ==================== GOOGLE SIGN-IN (TEMP MOCK) ====================

# async def verify_google_token(token: str) -> dict:
#     """
#     TEMP MOCK VERSION — because Sir only wants endpoints,
#     not actual Google Cloud OAuth integration.

#     Always returns fake user info so API testing works.
#     """
#     if not token:
#         raise HTTPException(status_code=400, detail="Google token missing")

#     # Return mock user data for testing
     
#     fake_names = ["Ayesha Khan", "Fatima Ahmed", "Zainab Ali", "Maryam Hussain", "Hafsa Siddiqui"]
#     fake_emails = ["ayesha@gmail.com", "fatima@yahoo.com", "zainab@outlook.com", "maryam123@gmail.com"]

#     return {
#         "google_id": f"mock_google_{secrets.token_hex(8)}",
#         "email": secrets.choice(fake_emails),
#         "name": secrets.choice(fake_names),
#         "picture": "https://ui-avatars.com/api/?name=" + secrets.choice(fake_names).replace(" ", "+") + "&background=random"
#     }

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

# ==================== AUTH DEPENDENCY ====================

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    return payload

# ==================== HELPER FUNCTIONS ====================

def generate_user_id() -> str:
    return f"user_{secrets.token_hex(8)}"

def generate_notification_id() -> str:
    return f"notif_{secrets.token_hex(8)}"

def generate_bookmark_id() -> str:
    return f"bm_{secrets.token_hex(8)}"

def generate_feedback_id() -> str:
    return f"fb_{secrets.token_hex(8)}"
