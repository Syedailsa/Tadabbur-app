import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
# from models import CleanText

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_AI_API_KEY")

groq_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="openai/gpt-oss-120b", 
    temperature=0, 
    max_retries=2,
    # response_format=CleanText
) 

system_instruction = """
You are a Text-to-Speech Pre-processor. Your job is to convert Markdown formatted text into a clean script optimized for a TTS engine to read aloud.

**RULES:**
1. **Remove Markdown:** Strip all '#', '*', '_', '---', '>', ',', '!', '`' and more similar special characters, just bring back the clean text without any characters.
2. **Expand Abbreviations:** Convert things like "vs." to "versus", "e.g." to "for example".
3. **Handle Citations:** Convert "Surah 2:255" to "Surah 2, Verse 255" so it reads naturally.
4. **Remove Visuals:** Remove any image tags, links, or complex tables. Just extract the text content from them if possible, or skip them.
5. **Natural Flow:** Ensure the punctuation creates natural pauses.
6. **NO PREAMBLE:** Do NOT say "Here is the cleaned text". Just output the final text immediately.

**INPUT TEXT:**
{text}
"""

prompt = ChatPromptTemplate.from_template(system_instruction)

cleaning_chain = prompt | groq_llm | StrOutputParser()

async def clean_text_with_groq(text: str) -> str:
    """
    Passes raw markdown to Groq and returns clean, speakable text.
    """
    if not text: 
        return ""
    
    try:
        clean_text = await cleaning_chain.ainvoke({"text": text})
        print(f"✅ Groq Cleaned Text: {clean_text}")
        return clean_text.strip()
    except Exception as e:
        print(f"⚠️ Groq Cleaning Failed: {e}. Falling back to raw text.")
        return text # Fail safe: return original text if Groq errors out