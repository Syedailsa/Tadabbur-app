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
    output_guardrail,
    function_tool
)
import json
from typing import Any
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

CSV_FILE_PATH= "quran_tafseer_hf.csv"


df = pd.read_csv(CSV_FILE_PATH)
texts = df['tafsir_content'].tolist()
csv_content = "\n\n".join(texts[:10]) 

json_file_path= "quran_tafseer_hf.json"

# json reader
function_tool
def read_json_file(json_file_path: str) -> Any:
    """
    Reads a JSON file and returns it as a Python object (dict or list).
    Callable by other scripts or agents.

    Args:
        json_file_path (str): Path to the JSON file

    Returns:
        dict/list: JSON content as Python object
    """
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data
 


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

fireworkmodel = OpenAIChatCompletionsModel(
    model= MODEL_NAME,
    openai_client= provider

)
config = RunConfig(
    model= fireworkmodel,
    model_provider=provider,
    tracing_disabled= True
    
)


input_guardrails_agent = Agent(
    name = "Quranic Tafseer Guardrail Agent",
    instructions= """You are Quranic Input Checker Agent that checks if the user query is valid and related to the provided context
    about Quranic Tafseer. If the query is valid and related, respond with is_query_valid_or_related_to_context as true, provide 
    reasoning and the answer based on the context. If not, respond with is_query_valid_or_related_to_context as false, provide 
    reasoning and do not provide an answer.""",
    output_type= Tafsir_Request

)

output_guardrail_agent = Agent(
    name = "Quranic Tafseer Output Guardrail Agent",
    instructions="""
    You are Quranic Output Checker Agent that checks if the generated output is valid and related to the provided context
    about Quranic Tafseer. If the output is valid and related, respond with is_query_valid_or_related_to_context as true, provide 
    reasoning and the answer based on the context. If not, respond with is_query_valid_or_related_to_context as false, provide 
    reasoning and do not provide an answer.""",
    output_type= Tafsir_Request
    
    )


# ------------------------------------------------------------------
# ---------------------- Input guardrail ---------------------------
# -------------------------------------------------------------------

@input_guardrail
async def input_guardrail_agent_fn(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str| list[TResponseInputItem]
)-> GuardrailFunctionOutput:
    result = await Runner.run(
        input_guardrails_agent,
        input,
        context= ctx.context,
        run_config= config
    )
    return GuardrailFunctionOutput(
        output_info= result.final_output,
        tripwire_triggered= not result.final_output.is_query_valid_or_related_to_context
    )



# ---------------------------------------------------------------------------------------
# ------------------------------------- Output Guardrail --------------------------------
# ---------------------------------------------------------------------------------------

@output_guardrail
async def output_agent_guard_fn(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output,
)-> GuardrailFunctionOutput:
    result = await Runner.run(
        output_guardrail_agent,
        output,
        context= ctx.context,
        run_config= config
    )
    return GuardrailFunctionOutput(
        output_info= result.final_output,
        tripwire_triggered= not result.final_output.is_query_valid_or_related_to_context
    )



Tafsir_Agent: Agent = Agent(
name="Quranic Tafsir Agent",
instructions=f"""
You are a Quranic Tafsir agent. Provide explanations of Quranic verses based ONLY on the following resources:

1. The provided CSV context: {csv_content}
2. The JSON reading tool: `read_json_file` (you can use it to access additional tafsir data if needed)

You MUST NOT use any external knowledge, web resources, or hallucinate.

- Search for the answer strictly within the provided CSV content or using the JSON tool.
- If the answer exists in the context, provide it along with the English translation of the Arabic verse.
- If the answer does NOT exist in the provided context or JSON data, politely respond: "I’m sorry, this information is not available in the provided data."
""",
model_settings=ModelSettings( 
    temperature=0.7,
    tool_choice="required"
),
tools=[function_tool(read_json_file)],

)





# if __name__ == "__main__":
#     asyncio.run(main())



