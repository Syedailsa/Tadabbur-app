import os
from langchain_groq import ChatGroq

GROQ_API_KEY = os.getenv("GROQ_AI_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ API Key not available!")


SUMMARIZER_MODEL = "llama-3.1-8b-instant"
summarizer_llm = ChatGroq(
    api_key = GROQ_API_KEY,
    model = SUMMARIZER_MODEL,
    temperature = 0.1
)

