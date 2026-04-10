from utils.db_retry import db_retry
from config.db import get_supabase_client
import asyncio

supabase_client = get_supabase_client()

async def test_function():
    try:
        # chat_sessions = await db_retry(
        #     lambda: supabase_client.table('chat_sessions')
        #     .select('session_id', 'title', 'description', 'created_at')
        #     .eq('user_id', user_id)
        #     .order('created_at', desc=True)
        #     .execute(), label="fetch_chat_sessions"
        # )
        user_message = await db_retry(
            lambda: supabase_client.table('chat_messages').select('reply_to_message_id').eq("message_id", "fcf65846-e5c6-4544-9474-b2b8c5488b6a").limit(1).maybe_single().execute(), label="fetch_user_message_id_of_assistant_message" 
        )
        print("user_message", user_message)
        
    except Exception as e:
        print(f"Some error occured: Error, {e}")


asyncio.run(test_function())