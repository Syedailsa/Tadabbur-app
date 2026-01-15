import os
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions


load_dotenv()
TADABBUR_PROJECT_URL = os.getenv('TADABBUR_PROJECT_URL')
TADABBUR_API_KEY = os.getenv('TADABBUR_API_KEY')

def get_supabase_client():
    try:
        print("Connecting to Database for saving user messages")
        supabase_client: Client = create_client(
            TADABBUR_PROJECT_URL,
            TADABBUR_API_KEY,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10,
                schema="public",
            )
        )
        print("✅ Supabase Client connected successfully!")
    
        return supabase_client
    except Exception as e:
        print("Some error occured while connecting to supabase", e)
        raise