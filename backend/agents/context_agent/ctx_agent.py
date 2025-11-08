from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    RunConfig,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered
    
)


import os
from dotenv import load_dotenv
import asyncio
import pandas as pd
from pydantic import BaseModel

# Load .env
load_dotenv()
FIRE_WORKS_API = os.getenv("FIRE_WORKS_API")
if not FIRE_WORKS_API:
    raise ValueError("API_KEY not found in environment variables.")

# CSV path
CSV_PATH = "asbabul_nuzul_text.csv"

async def main():
    
    df = pd.read_csv(CSV_PATH)
    texts = df['text'].tolist()
    
    
    csv_content = "\n\n".join(texts[:50])  
    # Initialize LLM client
    client = AsyncOpenAI(
        api_key= FIRE_WORKS_API,
        base_url="https://api.fireworks.ai/inference/v1"
    )

    llm_model = OpenAIChatCompletionsModel(
        model="accounts/fireworks/models/gpt-oss-20b",
        openai_client=client
    )

    config = RunConfig(
        model=llm_model,
        model_provider=client,
        tracing_disabled=True
    )

   

    # Define agent
    agent = Agent(
        name="Tadabbur Context Agent",
        instructions=(
            "You are a Quranic Context Agent. Read this CSV content and suggest the necessary columns "
            "for structuring the Asbabul Nuzul data for AI embedding and retrieval. "
            "For each column, provide its name and purpose.\n\n"
            f"CSV content:\n{csv_content}"
        ),             
    )

    try:
        result = await Runner.run(
            starting_agent= agent,
            input= "tell me the most important part of the history of the quran and also tell the source of which line and which number",
            run_config= config            
        )
        print("Context Agent Result:")
        print(result.final_output)
    except InputGuardrailTripwireTriggered as e:
        print("Input Guardrail Tripwire Triggered:")
        print(e)
    except OutputGuardrailTripwireTriggered as e:
        print("Output Guardrail Tripwire Triggered:")
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
