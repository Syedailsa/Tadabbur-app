from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner, AsyncOpenAI
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel
import asyncio
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Use Gemini’s reasoning model for main agent
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash-lite",    
    openai_client=external_client
)

# RunConfig for consistency
config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

# Load your Quran dataset
df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")
ct1 = "\n".join(df["ayah_en"].astype(str)[:50])
ct2 = "\n".join(df["ayah_ar"].astype(str)[:50])
ct3 = "\n".join(df["surah_no"].astype(str)[:50])
ct4= "\n".join(df["surah_name_en"].astype(str)[:50])
context = [ct1, ct2, ct3, ct4]

class structure(BaseModel):
    ayah_en: str 
    ayah_ar: str
    surah_no: int
    surah_name_en: str

agent = Agent(
    name="QuranTadabburAgent",
    instructions=f'You are Tadabbur a knowledgeable assistant specializing in Quranic knowledge on {context} data. Provide short detail on the Quranic verses provided in {context} data with its arabic too.'
    "Tell in proper structure by starting each ayah from a new line",
    model_settings=ModelSettings(
        temperature=0.2,
    ),
    # output_type= structure
)

# async def main():
#     result = await Runner.run(
#         agent,
#         "tell me the arabic of the whole surah al baqarah and its meaning in english",
#         run_config=config
#     )
#     print(result.final_output)

# asyncio.run(main())
