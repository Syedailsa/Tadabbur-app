import os
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions

load_dotenv()
TADABBUR_PROJECT_URL = os.getenv('TADABBUR_PROJECT_URL')
TADABBUR_API_KEY = os.getenv('TADABBUR_API_KEY')

# 1. Create a global variable to hold the client
_supabase_instance = None

def get_supabase_client():
    global _supabase_instance
    
    # ONLY create the client if it doesn't exist yet
    if _supabase_instance is None:
        try:
            _supabase_instance = create_client(
                TADABBUR_PROJECT_URL,
                TADABBUR_API_KEY,
                options=ClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10,
                    schema="public",
                )
            )
            print("✅ Supabase Client connected successfully! (INITIALIZED)")
        except Exception as e:
            print("Some error occurred while connecting to supabase", e)
            raise
            
    # Return the existing client
    print("✅ Supabase Client already exists.")
    return _supabase_instance