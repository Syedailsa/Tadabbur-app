from tadabbur_agents.report_rule_generator import report_rule_generator

def insert_report_rule(supabase_client, message_id: str, feedback:str):
    for i in range(8):
        try:
            print("Inserting hard rule...")
            # first fetch existing rules
            existing_rules = supabase_client.table('chat_rules').select("rule_id", "rule").eq("hard_rule", True).execute().data

            print("All existing hard rules", existing_rules)
            
            response = report_rule_generator.invoke({"existing_rules": existing_rules, "report_reason": feedback})

            existing_rule = response.existing_rule
            if existing_rule:
                print("Similar in intent rule already exists, returning...")
                response_data = {
                    "type": "report",
                    "message_id": message_id,
                    "status": "acknowledged"
                }
                return response_data 
            else:
                report_relevance = response.report_relevance
                if report_relevance == "relevant":
                    rule = response.report_rule
                    rule_id = response.rule_id

                    if not rule:
                        print("No rule, returning...")
                        response_data = {
                        "type": "report",
                        "status": "not-acknowledged"
                        }
                        return response_data
                    if rule_id:
                        # first delete the conflicting rule
                        supabase_client.table('chat_rules').delete().eq("rule_id", rule_id).execute()
                else:
                    print("Report reason not valid")
                    response_data = {
                        "type": "report",
                        "status": "not-acknowledged"
                        }
                    return response_data
            
            # insert hard rule
            supabase_client.table('chat_rules').insert({"rule": rule, "hard_rule": True, "message_id": message_id}).execute()
            print(f"Message with {message_id} is successfully reported!")
            response_data = {
                "type": "report",
                "status": "acknowledged",
                "message_id": message_id
            }
            return response_data # success
            
        except Exception as e:
            print("Some error occurred while inserting a hard rule:", e)
            print(f"Trying again, total tries {i+1}/8")
            last_error = e

    raise RuntimeError(
        f"Failed to insert hard rule after 8 attempts"
    ) from last_error


def delete_report_rule(supabase_client, message_id:str):
    # insert rule in the feedback system
    for i in range(8):
        try:
            print("Deleting hard rule...")
            supabase_client.table('chat_rules').delete().eq("message_id", message_id).execute()
            print(f"✅ Hard rule with message_id {message_id} deleted successfully!")
            return  # Success, return 
        except Exception as e:
            print("Some error occurred deleting the hard rule:", e)
            print(f"Trying again, total tries {i+1}/8")
            last_error = e
    
    raise RuntimeError(
        f"Failed to delete hard rule after 8 attempts"
    ) from last_error
