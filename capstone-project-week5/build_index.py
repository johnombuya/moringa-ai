"""build_index.py — Build a CLIP retrieval index over health-domain images.

Scans the images/ folder, encodes every .jpg/.jpeg/.png with CLIP ViT-B-32,
and saves the normalised image vectors + file paths into image_index.pkl.

Usage:
    python build_index.py
"""
import os
import torch
import open_clip
import pickle
from PIL import Image

# ── Device selection ────────────────────────────────────────────────
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# ── Load CLIP model (weights download on first run) ─────────────────
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='openai')
model = model.to(device).eval()

# ── Locate images ───────────────────────────────────────────────────
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
if not os.path.isdir(IMAGE_DIR):
    print(f'Folder not found: {IMAGE_DIR}/')
    raise SystemExit(1)

SUPPORTED = ('.jpg', '.jpeg', '.png')
image_paths = sorted([
    os.path.join(IMAGE_DIR, f)
    for f in os.listdir(IMAGE_DIR)
    if f.lower().endswith(SUPPORTED)
])

if len(image_paths) < 15:
    print(f'WARNING: Only {len(image_paths)} images found — the rubric requires ≥15.')

# ── Encode images ───────────────────────────────────────────────────
image_vectors = []
valid_paths = []

with torch.no_grad():
    for path in image_paths:
        try:
            image = Image.open(path).convert('RGB')
            img_tensor = preprocess(image).unsqueeze(0).to(device)
            vec = model.encode_image(img_tensor)
            vec = vec / vec.norm(dim=-1, keepdim=True)   # L2-normalise
            image_vectors.append(vec.cpu())
            valid_paths.append(path)
        except Exception as e:
            print(f'Skipping {path}: {e}')

if not image_vectors:
    print('No images were successfully encoded.')
    raise SystemExit(1)

image_vectors = torch.cat(image_vectors, dim=0)

# ── Save index ──────────────────────────────────────────────────────
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image_index.pkl')
with open(INDEX_PATH, 'wb') as f:
    pickle.dump({'paths': valid_paths, 'vectors': image_vectors}, f)

print(f'Indexed {len(valid_paths)} images into {INDEX_PATH}')
