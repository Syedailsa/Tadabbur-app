from langchain.tools import tool
from tadabbur_agents.story_agent import story_agent

@tool
def story_agent_tool(query: str) -> str:
    """
    Quran Story Teller Agent
    1. Use ONLY when the user explicitly requests a *story*
    (e.g., "tell me the story of Musa").
    Generates and returns the story based on the query.
    2. Tool Usage Constraint
    You may call tools at most 2 times per user query.
    """
    print(f"Story agent tool called with query: {query}")
    result = story_agent.invoke({"input": query})
    print(f"Story agent result: {result}")

    return result.get("output", str(result))

print("Story agent tool defined.")
