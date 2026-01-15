import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from prompts.report_rule_generator_instructions import system_instructions
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal, Optional


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_AI_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ API KEY is missing! Can't Proceed.")


class OutputSchema(BaseModel):
    existing_rule: bool = Field(description = "True if a similar in intent rule exists, otherwise False")
    report_relevance: Literal["relevant", "irrelevant"] = Field(description = "The relevance of the response for the reported content")
    report_rule: Optional[str] = Field(description = "The rule for the reported response") 
    rule_id: Optional[int]
    category: Literal["Content", "Tone", "Format", "Safety", "Behavioral"] = Field(description = "The category of the report rule")


model = ChatGroq(
    api_key = GROQ_API_KEY,
    model = 'openai/gpt-oss-20b',
    temperature = 0,
)
llm = model.with_structured_output(schema = OutputSchema,  method='json_schema')

prompt = ChatPromptTemplate.from_messages([
    ("system", system_instructions),
    ("human", "Existing_Rules: {existing_rules} \n Report_Reason: {report_reason}"
)
])

report_rule_generator = prompt | llm
