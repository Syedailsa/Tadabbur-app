from agents import (
    Agent, ModelSettings, OpenAIChatCompletionsModel,
    RunConfig, Runner, GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered, RunContextWrapper,
    TResponseInputItem, input_guardrail
)
from openai import AsyncOpenAI
import pandas as pd
from dotenv import load_dotenv
import asyncio
import os

# Load environment variables (for FIREWORKS_API_KEY)
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

# Load Quran dataset context
df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")

ct1 = "\n".join(df["ayah_en"].astype(str)[:50])
ct2 = "\n".join(df["ayah_ar"].astype(str)[:50])
ct3 = "\n".join(df["surah_no"].astype(str)[:50])
ct4 = "\n".join(df["surah_name_en"].astype(str)[:50])
context = [ct1, ct2, ct3, ct4]

# Guardrail Agent – only allow storytelling related to the Quranic context
guardrail_agent = Agent(
    name="StoryGuardrail",
    instructions=f"Determine if the users request relates to storytelling inspired by the Quranic dataset {context}. If not, block it politely.",
    model=model
)

@input_guardrail
async def story_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    # Check if guardrail should trip
    if "story" not in str(result.final_output).lower() and "quran" not in str(result.final_output).lower():
        return GuardrailFunctionOutput(
            output_info="This request isn't related to Quranic storytelling.",
            tripwire_triggered=True
        )

    return GuardrailFunctionOutput(
        output_info="Storytelling confirmed.",
        tripwire_triggered=False
    )

# Storytelling Agent
story_agent = Agent(
    name="QuranStoryTeller",
    instructions=(
        "You are a storytelling assistant inspired by Quranic knowledge. "
        "Using the provided Quran dataset, craft short, engaging stories "
        "that teach moral lessons from the verses, mentioning Arabic and English context. "
        "Always start each new story or verse on a new line, in a poetic and inspiring tone."
    ),
    model=model,
    model_settings=ModelSettings(temperature=0.7),
    input_guardrails=[story_guardrail]
)

# Runner test
async def main():
    try:
        result = await Runner.run(story_agent, "Tell me a story from surah baqarah in the Quran", run_config=config)
        print("\n✨ Tadabbur Story Output:\n")
        print(result.final_output)

    except InputGuardrailTripwireTriggered:
        print("⚠️ Guardrail triggered — unrelated to storytelling.")

if __name__ == "__main__":
    asyncio.run(main())
