import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Literal
from prompts.trait_classification_instructions import system_instructions

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_AI_API_KEY')
if not GROQ_API_KEY:
    raise ValueError('GROQ API KEY not found in environment')


model = ChatGroq(
    api_key = GROQ_API_KEY,
    model = "openai/gpt-oss-120b",
    temperature = 0
)

class TraitSchema(BaseModel):
    category: Literal["Content", "Tone", "Format", "Safety", "Behavioral"] = Field(description = "The category of the trait")
    trait: str = Field(description = "The trait of the LLM's response")

class OutputSchema(BaseModel):
    all_traits: List[TraitSchema] = Field(description = "List of the traits of the LLM's response")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_instructions),
    ("human", "User Feedback:{user_feedback} \n Assistant Response: {assistant_response}" )
])

model_with_structured_output = model.with_structured_output(schema = OutputSchema, method='json_schema')

trait_classifier = prompt | model_with_structured_output


