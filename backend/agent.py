from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner, AsyncOpenAI, GuardrailFunctionOutput,InputGuardrailTripwireTriggered, RunContextWrapper, TResponseInputItem, input_guardrail
from story_agent import story_agent
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
ct1 = "\n".join(df["ayah_en"].astype(str))
ct2 = "\n".join(df["ayah_ar"].astype(str))
ct3 = "\n".join(df["surah_no"].astype(str))
ct4= "\n".join(df["surah_name_en"].astype(str))
context = [ct1, ct2, ct3, ct4]

guardrail_agent = Agent( 
    name="Guardrail check",
    instructions=f'Check if the user is asking you about data related to the {context} you are provided with.'
    f"If its unrelated to the Quranic {context} meaningfully, respond with 'UNRELATED'."
    "Otherwise, respond with 'RELATED'.",
    model=model
)

fallback_agent = Agent(
    name="FallbackResponder",
    instructions="You are unable to answer the question as it is outside your knowledge base. Politely inform the user that you cannot provide an answer.",
    model=model
)

@input_guardrail
async def quran_input_guardrail( 
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    output = str(result.final_output).strip().lower()

    if "unrelated" in output:
        fallback = await Runner.run(fallback_agent, input, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=fallback.final_output, 
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="Input verified — Quranic content confirmed.",
        tripwire_triggered=False
    )

from agents import output_guardrail, GuardrailFunctionOutput

# --- OUTPUT GUARDRAIL AGENT ---
output_guard_agent = Agent(
    name="OutputVerifier",
    instructions=(
        f"You are a strict Quranic context verifier. "
        f"Given the original Quranic context:\n{context}\n\n"
        f"When you receive an assistant's response, determine if it strictly relates to the {context} provided. "
        "If yes, respond only with 'VALID'. "
        "If no, respond only with 'INVALID'."
    ),
    model=model,
)

@output_guardrail
async def quran_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """Checks if the generated output is Quranic and valid"""
    result = await Runner.run(output_guard_agent, output, context=ctx.context)
    output = str(result.final_output).strip().lower()

    if "invalid" in output:
        # If the model says the response drifted — send fallback
        fallback = await Runner.run(fallback_agent, "Sorry, I can only provide responses based on Quranic content.", context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=fallback.final_output,
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="Response validated — relevant to Quranic context.",
        tripwire_triggered=False
    )


agent = Agent(
    name="QuranTadabburAgent",
    instructions=f'You are Tadabbur a knowledgeable assistant specializing in Quranic knowledge on {context} data. Provide short detail on the Quranic verses provided in {context} data with its arabic too.'
    "Tell in proper structure by starting each ayah from a new line"
    "talk in english on default unless user asks in other language.",
    model_settings=ModelSettings(
        temperature=0.2,
    ),
    input_guardrails=[quran_input_guardrail],
    output_guardrails=[quran_output_guardrail],
    handoffs=[{"QuranStoryTeller": story_agent}]
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

# import pandas as pd

# df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")

# print(df.columns)
# print(df.head())

# # Show all distinct surah names to confirm the exact name
# print(df["surah_name_en"].unique()[:10])  # just first 10
