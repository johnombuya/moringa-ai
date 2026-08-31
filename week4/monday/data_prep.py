# The full Monday pipeline: load raw records, format for LLaMA instruction
# tuning, validate every example, and split 80/10/10 into JSONL files.
import json
import os
import random

SYSTEM_PROMPT = """You are the AfyaPlus operational assistant. You help clinicians and patients navigate clinical workflows, appointment scheduling, and internal triage protocols. Your responses must be:
- Precise and aligned with standard operating procedures (SOPs)
- Focused on administrative guidance, such as booking, system navigation, and protocol escalation
- Safety-conscious, always directing patients to appropriate clinical staff for medical diagnostics
- Clear, professional, and empathetic
Do not provide medical diagnoses or treatment plans; instead, guide users to the correct AfyaPlus clinical service or provider."""


# ---------------------------------------------------------------
# STEP 1: Load and check the raw records
# ---------------------------------------------------------------
def load_and_validate_data(file_path: str) -> list:
    with open(file_path, "r") as f:
        data = json.load(f)
    if len(data) < 100:
        raise ValueError("Dataset too small: please provide at least 100 records.")
    return data

# ---------------------------------------------------------------
# STEP 2: Format each record into the LLaMA instruction-tuning shape
# ---------------------------------------------------------------
def format_example(qa: dict) -> dict:
    return {
        "messages": [
            {"role": "system",    "content": SYSTEM_PROMPT},
            {"role": "user",      "content": qa["question"]},
            {"role": "assistant", "content": qa["answer"]},
        ]
    }

def validate_dataset(examples: list) -> dict:
    """
    Validate every example. Checks:
      - Correct message structure (system, user, assistant roles, in order)
      - Non-empty content in all fields
      - Token count within the training range (64 to 2048)
      - No duplicate examples (exact match on user content)
    Returns a report dictionary with counts and any problems found.
    """
    tokenizer = _load_llama_tokenizer()

    errors, warnings = [], []
    seen_questions = set()
    token_counts = []

    for i, example in enumerate(examples):
        msgs = example.get("messages", [])

        if len(msgs) != 3:
            errors.append(f"Example {i}: expected 3 messages, got {len(msgs)}")
            continue

        roles = [m.get("role") for m in msgs]
        if roles != ["system", "user", "assistant"]:
            errors.append(f"Example {i}: wrong role order {roles}")
            continue

        for msg in msgs:
            if not msg.get("content", "").strip():
                errors.append(f"Example {i}: empty content in role '{msg['role']}'")

        user_content = msgs[1]["content"]
        if user_content in seen_questions:
            warnings.append(f"Example {i}: duplicate question '{user_content[:60]}...'")
        seen_questions.add(user_content)

        tokens = count_tokens(msgs, tokenizer)
        token_counts.append(tokens)
        if tokens < 64:
            warnings.append(f"Example {i}: very short ({tokens} tokens)")
        if tokens > 2048:
            errors.append(f"Example {i}: too long ({tokens} tokens), exceeds training context")

    return {
        "total_examples": len(examples),
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "avg_tokens": round(sum(token_counts) / len(token_counts), 1) if token_counts else 0,
        "min_tokens": min(token_counts) if token_counts else 0,
        "max_tokens": max(token_counts) if token_counts else 0,
        "valid_examples": len(examples) - len(errors),
    }

# ---------------------------------------------------------------
# STEP 4: Shuffle, split 80/10/10, and save as JSONL
# ---------------------------------------------------------------
def split_and_save(examples: list, output_dir: str = "data") -> None:
    """JSONL = one JSON object per line, the format Hugging Face datasets expects."""
    os.makedirs(output_dir, exist_ok=True)

    random.seed(42)  # Fixed seed: the same split every run, essential for debugging
    shuffled = examples[:]
    random.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * 0.80)
    n_val = int(n * 0.10)

    splits = [
        ("train", shuffled[:n_train]),
        ("val",   shuffled[n_train:n_train + n_val]),
        ("test",  shuffled[n_train + n_val:]),
    ]
    for split_name, split_data in splits:
        path = f"{output_dir}/{split_name}.jsonl"
        with open(path, "w") as f:
            for ex in split_data:
                f.write(json.dumps(ex) + "\n")
        print(f"Saved {len(split_data)} examples to {path}")

    print(f"\nSplit summary: {len(splits[0][1])} train | {len(splits[1][1])} val | {len(splits[2][1])} test")

# ---------------------------------------------------------------
# STEP 5: Run the whole pipeline end-to-end
# ---------------------------------------------------------------
if __name__ == "__main__":
    raw_data = load_and_validate_data("operational_data.json")
    formatted_data = [format_example(record) for record in raw_data]
    print(f"Formatted {len(formatted_data)} examples")

    report = validate_dataset(formatted_data)
    print("\n=== DATASET VALIDATION REPORT ===")
    print(f"Total examples:  {report['total_examples']}")
    print(f"Valid examples:  {report['valid_examples']}")
    print(f"Errors:          {report['error_count']}")
    print(f"Warnings:        {report['warning_count']}")
    print(f"Avg token count: {report['avg_tokens']}")
    print(f"Token range:     {report['min_tokens']} to {report['max_tokens']}")

    for e in report["errors"]:
        print(f"  ERROR: {e}")
    for w in report["warnings"]:
        print(f"  WARN:  {w}")

    if report["error_count"] == 0:
        split_and_save(formatted_data)
        print("\nDataset preparation complete. Ready to upload to Nebius.")
    else:
        print("\nFix the errors above before splitting. Do not train on a broken dataset.")