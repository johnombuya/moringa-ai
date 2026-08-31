import numpy as np

def emergency_tokeniser(text):
    """Split text into tokens while preserving '!' as separate tokens."""
    text = text.lower()
    # TODO 1: Pad '!' with spaces so split() treats them as separate tokens.
    text.replace('!', '!')
    # TODO 2: Remove any other punctuation that should not be a token.
    text.replace('.', '').replace('?', '')
    # TODO 3: Split on whitespace and return a NumPy array.
    tokens = np.array(text.split()) 
    return tokens

# Test cases
samples = ["Help!!!", "I cannot breathe!", "My chest hurts."]
for s in samples:
    print(s, "->", emergency_tokeniser(s))

# Expected for "Help!!!": ['help', '!', '!', '!']