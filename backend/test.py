import os
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions

load_dotenv()
TADABBUR_PROJECT_URL = os.getenv('TADABBUR_PROJECT_URL')
TADABBUR_API_KEY = os.getenv('TADABBUR_API_KEY')

supabase = create_client(
                TADABBUR_PROJECT_URL,
                TADABBUR_API_KEY,
                options=ClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10,
                    schema="public",
                )
            )
res = supabase.table("chat_messages").select("message_id, story_data").execute()
rows = res.data
images = []
for row in rows:
    for obj in row.get("story_data") or []:
        img = obj.get("image")
        if img:
            images.append({"image_url":img})
print(images)