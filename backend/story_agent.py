from agents import (
    Agent, ModelSettings, OpenAIChatCompletionsModel, 
    RunConfig, Runner, GuardrailFunctionOutput,
    RunContextWrapper, TResponseInputItem, function_tool, input_guardrail
)
from openai import AsyncOpenAI
from tafseer_agent import Tafsir_Agent
import pandas as pd
from dotenv import load_dotenv
import asyncio
import json
import os

# Load environment variables
load_dotenv()
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

# Initialize Fireworks client
external_client = AsyncOpenAI(
    api_key=FIREWORKS_API_KEY,
    base_url="https://api.fireworks.ai/inference/v1"
)

# Define model and configuration
model = OpenAIChatCompletionsModel(
    model="accounts/fireworks/models/gpt-oss-20b",
    openai_client=external_client
)
config = RunConfig(model=model, model_provider=external_client, tracing_disabled=True)

# Load Quran dataset context
df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")
context = [
    "\n".join(df["ayah_en"].astype(str)),
    "\n".join(df["ayah_ar"].astype(str)),
    "\n".join(df["surah_no"].astype(str)),
    "\n".join(df["surah_name_en"].astype(str)),
]

# Load example story for narrative style
with open("story_exmp.txt", "r", encoding="utf-8") as f:
    story_example = json.load(f)

@function_tool
async def tafseer(ayah_reference: str) -> str:
    print(f"Fetching tafseer for ayah reference: {ayah_reference}")
    """
    Fetches the tafseer for a given Quranic ayah reference using the Tafsir_Agent.

    Args:
        ayah_reference (str): The reference of the ayah (e.g., "2:25").

    Returns:
        str: The tafseer content for the specified ayah.
    """
    result = await Runner.run(
        Tafsir_Agent,
        ayah_reference,
        run_config=config
    )
    print(f"Tafseer fetched for {ayah_reference}: {result.final_output}")
    return str(result.final_output)

# 🧠 Guardrail Agent — checks semantic relevance
guardrail_agent = Agent(
    name="Guardrail check",
    instructions=(
        "Determine whether the user's request is semantically related to the provided Quranic dataset "
        "and its themes (moral lessons, reflection, faith, spirituality, prophets, divine guidance, etc.). "
        "If it’s unrelated to these themes or doesn’t use the Quranic context meaningfully, respond with 'UNRELATED'. "
        "Otherwise, respond with 'RELATED'."
    ),
    model=model
)

# --- CONTEXT FOR INPUT GUARDRAIL AGENT ---
quran_topics = """
The Quran discusses faith, worship, moral values, patience, guidance, repentance,
justice, stories of prophets, creation, the afterlife, and reflections on life, islamic history and
spiritual growth. It does not cover math, technology, or unrelated worldly knowledge.
"""

# 💬 Fallback Agent — responds gracefully to off-topic queries
fallback_agent = Agent(
    name="FallbackResponder",
    instructions=(
        "You are a polite assistant."
        f"If a user says something unrelated to the Quran topics like {quran_topics} reply politely and warmly that you cant reply to topics related to maths, technology etc but if you are greeted then greet back and tell who you are and what can the user ask you, "
        "gently remind them that you can only create Quran inspired moral stories."
    ),
    model=model
)

# 🛡️ Input Guardrail — uses semantic judgment instead of keyword matching
@input_guardrail
async def quran_input_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    print("Running QuranStory input guardrail...")
    """Checks if the input question is Quranic-stories"""
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    decision = str(result.final_output).strip().upper()
    print(decision)

    if "UNRELATED" in decision:
        # Graceful fallback: no error, just redirect
        fallback = await Runner.run(fallback_agent, "This seems unrelated to Quranic story telling", context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=fallback.final_output,
            tripwire_triggered=True  # tripwire signals fallback, not failure
        )

    return GuardrailFunctionOutput(
        output_info="Input is relevant to Quranic storytelling.",
        tripwire_triggered=False
    )

from agents import output_guardrail, GuardrailFunctionOutput

output_guard_agent = Agent(
    name="OutputVerifier",
    instructions=(
        f"You are a strict Quranic context verifier. "
        f"Given the original Quranic context:\n{context}\n\n"
        "When you receive an assistant's response, determine if it strictly relates "
        "to Quranic teachings, ayahs, stories, or moral lessons. "
        "If yes, respond only with 'VALID'. "
        "If no, respond only with 'INVALID'."
    ),
    model=model,
)

@output_guardrail
async def story_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    print("Running QuranStory output guardrail...")
    """Ensure the story stays within Quranic moral context"""
    result = await Runner.run(output_guard_agent, output, context=ctx.context)
    verdict = str(result.final_output).strip().lower()

    if "invalid" in verdict:
        fallback = await Runner.run(
            fallback_agent,
            "Sorry, this story seems unrelated to the Quranic teachings.",
            context=ctx.context
        )
        return GuardrailFunctionOutput(
            output_info=fallback.final_output,
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="Output verified — relevant story.",
        tripwire_triggered=False
    )

# 🌙 Main Quranic Storytelling Agent
story_agent = Agent(
    name="QuranStoryTeller",
    instructions=(
        "You are Tadabbur, a storytelling assistant inspired by the Quran. "
        f"Using the Quranic dataset {context} provided, craft short, emotionally engaging stories "
        "that teach moral lessons from Quranic verses. "
        "take the ayah references by calling the tafseer tool to build the story around them. "
        "Your stories should be engaging and like this example:\n\n"
        f"{story_example}\n\n"
        "the final answer should be in a story format for users to read and not in json form. "
        "Always stay relevant to the Quranic moral and narrative context."
    ),
    model=model,
    tools=[tafseer],
    model_settings=ModelSettings(temperature=0.7),
    input_guardrails=[quran_input_guardrail],
    output_guardrails=[story_output_guardrail],
)

# async def main():
#     try:
#         result = await Runner.run(
#             story_agent,
#             "hi.",
#             run_config=config
#         )
#         print("🧠 Final Output:\n", result.final_output)

#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     asyncio.run(main())
