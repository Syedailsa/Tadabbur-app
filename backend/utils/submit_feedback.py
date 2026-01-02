import os
from collections import defaultdict
from tadabbur_agents.trait_classification_agent import trait_classifier
from tadabbur_agents.rule_similarity_checker_generator import rule_similarity_evaluator
from typing import Literal
from config.db import get_supabase_client

def get_rules_grouped_by_category(supabase_client):
    try:
        res = supabase_client.table('chat_rules') \
            .select('rule_id', 'rule', 'category', 'weight') \
            .execute()

        grouped = defaultdict(list)
        if res.data:
            for row in res.data:
                grouped[row['category']].append({
                    "rule_id": row['rule_id'],
                    "rule": row['rule'],
                    "weight": row['weight']
                })

            return [
                {"category": category, "rules": rules}
                for category, rules in grouped.items()
            ]
        else:
            return []

    except Exception as e:
        print('Error fetching rules:', e)
        return []


def submit_feedback(user_feedback:Literal ['like', 'dislike', 'report'], assistant_response:str):

    try:
        # initialize supabase_client
        supabase_client = get_supabase_client()        
        response = trait_classifier.invoke({"user_feedback": user_feedback, "assistant_response": assistant_response})

        all_traits = response.all_traits
        if not all_traits:
            raise ValueError("No traits found")

        categories = get_rules_grouped_by_category(supabase_client)

        for record in all_traits:
            trait_category = record.category
            trait = record.trait

            if not trait_category or not trait:
                raise ValueError("Category or trait is not defined. Can't proceed!")
            
            if categories:
                for row in categories:
                    rules = row['rules']
                    category = row['category']

                    if trait_category == category:
                        response = rule_similarity_evaluator.invoke({"existing_rules": rules, "trait": trait})

                        # insert those with no existing rule using a small weight
                        if response.existing_rule:
                           
                            # if rule exists increase weight by 0.1
                            rule_id = response.rule_id
                            if not rule_id:
                                raise ValueError("No rule_id, can't adjust weight of the existing rule!")
                                
                            print(f"Incrementing weight of rule with rule_id {rule_id}")
                            result = supabase_client.table("chat_rules").select("weight").eq("rule_id", rule_id).limit(1).execute()
                            existing_weight = result.data[0]['weight']
                           
                            if existing_weight >=1 or existing_weight < 0.3:
                                continue
                            if response.weight_increment is True:
                                new_weight = existing_weight + 0.1
                            elif response.weight_increment is False:
                                new_weight = existing_weight - 0.1

                            supabase_client.table("chat_rules").update({"weight": new_weight}).eq("rule_id", rule_id).execute()

                        else:
                            rule = response.new_rule
                            category = response.category
                            if not rule or not category:
                                raise ValueError("No rule and category, can't proceed")
                            # insert a new rule with a small weight
                            supabase_client.table("chat_rules").insert({"rule": rule, "category": category, "weight": 0.3}).execute()


            else:
                # no categories, no rules, insert all
                response = rule_similarity_evaluator.invoke({"existing_rules": [], "trait": trait})
                if not response.existing_rule:
                    category = response.category
                    new_rule = response.new_rule
                    supabase_client.table('chat_rules').insert({"rule": new_rule, "category": category, "weight": 0.3}).execute()
            
    except Exception as error:
        print("Some error occured while submitting feedback", error)
        raise
        
