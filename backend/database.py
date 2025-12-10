import os
from dotenv import load_dotenv
import asyncpg
from contextlib import asynccontextmanager

# Load environment variables with absolute path
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

# Print for debugging (remove in production)
if DATABASE_URL:
    print(f"✅ DATABASE_URL loaded: {DATABASE_URL[:30]}...")
else:
    print("❌ DATABASE_URL not found!")


# Global connection pool
db_pool = None

async def init_db_pool():
    """
    Initialize database connection pool
    Yeh function main.py mein startup pe call hoga
    """
    global db_pool
    
    if not DATABASE_URL:
        print("⚠️ WARNING: DATABASE_URL not found in .env file!")
        print("PostgreSQL features will be disabled.")
        return
    print(f"Attempting to connect to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split(':')[-1], '****')}")  # Debug

    
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        print("✅ SUPABASE CONNECTED SUCCESSFULLY!" )
        
        # Create tables automatically
        await create_tables()
        
    except Exception as e:
        print(f"❌❌ FAILED TO CONNECT SUPABASE: {e}")
        print("Check your DATABASE_URL and internet connection")
        db_pool = None

async def close_db_pool():
    """Close database pool on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
        print("❌ Database pool closed")

@asynccontextmanager
async def get_db_connection():
    """
    Get database connection from pool
    Usage:
        async with get_db_connection() as conn:
            result = await conn.fetch("SELECT * FROM users")
    """
    if not db_pool:
        raise Exception("Database pool not initialized. Call init_db_pool() first.")
    
    async with db_pool.acquire() as conn:
        yield conn

async def create_tables():
    """Create all required tables if they don't exist"""
    if not db_pool:
        return
    
    async with get_db_connection() as conn:
        # USERS TABLE (Email/Password authentication)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                profile_picture TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # GOOGLE USERS TABLE (OAuth authentication)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS google_users (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                username TEXT,
                profile_picture TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # AUTH TOKENS TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL
            )
        """)
        
        # NOTIFICATIONS TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                notification_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create index for faster queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user 
            ON notifications(user_id, created_at DESC)
        """)
        
        # BOOKMARKS TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id SERIAL PRIMARY KEY,
                bookmark_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, item_id)
            )
        """)
        
        # Create index
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookmarks_user 
            ON bookmarks(user_id, created_at DESC)
        """)
        
        # FEEDBACK TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                feedback_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                rating TEXT CHECK(rating IN ('like', 'dislike')),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # CONTENT FEEDBACK TABLE 
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS content_feedback (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                item_index INTEGER NOT NULL,
                feedback_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(session_id, item_index, feedback_type)
            )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_otps (
        id SERIAL PRIMARY KEY,
        email TEXT NOT NULL,
        otp TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

        # Create index for faster queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_otp_email 
            ON password_reset_otps(email, created_at DESC)
        """)

        # RECENT REFLECTIONS TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS recent_reflections (
                id SERIAL PRIMARY KEY,
                reflection_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                surah_name_eng TEXT NOT NULL,
                surah_name_arabic TEXT NOT NULL,
                surah_no INTEGER NOT NULL,
                total_ayah INTEGER NOT NULL,
                last_ayah_read INTEGER,
                last_read_at TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id)
            )
        """)

        # Create index
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reflection_user 
            ON recent_reflections(user_id)
        """)

        print("✅ All PostgreSQL tables created/verified (including new tables)")
                
        print("✅ All PostgreSQL tables created/verified")

# Helper functions for quick queries
async def execute_query(query: str, *args):
    """Execute SELECT query and return all results"""
    async with get_db_connection() as conn:
        return await conn.fetch(query, *args)

async def execute_one(query: str, *args):
    """Execute SELECT query and return single row"""
    async with get_db_connection() as conn:
        return await conn.fetchrow(query, *args)

async def execute_write(query: str, *args):
    """Execute INSERT/UPDATE/DELETE query"""
    async with get_db_connection() as conn:
        return await conn.execute(query, *args)