import asyncio
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    RunConfig,
    ModelSettings,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    output_guardrail
)
from dotenv import load_dotenv
from pydantic import BaseModel


import pandas as pd
load_dotenv()
import os

class Tafsir_Request(BaseModel):
    is_query_valid_or_related_to_context: bool
    reasoning: str
    answer: str



FIRE_WORKS_API = os.getenv("FIREWORKS_API_KEY")
if not FIRE_WORKS_API:
    raise ValueError("API_KEY not found in environment variables.")

Base_URL = "https://api.fireworks.ai/inference/v1"
MODEL_NAME = "accounts/fireworks/models/gpt-oss-20b"

CSV_FILE_PATH= f"quran_tafseer_hf.csv"





df = pd.read_csv(CSV_FILE_PATH)
texts = df['surah_name'].tolist()
csv_content = "\n\n".join(texts[:10])  

class Output_type(BaseModel):
    surah_name: str
    revelation_type: str
    ayah: str
    tafsir_book: str
    tafsir_content: str




provider = AsyncOpenAI(
    api_key= FIRE_WORKS_API,
    base_url= Base_URL
        )

gemini_model = OpenAIChatCompletionsModel(
    model= MODEL_NAME,
    openai_client= provider

)
config = RunConfig(
    model= gemini_model,
    model_provider=provider,
    tracing_disabled= True

)


        # # ------------------------------------------------------------------
        # # ---------------------- Input guardrail ---------------------------
        # # -------------------------------------------------------------------

        # @input_guardrail
        # async def input_guardrail_agent_fn(
        #     ctx: RunContextWrapper[None],
        #     agent: Agent,
        #     input: str| list[TResponseInputItem]
        # )-> GuardrailFunctionOutput:
        #     result = await Runner.run(
        #         input_guardrails_agent,
        #         input,
        #         context= ctx.context,
        #         run_config= config
        #     )
        #     return GuardrailFunctionOutput(
        #         output_info= result.final_output,
        #         tripwire_triggered= not result.final_output.is_query_valid_or_related_to_context
        #     )
        
        
        
        # # ---------------------------------------------------------------------------------------
        # # ------------------------------------- Output Guardrail --------------------------------
        # # ---------------------------------------------------------------------------------------

        # @output_guardrail
        # async def output_agent_guard_fn(
        #     ctx: RunContextWrapper[None],
        #     agent: Agent,
        #     output,
        # )-> GuardrailFunctionOutput:
        #     result = await Runner.run(
        #         output_guardrail_agent,
        #         output,
        #         context= ctx.context,
        #         run_config= config
        #     )
        #     return GuardrailFunctionOutput(
        #         output_info= result.final_output,
        #         tripwire_triggered= not result.final_output.is_query_valid_or_related_to_context
        #     )



Tafsir_Agent: Agent = Agent(
    name= "QuranicTafsirAgent",
    instructions= f"""You are a Quranic Tafsir agent that provides explanations of Quranic verses
    based only on the following context:\n\n{csv_content}\n\nRestriction: Use ONLY the provided c
    ontext. Do NOT use external knowledge, web resources, or hallucinate.
    
    """,

    model_settings= ModelSettings(
        temperature= 0.7,
        
    ),
    # input_guardrails=[input_guardrail_agent_fn],
    # output_guardrails= [output_agent_guard_fn],
    
)

# async def main():
#     try:
#         result = await Runner.run(
#             starting_agent= Tafsir_Agent,
#             input= "tell me the tafseer of surah baqarah ayah number 5",
#             run_config= config            
#         )
#         print("Tafsir Agent Result:")
#         print(result.final_output)
#     except InputGuardrailTripwireTriggered as e:
#         print("Input Guardrail Tripwire Triggered:")
#         print(e)
#     except OutputGuardrailTripwireTriggered as e:
#         print("Output Guardrail Tripwire Triggered:")
#         print(e)

# if __name__ == "__main__":
#     asyncio.run(main())



