from transformers import GPT2LMHeadModel, GPT2TokenizerFast
import torch

class InputAuditor:
    def __init__(self, threshold: float = 45.0):
        self.threshold = threshold
        self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
        self.model = GPT2LMHeadModel.from_pretrained("gpt2")
        self.model.eval()

    def calculate_ppl(self, text: str) -> float:
        encodings = self.tokenizer(text, return_tensors="pt")
        input_ids = encodings.input_ids
        with torch.no_grad():
            outputs = self.model(input_ids, labels=input_ids)
            return torch.exp(outputs.loss).item()

    def is_valid_input(self, text: str) -> bool:
        score = self.calculate_ppl(text)
        print(f"[AUDIT LOG] Perplexity: {score:.2f}")
        return score <= self.threshold

if __name__ == "__main__":
    auditor = InputAuditor(threshold=45.0)
    good_prompt = "The patient has been suffering from a continuous dry cough for five days."
    bad_prompt  = "xyz123 blood pressure fever asdfghjk qwerty"

    print("--- Evaluating Good Input ---")
    if auditor.is_valid_input(good_prompt):
        print("RESULT: PASS - Forwarding to LLM pipeline.")
    else:
        print("RESULT: REJECT - Halting to save API budget.")

    print("\n--- Evaluating Corrupted Input ---")
    if auditor.is_valid_input(bad_prompt):
        print("RESULT: PASS - Forwarding to LLM pipeline.")
    else:
        print("RESULT: REJECT - Halting to save API budget.")