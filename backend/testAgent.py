import os
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain.messages import HumanMessage

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"


model = ChatGroq(
    api_key = "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", 
    model = "llama-3.1-8b-instant",
    temperature = 0,
    
)
agent = create_agent(model, tools=[search, get_weather])


response = agent.invoke({"messages": [HumanMessage("What is the weather in San Fransisco?")]})

print("Response", response)