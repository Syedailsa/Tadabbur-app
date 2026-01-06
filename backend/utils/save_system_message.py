from utils.generate_short_id import generate_short_id

def save_system_message_to_db(session_id: str, message: str, unique_message_ids: set = None, supabase_client = None):
    # save system message in db
    try:
        # make a unique message_id
        dynamic_system_message_id = generate_short_id()
        while dynamic_system_message_id in unique_message_ids:
            dynamic_system_message_id = generate_short_id()
            unique_message_ids.add(dynamic_system_message_id)
        supabase_client.table('chat_messages').insert({
            "message_id": dynamic_system_message_id,
            "session_id": session_id,
            "role": "system",
            "message": message,
        }).execute()
        print("✅ System message saved successfully!")
    except Exception as e:
        print("Some error occured while inserting System messages", e)

