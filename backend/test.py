import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_AI_API_KEY")

print("APIKEY GROQ", api_key)
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print(response.json())