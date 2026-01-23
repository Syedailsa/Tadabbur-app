import asyncio
from config.db import get_supabase_client
from collections import defaultdict

def group_by_category(system_rules):
    grouped_by_category = defaultdict(list)

    for item in system_rules:
        grouped_by_category[item['category']].append({
            "text": item['rule'],
            "hard_rule": item['hard_rule']
        })

    result = []
    for category, rules in grouped_by_category.items():
        result.append({
            "category": category,
            "rules": rules
        })

    return result


async def refresh_system_instructions(state: dict):
    while True:
        try:
            supabase_client = get_supabase_client()
            # fetch those rules whose weight exceeds 0.8 and build the dynamic system instructions
            system_rules = supabase_client.table('chat_rules').select('rule','category', 'hard_rule').or_("weight.gte.0.7,hard_rule.eq.True").execute().data
            print("Refreshing system instructions")
            dynamic_system_instruction_string = ""
            if system_rules:
                system_rules = group_by_category(system_rules)
                
                hard_rules = []
                # iterate and build strict guidelines
                for record in system_rules:
                    for rule in record['rules']:
                        rule_text = rule["text"]
                        if rule['hard_rule']:
                            hard_rules.append(rule['text'])
                if hard_rules:                
                    dynamic_system_instruction_string += "## STRICT RULES\n\n"
                    for i, rule in enumerate(hard_rules,1):
                        dynamic_system_instruction_string += f"{i}. {rule} \n"
                        
                
                soft_rules = []
                # now build soft guidelines
                for record in system_rules:
                    category = record["category"]
                    rules = record["rules"]
                    
                    category_rules = []
                    for rule in rules:
                        rule_text = rule['text']
                        hard_rule = rule["hard_rule"]
                        if not hard_rule:
                            category_rules.append(rule_text)    
                    if category_rules:
                        soft_rules.append({
                            "category": category,
                            "rules": category_rules
                        }) 

                if soft_rules:
                    dynamic_system_instruction_string += f"\n ## GUIDELINES \n"
                    for record in soft_rules:
                            dynamic_system_instruction_string += f"\n {record['category']}_Rules \n"
                            for i,rule in enumerate(record['rules'], 1):
                                dynamic_system_instruction_string += f'{i}. {rule} \n'
                    
            state["text"] = dynamic_system_instruction_string        
        except Exception as e:
            print("Some error occured while building system instructions", e)
        
        await asyncio.sleep(120)  # 2 minutes
