import os
import logging
from dotenv import load_dotenv
import asyncpg
from contextlib import asynccontextmanager
from config.db import get_supabase_client

logger = logging.getLogger(__name__)

# Load environment variables with absolute path
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

# Print for debugging (remove in production)
if DATABASE_URL:
    print(f"DATABASE_URL loaded: {DATABASE_URL[:30]}...")
else:
    print("DATABASE_URL not found!")


# Global connection pool
db_pool = None

async def init_db_pool():
    """
    Initialize database connection pool
    Yeh function main.py mein startup pe call hoga
    """
    global db_pool
    
    if not DATABASE_URL:
        print("WARNING: DATABASE_URL not found in .env file!")
        print("PostgreSQL features will be disabled.")
        return
    print(f"Attempting to connect to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split(':')[-1], '****')}")  # Debug

    
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60,
            statement_cache_size=0
        )
        print("✅ SUPABASE CONNECTED SUCCESSFULLY!" )
        
        # Create tables automatically
        await create_tables()
        
    except Exception as e:
        print(f"FAILED TO CONNECT SUPABASE: {e}")
        print("Check your DATABASE_URL and internet connection")
        db_pool = None

async def close_db_pool():
    """Close database pool on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
        print("Database pool closed")

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
                firstname TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,

                last_name TEXT,
                date_of_birth DATE,
                address TEXT,
                phone_number TEXT,
                gender TEXT,
                profile_picture TEXT,
                image_url TEXT,
                bio TEXT,

                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS firstname TEXT UNIQUE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();")
        
        # USER IMAGES TABLE (for storing image bytes)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_images (
                id SERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                image_name TEXT NOT NULL,
                image_data BYTEA NOT NULL,
                content_type TEXT NOT NULL,
                image_size INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_images_user_id ON user_images(user_id);")
        
        # GOOGLE USERS TABLE (OAuth authentication)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS google_users (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                firstname TEXT,
                profile_picture TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("ALTER TABLE google_users ADD COLUMN IF NOT EXISTS firstname TEXT;")
        await conn.execute("ALTER TABLE google_users ADD COLUMN IF NOT EXISTS image_url TEXT;")
        
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
                type TEXT NOT NULL, 
                surah_name_eng TEXT NOT NULL,
                surah_name_arb TEXT NOT NULL,
                surah_no INTEGER NOT NULL,
                ayah_no INTEGER NOT NULL,
                total_ayah INTEGER NOT NULL,
                ayah TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, surah_no, ayah_no)
            )
        """)
        
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
        
        # PASSWORD RESET OTPs TABLE
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_otps (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                reset_token TEXT UNIQUE NOT NULL,
                otp TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("ALTER TABLE password_reset_otps ADD COLUMN IF NOT EXISTS reset_token TEXT UNIQUE;")

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_otp_email
            ON password_reset_otps(email, created_at DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_otp_reset_token
            ON password_reset_otps(reset_token)
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
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reflection_user
            ON recent_reflections(user_id)
        """)

        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT,
                title TEXT,
                description TEXT,
                file_context TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS user_id TEXT;")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_user 
            ON chat_sessions(user_id, created_at DESC)
        """)
        
        print("✅ chat_sessions table created/verified")

        # 🆕 SESSION FILES TABLE (Child table - requires chat_sessions to exist)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS session_files (
                id SERIAL PRIMARY KEY,
                file_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_url TEXT,
                file_content TEXT,
                file_size INTEGER,
                message_id TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_files_session 
            ON session_files(session_id, created_at DESC)
        """)
        
        print("✅ session_files table created/verified")

        # Add foreign key constraint (only if not already exists)
        fk_check = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE constraint_name = 'session_files_session_id_fkey'
        """)

        if fk_check == 0:
            try:
                await conn.execute("""
                    ALTER TABLE session_files
                    ADD CONSTRAINT session_files_session_id_fkey
                    FOREIGN KEY (session_id)
                    REFERENCES chat_sessions(session_id)
                    ON DELETE CASCADE
                """)
                print("✅ Foreign key constraint added to session_files")
            except Exception as e:
                logger.warning(f"FK constraint failed (may already exist): {e}")

        # Disable RLS for session_files table (development only)
        try:
            await conn.execute("""
                ALTER TABLE session_files DISABLE ROW LEVEL SECURITY
            """)
            print("✅ RLS disabled for session_files table")
        except Exception as e:
            logger.warning(f"RLS disable failed: {e}")

        # Add message_id column if it doesn't exist
        await conn.execute("ALTER TABLE session_files ADD COLUMN IF NOT EXISTS message_id TEXT;")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_files_message_id 
            ON session_files(message_id)
        """)
        print("✅ message_id column added/verified for session_files")

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

async def delete_all_user_sessions(user_id: str):
    """Delete all chat sessions and messages for a specific user"""
    supabase_client = get_supabase_client()

    try:
        # Get all session_ids for the user
        sessions_with_user = supabase_client.table('chat_sessions')\
            .select('session_id')\
            .eq('user_id', user_id)\
            .execute()

        # Also get sessions without user_id (backward compatibility)
        sessions_without_user = supabase_client.table('chat_sessions')\
            .select('session_id')\
            .is_('user_id', None)\
            .execute()

        session_ids = [s['session_id'] for s in sessions_with_user.data + sessions_without_user.data]

        if session_ids:
            # 🆕 Delete session files first
            for sess_id in session_ids:
                try:
                    supabase_client.table('session_files')\
                        .delete()\
                        .eq('session_id', sess_id)\
                        .execute()
                except Exception as e:
                    logger.warning(f"Error deleting files for session {sess_id}: {e}")

            # Get message IDs
            messages = supabase_client.table('chat_messages')\
                .select('message_id')\
                .in_('session_id', session_ids)\
                .execute()

            message_ids = [m['message_id'] for m in messages.data]

            if message_ids:
                # Delete chat_rules
                for msg_id in message_ids:
                    try:
                        supabase_client.table('chat_rules')\
                            .delete()\
                            .eq('message_id', msg_id)\
                            .execute()
                    except Exception:
                        pass

                # Delete content_feedback
                for sess_id in session_ids:
                    try:
                        supabase_client.table('content_feedback')\
                            .delete()\
                            .eq('session_id', sess_id)\
                            .execute()
                    except Exception:
                        pass

                # Delete messages
                supabase_client.table('chat_messages')\
                    .delete()\
                    .in_('session_id', session_ids)\
                    .execute()

            # Delete sessions
            supabase_client.table('chat_sessions')\
                .delete()\
                .in_('session_id', session_ids)\
                .execute()

            print(f"✅ Deleted {len(session_ids)} sessions for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting all sessions for user {user_id}: {e}")
        return False


async def delete_user_session(user_id: str, session_id: str):
    """Delete a specific chat session and its messages for a user"""
    supabase_client = get_supabase_client()

    try:
        # Verify the session belongs to the user
        session_check = supabase_client.table('chat_sessions')\
            .select('session_id')\
            .eq('session_id', session_id)\
            .eq('user_id', user_id)\
            .execute()

        if not session_check.data:
            print(f"❌ Session {session_id} not found or doesn't belong to user {user_id}")
            return False

        # 🆕 Delete session files first
        try:
            supabase_client.table('session_files')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()
            print(f"✅ Deleted files for session {session_id}")
        except Exception as e:
            logger.warning(f"Error deleting files: {e}")

        # Get message_ids for this session
        messages = supabase_client.table('chat_messages')\
            .select('message_id')\
            .eq('session_id', session_id)\
            .execute()

        message_ids = [m['message_id'] for m in messages.data]

        if message_ids:
            # Delete chat_rules
            for msg_id in message_ids:
                try:
                    supabase_client.table('chat_rules')\
                        .delete()\
                        .eq('message_id', msg_id)\
                        .execute()
                except Exception:
                    pass

            # Delete content_feedback
            try:
                supabase_client.table('content_feedback')\
                    .delete()\
                    .eq('session_id', session_id)\
                    .execute()
            except Exception:
                pass

            # Delete messages
            supabase_client.table('chat_messages')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()

        # Delete the session
        supabase_client.table('chat_sessions')\
            .delete()\
            .eq('session_id', session_id)\
            .execute()

        print(f"✅ Deleted session {session_id} for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting session {session_id} for user {user_id}: {e}")
        return False