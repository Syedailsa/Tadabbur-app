from time import sleep
from langchain.messages import HumanMessage
from tadabbur_agents.title_agent import title_agent

def generate_title_description(conversation_history: list[dict], session_id: str, supabase_client = None):
    if not conversation_history:
        return
    
    if (len(conversation_history) == 2):
        conversation_string = ""
        # build a conversation string from user & assistant messages
        for message in conversation_history:
            if isinstance(message, HumanMessage):
                conversation_string += f"User message: {message['content']} \n"
            else:
                conversation_string += f"Assistant message: {message['content']} \n"
        if conversation_string:
            for gen_attempt in range(10):
                try:
                    agent_response = title_agent.invoke(conversation_string)
                    title = agent_response.title or "Title"
                    description = agent_response.description or "Description of chat session"
                    # insert title and description in session table
                    for db_attempt in range(10):
                        try:
                            print("🔃 Inserting title and description in session record")
                            supabase_client.table('chat_sessions').update({"title": title, "description": description}).eq("session_id", session_id).execute()
                            print("✅ Successfully insert title and description")
                            break
                        except Exception as e:
                            print("Some error occured while inserting title and description in session table", e)
                            print(f"Attempt {db_attempt + 1}/10 failed")
                            sleep(0.1)
                    break
                except Exception as e:
                    print("Some error occured while generating title and description", e)
                    print(f"Attempt {gen_attempt + 1}/10 failed")
                    sleep(0.1)
        else:
            print("No conversation string so not generating title and description.")
    else:
        return