import os
from dotenv import load_dotenv
from typing import Literal
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from prompts.rule_similarity_checker_generator import system_instructions
from typing import Optional

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')


prompt = ChatPromptTemplate.from_messages([
    ("system", system_instructions),
    ("human", "Existing rules: {existing_rules} \n trait: {trait}")
])

if not GROQ_API_KEY:
    raise ValueError('GROQ API KEY not found in environment')


class OutputSchema(BaseModel):
    rule_id: Optional[int] = Field("The rule id of the similar rule")
    category: Literal["Content", "Tone", "Format", "Safety", "Behavioral"] = Field(description = "The category of the trait")
    existing_rule: bool = Field("True if a trait matches an existing rule otherwise false")
    weight_increment:Optional[bool] = Field(description = "True if weight should be incremented otherwise false")
    new_rule: Optional[str] = Field(
    default= None,
    description = "New rule in case a trait doesn't match an existing rule"
    )


model = ChatGroq(
    api_key = GROQ_API_KEY,
    model = "openai/gpt-oss-120b",
    temperature = 0
)


model_with_structured_output =  model.with_structured_output(schema = OutputSchema, method = 'json_schema')


rule_similarity_evaluator = prompt | model_with_structured_output