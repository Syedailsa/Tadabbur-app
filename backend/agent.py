from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner, AsyncOpenAI, GuardrailFunctionOutput, RunContextWrapper, TResponseInputItem, input_guardrail, output_guardrail
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

# --- CONTEXT FOR INPUT GUARDRAIL AGENT ---
quran_topics = """
The Quran discusses faith, worship, moral values, patience, guidance, repentance,
justice, stories of prophets, creation, the afterlife, and reflections on life and
spiritual growth. It does not cover math, technology, or unrelated worldly knowledge.
"""

guardrail_agent = Agent( 
    name="Guardrail check",
    # instructions=f'Check if the user is asking you about data related to the {context} you are provided with.'
    # f"If its unrelated to the Quranic {context} meaningfully, respond with 'UNRELATED'."
    # "Otherwise, respond with 'RELATED'.",
    instructions=(
        "Your task is to decide whether the user’s question is related to Quranic knowledge. "
        "If it’s about verses, tafsir, meaning, translation, reflection, or anything spiritually relevant, "
        "respond only with 'RELATED'. "
        "If it’s about unrelated topics such as math, science, entertainment, coding, or general trivia, "
        "respond only with 'UNRELATED'. "
        f"Context summary:\n{quran_topics}" 
        ),
    model=model
)

fallback_agent = Agent(
    name="FallbackResponder",
    instructions=(
        "You are Tadabbur your friendly Quran companion. "
        f"If a user says something unrelated to the Quran topics like {quran_topics} reply politely and warmly that you cant reply to topics related to maths, technology etc but if you are greeted then greet back and tell who you are and what can the user ask you, "
        "'Hi there! Im Tadabbur — I specialize in Quranic insights. What would you like to explore today?'"
    ),
    model=model
)

@input_guardrail
async def quran_input_guardrail( 
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    print("Running Quran input guardrail...")
    """Checks if the input question is Quranic-related"""
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    output = str(result.final_output).strip().lower()

    if "unrelated" in output:
        fallback = await Runner.run(fallback_agent, "This question seems unrelated to Quranic context.", context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=fallback.final_output, 
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="Input verified — Quranic content confirmed.",
        tripwire_triggered=False
    )

# --- OUTPUT GUARDRAIL AGENT ---
output_guard_agent = Agent(
    name="OutputVerifier",
    instructions=(
        "You are a strict verifier ensuring that Tadabbur’s responses remain Quran-related. "
        "If the assistant’s reply focuses on Quranic verses, tafsir, themes, moral lessons, or reflections, respond ONLY with 'VALID'. "
        "If it drifts into unrelated topics (e.g., math, tech, movies, or general knowledge), respond ONLY with 'INVALID'. "
        f"Context summary:\n{quran_topics}"
    ),
    model=model,
)

@output_guardrail
async def quran_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    print("Running Quran output guardrail...")
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
    "If a user asks for Quranic **stories**, narratives of prophets, or moral lessons, "
    "you must **handoff** the conversation to the `QuranStoryTeller` agent by calling "
    "`transfer_to_quranstoryteller`. "
    "talk in english on default unless user asks in other language.",
    model_settings=ModelSettings(
        temperature=0.2,
    ),
    input_guardrails=[quran_input_guardrail],
    output_guardrails=[quran_output_guardrail],
    handoffs=[{"QuranStoryTeller": story_agent}]
)

# async def main():
#     result = await Runner.run(agent, "Hello, can you story of hazrat adam (a.s)?" , run_config=config, context=context)
#     print(result.final_output)
#     print(result)

# if __name__ == "__main__":
#     asyncio.run(main())

# import pandas as pd

# df = pd.read_csv("QuranDataset.csv", encoding="utf-8-sig")

# print(df.columns)
# print(df.head())

# # Show all distinct surah names to confirm the exact name
# print(df["surah_name_en"].unique()[:10])  # just first 10