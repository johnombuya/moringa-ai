SYSTEM_PROMPT = "You are the AfyaPlus operational assistant."

def filter_and_process(qa_list: list) -> list:
    clean_data = []
    keywords = ["critical error", "system lockout", "urgent escalation"]

    for qa in qa_list:
        # 1. Filter: both fields must exist and be non-empty
        if not qa.get("question") or not qa.get("answer"):
            continue
        if "Unknown" in qa["answer"]:
            continue

        # 2. Detect operational urgency
        is_urgent = any(word in qa["question"].lower() for word in keywords)

        # 3. Dynamic prompting
        current_prompt = SYSTEM_PROMPT
        if is_urgent:
            current_prompt += ("\nNOTE: You are in Critical Operations mode; "
                               "prioritise notifying the AfyaPlus administrative "
                               "lead immediately.")
        clean_data.append({"qa": qa, "prompt": current_prompt})
    return clean_data
