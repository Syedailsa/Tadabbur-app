liked_message_prompt = """Your following response is liked by the user. Responses of these types is appreciated:\n

User Message:
{user_message}

\n

Assistant Response:
{assistant_response}
"""

disliked_message_prompt = """Your following response is disliked by the user. Responses of these types is discouraged:\n

User Message:
{user_message}

\n

Assistant Response:
{assistant_response}
"""

reported_message_prompt = """Your following response is reported by the user.Responses of these types should be COMPLETELY avoided:\n

User Message:
{user_message}

\n

Assistant Response:
{assistant_response}
"""