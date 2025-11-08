from pydantic import BaseModel
from agents import Agent
import pandas as pd


class Tafsir_Request(BaseModel):
    is_query_valid_or_related_to_context: bool
    reasoning: str
    answer: str

CSV_FILE_PATH= "quran_tafseer_hf.csv"

df = pd.read_csv(CSV_FILE_PATH)
texts = df['surah_name'].tolist()
csv_content = "\n\n".join(texts[:10]) 

instruction = f"""You are Quranic Input Checker Agent that checks if the user query is valid and related to the provided {csv_content} context
     about Quranic Tafseer. If the query is valid and related, respond with is_query_valid_or_related_to_context as true, provide 
     reasoning and the answer based on the context. If not, respond with is_query_valid_or_related_to_context as false, provide 
     reasoning and do not provide an answer.""",

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