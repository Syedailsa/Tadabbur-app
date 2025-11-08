from agents import (
    Agent, ModelSettings, OpenAIChatCompletionsModel,
    RunConfig, Runner, GuardrailFunctionOutput,
    RunContextWrapper, TResponseInputItem, input_guardrail
)
from openai import AsyncOpenAI
import pandas as pd
from dotenv import load_dotenv
import asyncio
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
    "\n".join(df["ayah_en"].astype(str)[:50]),
    "\n".join(df["ayah_ar"].astype(str)[:50]),
    "\n".join(df["surah_no"].astype(str)[:50]),
    "\n".join(df["surah_name_en"].astype(str)[:50]),
]

# Load example story for narrative style
with open("story_exmp.txt", "r", encoding="utf-8") as f:
    story_example = f.read()

# 🧠 Guardrail Agent — checks semantic relevance
guardrail_agent = Agent(
    name="SemanticGuardrail",
    instructions=(
        "Determine whether the user's request is semantically related to the provided Quranic dataset "
        "and its themes (moral lessons, reflection, faith, spirituality, prophets, divine guidance, etc.). "
        "If it’s unrelated to these themes or doesn’t use the Quranic context meaningfully, respond with 'UNRELATED'. "
        "Otherwise, respond with 'RELATED'."
    ),
    model=model
)

# 💬 Fallback Agent — responds gracefully to off-topic queries
fallback_agent = Agent(
    name="FallbackResponder",
    instructions=(
        "You are a polite assistant. If the user's question is unrelated to Quranic storytelling, "
        "gently remind them that you can only create Quran inspired moral stories."
    ),
    model=model
)

# 🛡️ Input Guardrail — uses semantic judgment instead of keyword matching
@input_guardrail
async def semantic_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    decision = str(result.final_output).strip().upper()

    if "UNRELATED" in decision:
        # Graceful fallback: no error, just redirect
        fallback = await Runner.run(fallback_agent, input, context=ctx.context)
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
        "Using the Quranic dataset context provided, craft short, emotionally engaging stories "
        "that teach moral lessons from Quranic verses. "
        "Your stories should blend Arabic and English verses, highlight wisdom, and follow this example:\n\n"
        f"{story_example}\n\n"
        "Always stay relevant to the Quranic moral and narrative context."
    ),
    model=model,
    model_settings=ModelSettings(temperature=0.7),
    input_guardrails=[semantic_guardrail],
    output_guardrails=[story_output_guardrail],
)
