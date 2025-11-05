from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner, AsyncOpenAI, GuardrailFunctionOutput,InputGuardrailTripwireTriggered, RunContextWrapper, TResponseInputItem, input_guardrail

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel
import asyncio
import os

load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

external_client = AsyncOpenAI(
    api_key=FIREWORKS_API_KEY,
    base_url="https://api.fireworks.ai/inference/v1"
)

model = OpenAIChatCompletionsModel(
    model="accounts/fireworks/models/gpt-oss-20b", 
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

# Quran dataset
df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")
ct1 = "\n".join(df["ayah_en"].astype(str)[:50])
ct2 = "\n".join(df["ayah_ar"].astype(str)[:50])
ct3 = "\n".join(df["surah_no"].astype(str)[:50])
ct4= "\n".join(df["surah_name_en"].astype(str)[:50])
context = [ct1, ct2, ct3, ct4]

guardrail_agent = Agent( 
    name="Guardrail check",
    instructions=f'Check if the user is asking you about data related to the {context} you are provided with.',
    model=model
)

@input_guardrail
async def quran_guardrail( 
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=print("Quran guardrial tripped"), 
        tripwire_triggered=result.final_output,
    )

agent = Agent(
    name="QuranTadabburAgent",
    instructions=f'You are Tadabbur a knowledgeable assistant specializing in Quranic knowledge on {context} data. Provide short detail on the Quranic verses provided in {context} data with its arabic too.'
    "Tell in proper structure by starting each ayah from a new line",
    model_settings=ModelSettings(
        temperature=0.2,
    ),
    input_guardrails=[quran_guardrail],
)

# async def main():
#     # trip the guardrail
#     try:
#         await Runner.run(agent, "Hello, can you tell me the ayah no 17 of surah al baqarah?")
#         print("Guardrail didn't trip - this is unexpected")

#     except InputGuardrailTripwireTriggered:
#         print("Quran guardrail tripped")

# if __name__ == "__main__":
#     asyncio.run(main())