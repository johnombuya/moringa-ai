"""search.py — Text-to-image retrieval using a pre-built CLIP index.

Loads image_index.pkl (built by build_index.py) and exposes a
search(query, top_k) function that returns ranked results above a
documented similarity threshold.

Threshold justification
-----------------------
CLIP cosine similarities for health-education images typically range
between 0.15 and 0.40 for relevant matches.  Scores below 0.20 are
nearly always irrelevant (generic object-level overlap, not topical
relevance).  We set MIN_SIMILARITY = 0.20 to filter noise while
retaining genuinely related posters.  This value was validated
empirically: a query such as "malaria prevention" returns the malaria
poster at ~0.30 and unrelated topics below 0.22.

Usage:
    from search import search
    results = search('malaria prevention', top_k=3)
    for path, score in results:
        print(f'{score:.3f}  {path}')
"""
import os
import torch
import open_clip
import pickle

# ── Device selection ────────────────────────────────────────────────
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# ── Load CLIP model ─────────────────────────────────────────────────
model, _, _ = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='openai')
tokenizer = open_clip.get_tokenizer('ViT-B-32')
model = model.to(device).eval()

# ── Load index ──────────────────────────────────────────────────────
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image_index.pkl')
with open(INDEX_PATH, 'rb') as f:
    index = pickle.load(f)

# ── Similarity threshold ───────────────────────────────────────────
# See docstring above for justification.
MIN_SIMILARITY = 0.20


def search(query_text: str, top_k: int = 3) -> list[tuple[str, float]]:
    """Return up to *top_k* (path, score) pairs above MIN_SIMILARITY.

    If no image exceeds the threshold, returns an empty list and prints
    a notice.
    """
    with torch.no_grad():
        tokens = tokenizer([query_text]).to(device)
        query_vec = model.encode_text(tokens)
        query_vec = query_vec / query_vec.norm(dim=-1, keepdim=True)

    similarities = (index['vectors'] @ query_vec.T.cpu()).squeeze(1)
    top = similarities.topk(min(top_k, len(index['paths'])))

    results = []
    for score, idx in zip(top.values, top.indices):
        sc = float(score)
        if sc >= MIN_SIMILARITY:
            results.append((index['paths'][idx], sc))

    if not results:
        print(f'No images above threshold ({MIN_SIMILARITY}) for query: '
              f'"{query_text}"')

    return results


if __name__ == '__main__':
    print('--- Search: "malaria prevention" ---')
    for path, score in search('a poster about mosquito nets and malaria prevention'):
        print(f'  {score:.3f}  {os.path.basename(path)}')

    print()
    print('--- Search: "nutrition for children" ---')
    for path, score in search('nutrition and feeding for children'):
        print(f'  {score:.3f}  {os.path.basename(path)}')
