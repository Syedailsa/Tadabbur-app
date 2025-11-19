from agents import (
    Agent, ModelSettings, OpenAIChatCompletionsModel, 
    RunConfig, Runner, GuardrailFunctionOutput,
    RunContextWrapper, TResponseInputItem, function_tool, input_guardrail
)
from openai import AsyncOpenAI
from typing import Optional
# from tafseer_agent import Tafsir_Agent
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

SUPPORTED_MODELS = {
    "kimi-k2-instruct-0905": {
        "model_id": "accounts/fireworks/models/kimi-k2-instruct-0905",
        "provider": external_client,
        "name": "Kimi K2 Instruct 0905"
    },
    "deepseek-v3p1-terminus": {
        "model_id": "accounts/fireworks/models/deepseek-v3p1-terminus",
        "provider": external_client,
        "name": "DeepSeek V3.1 Terminus"
    },
    "gpt-oss-120b": {
        "model_id": "accounts/fireworks/models/gpt-oss-120b",
        "provider": external_client,
        "name": "OpenAI GPT-OSS 120B"
    },
    "gpt-oss-20b": {  # your current default
        "model_id": "accounts/fireworks/models/gpt-oss-20b",
        "provider": external_client,
        "name": "OpenAI GPT-OSS 20B"
    },
    "qwen3-235b-a22b-instruct": {  # your current default
        "model_id": "accounts/fireworks/models/qwen3-235b-a22b-instruct",
        "provider": external_client,
        "name": "Qwen3 235B a22B Instruct"
    }
}

def get_model_config(model_key: Optional[str] = None) -> RunConfig:
    """
    Returns a RunConfig with the selected model.
    Falls back to default 'gpt-oss-20b' if invalid or None.
    """
    if not model_key or model_key not in SUPPORTED_MODELS:
        model_key = "gpt-oss-20b"  # fallback

    info = SUPPORTED_MODELS[model_key]

    selected_model = OpenAIChatCompletionsModel(
        model=info["model_id"],
        openai_client=info.get("provider") or external_client
    )

    return RunConfig(
        model=selected_model,
        model_provider=info.get("provider") or external_client,
        tracing_disabled=True
    )

# config as default (for backward compatibility)
config = get_model_config("gpt-oss-20b") 

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

# @function_tool
# async def tafseer(ayah_reference: str) -> str:
#     print(f"Fetching tafseer for ayah reference: {ayah_reference}")
#     """
#     Fetches the tafseer for a given Quranic ayah reference using the Tafsir_Agent.

#     Args:
#         ayah_reference (str): The reference of the ayah (e.g., "2:25").

#     Returns:
#         str: The tafseer content for the specified ayah.
#     """
#     result = await Runner.run(
#         Tafsir_Agent,
#         ayah_reference,
#         run_config=config
#     )
#     print(f"Tafseer fetched for {ayah_reference}: {result.final_output}")
#     return str(result.final_output)

# 🧠 Guardrail Agent — checks semantic relevance
guardrail_agent = Agent(
    name="Guardrail check",
    instructions=(
        "Determine whether the user's request is semantically related to the provided Quranic dataset "
        "and its themes (moral lessons, reflection, faith, spirituality, prophets, divine guidance, etc.). "
        "If it’s unrelated to these themes or doesn’t use the Quranic context meaningfully, respond with 'UNRELATED'. "
        "Otherwise, respond with 'RELATED'."
    )
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
    )
)

# 🛡️ Input Guardrail — uses semantic judgment instead of keyword matching
@input_guardrail
async def quran_input_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    print("Running QuranStory input guardrail...")
    """Checks if the input question is Quranic-stories"""
        # Extract the model selected by the user (passed via context from main.py)
    current_model_key = getattr(ctx.context, "model_key", "gpt-oss-20b")

    # Build a RunConfig with the SAME model the user chose
    guardrail_config = get_model_config(current_model_key)

    result = await Runner.run(guardrail_agent, input,run_config=guardrail_config, context=ctx.context)
    decision = str(result.final_output).strip().upper()
    print(decision)

    if "UNRELATED" in decision:
        # Graceful fallback: no error, just redirect
        fallback = await Runner.run(fallback_agent, "This seems unrelated to Quranic story telling",run_config=guardrail_config, context=ctx.context)
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
    )
)

@output_guardrail
async def story_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    print("Running QuranStory output guardrail...")
    """Ensure the story stays within Quranic moral context"""
    # Extract the model selected by the user (passed via context from main.py)
    current_model_key = getattr(ctx.context, "model_key", "gpt-oss-20b")

    # Build a RunConfig with the SAME model the user chose
    guardrail_config = get_model_config(current_model_key)

    result = await Runner.run(guardrail_agent, output ,run_config=guardrail_config, context=ctx.context)
    verdict = str(result.final_output).strip().lower()

    if "invalid" in verdict:
        fallback = await Runner.run(
            fallback_agent,
            "Sorry, this story seems unrelated to the Quranic teachings.",
            run_config=guardrail_config,
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
        "Your stories should be engaging and like this example:\n\n"
        f"{story_example}\n\n"
        "the final answer should be in a story format for users to read and not in json form. "
        "Always stay relevant to the Quranic moral and narrative context."
    ),
    model=config.model,
    # tools=[tafseer],
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
