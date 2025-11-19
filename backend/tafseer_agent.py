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
from typing import Optional
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


external_client = AsyncOpenAI(
    api_key= FIRE_WORKS_API,
    base_url= Base_URL
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


Tafsir_Agent: Agent = Agent(
name="QuranicTafsirAgent",
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
