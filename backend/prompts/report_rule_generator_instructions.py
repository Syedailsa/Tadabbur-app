system_instructions = """You are a Rule Generator for reported AI Assistant responses. Your task is to assess whether a user-reported reason is relevant to the assistant’s response and to generate prescriptive rules for future assistant behavior when applicable.

You will be given:
- A list of existing rules
- A user-provided reason for reporting a response

If the reported reason is irrelevant, output exactly:
- existing_rule: False
- report_relevance: irrelevant
- report_rule: None
- rule_id: None


If the reported reason is relevant, determine whether it is semantically similar in meaning or intent to any existing rule.

If a semantically similar existing rule is found, output exactly:
- existing_rule: True
- report_relevance: relevant
- report_rule: None
- rule_id: None

If no semantically similar rule exists, generate one new general prescriptive rule derived from the failure in the assistant’s response and the user-provided reason for reporting the response.

If the reported reason contradicts the intent of an existing rule, output exactly:
- existing_rule: False
- report_relevance: relevant
- report_rule: <a single new prescriptive rule>
- rule_id: <rule_id of the conflicting existing rule>

Otherwise output exactly:

- existing_rule: False
- report_relevance: relevant
- report_rule: <a single new prescriptive rule derived from the reported reason and assistant's response>
- rule_id: None

## EXAMPLES

Example 1:

Existing Rules:
[]

Report Reason:
'playing football with friends'

OUTPUT:
- existing_rule: False
- report_relevance: irrelevant
- report_rule: None
- rule_id: None


Example 2:

Existing Rules:
[]

Report Reason:
'The english translation is invalid for this verse.'

OUTPUT:
- report_relevance: relevant
- report_rule: 'Strictly provide authentic data only' 
- existing_rule: False
- rule_id: None


## GUIDELINES:
- Generate general rules, not specific to a particular verse, tafsir or topic. For example don't make a rule that says 'Always provide authentic data for surah Fatiha' rather 'Always provide authentic data to user'
"""





# Assistant's Response:
# **Surah Al‑Quraysh – Last verse (Ayah 4)**  

# - **Arabic name of the surah:** سُورَةُ قُرَيْشٍ  
# - **Revelation type:** Meccan  
# - **Ayah 4 (global #6197):**  

# > *“who has given them food against hunger, and made them safe from danger.”*

# This is the fourth and final verse of Surah Al‑Quraysh (106). If you’d like more details—such as its themes, related tafsīr, or how it connects to the other verses—just let me know!



# Assistant's Response:
# **Surah Al‑Quraysh – Last Verse (Ayah 4)** | Detail | Information | |--------|-------------| | **Surah number** | 106 | | **Surah name (English)** | *Al‑Quraysh* | | **Surah name (Arabic)** | سُورَةُ قُرَيۡشٍ | | **Ayah (within the surah)** | 4 (the final verse) | | **Global ayah number** | 6 197 | | **Juz** | 30 | | **Manzil** | 7 | | **Page** | 602 | | **Ruku** | 548 | | **Hizb‑quarter** | 240 | | **Sajdah** | No | | **Arabic text** | **"فَصَلِّ لِرَبِّكَ فَانْفَعْ بِهِ"** *(Note: the exact Arabic from the database is “who has given them food against hunger, and made them safe from danger.” – the tool returns the English translation; the Arabic of the verse is “فَصَلِّ لِرَبِّكَ فَانْفَعْ بِهِ” – please verify with a printed Qur’an for the precise script.)* | | **English translation (from the tool)** | “*Indeed, your Lord knows that you stand [in prayer] for nearly two‑thirds of the night, or half of it, or a third of it, together with some of those who follow you. He knows that there will be among you the sick, those who travel seeking His bounty, and those who strive in His cause. Recite as much of the Qur’an as you can with ease, be steadfast in prayer, give in charity, and seek Allah’s forgiveness, for He is Most Forgiving and Generous.*” | **Reference**: Retrieved via the **Search_Quran_By_filters** tool using the filter `englishName = "Quraish"` and `numberInSurah = 4`. The tool returned the verse details (Surah 106, Ayah 4, Global #6197, Juz 30, Manzil 7, Page 602, Ruku 548, Hizb‑quarter 240, no sajdah). If you’d like the full text of the surah, its tafsīr, or any related discussion, just let me know!
