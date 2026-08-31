from transformers import GPT2LMHeadModel, GPT2TokenizerFast
import torch

def compute_perplexity(text: str, model_name: str = "gpt2") -> float:
    # 1. Load tokenizer and model architecture
    tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
    model = GPT2LMHeadModel.from_pretrained(model_name)

    # 2. Switch to eval mode (no random dropout)
    model.eval()

    # 3. Convert text to tensor IDs
    encodings = tokenizer(text, return_tensors="pt")
    input_ids = encodings.input_ids

    # 4. Sliding window parameters
    max_length = model.config.n_positions
    stride = 512
    nlls = []
    prev_end = 0

    # 5. Loop through the text in chunks
    for begin_loc in range(0, input_ids.size(1), stride):
        end_loc = min(begin_loc + max_length, input_ids.size(1))
        trg_len = end_loc - prev_end
        ids_win = input_ids[:, begin_loc:end_loc]

        target_ids = ids_win.clone()
        # Mask historical tokens so they aren't scored twice
        target_ids[:, :-trg_len] = -100

        with torch.no_grad():
            outputs = model(ids_win, labels=target_ids)
            nlls.append(outputs.loss)

        prev_end = end_loc
        if end_loc == input_ids.size(1):
            break

    # 6. Return the exponentiated average loss
    return torch.exp(torch.stack(nlls).mean()).item()

if __name__ == "__main__":
    # Runnable demo - no API key needed. The first run downloads the small gpt2 model.
    in_distribution  = "The patient has a persistent dry cough and a low-grade fever lasting two weeks."
    out_distribution = "xkcd zphqr blorf 2931 asdfgh qwerty zzx clinic table mauve"

    ppl_good = compute_perplexity(in_distribution)
    ppl_bad  = compute_perplexity(out_distribution)
    print(f"In-distribution clinical text : perplexity = {ppl_good:.2f}")
    print(f"Out-of-distribution gibberish : perplexity = {ppl_bad:.2f}")
    print("Lower perplexity = the model finds the text predictable and in-domain.")