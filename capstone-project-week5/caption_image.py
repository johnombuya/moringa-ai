"""caption_image.py — GPT-4o vision captioning with safety constraints.

Provides a constrained image captioner for the AfyaPlus health domain.
Every response includes a mandatory clinical disclaimer.

Handles three classes of input:
  1. CLEAR    — sharp, health-relevant image → factual description + disclaimer
  2. AMBIGUOUS — blurry or unclear image → "image is unclear" + human-review flag
  3. OUT-OF-SCOPE — non-health image → polite refusal + disclaimer

Usage:
    from caption_image import caption_image
    print(caption_image('test_images/clear.jpg'))
"""
import os
import base64
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Support both direct OpenAI and proxy endpoints (e.g. OpenRouter)
_base_url = os.getenv('OPENAI_BASE_URL')
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    **({'base_url': _base_url} if _base_url else {}),
)

# ── Safety constants ────────────────────────────────────────────────
DISCLAIMER = (
    'This description is for informational purposes only and is not a '
    'medical diagnosis. Please consult an AfyaPlus clinician for assessment.'
)

SYSTEM_PROMPT = f"""You are the AfyaPlus image captioning assistant.
You describe images submitted by patients or community health workers
in clear, factual, non-diagnostic language.

Rules you must always follow:
- Describe only what is visibly present (colour, location, size, texture).
- Never state or imply a medical diagnosis, condition name, or severity.
- Never recommend a specific medication or treatment.
- If the image is unclear, blurry, or unreadable, respond with:
  "HUMAN REVIEW REQUIRED — The uploaded image is too unclear for a reliable
  description. Please retake the photo in better lighting and resubmit."
  Then still append the disclaimer.
- If the image is obviously not health-related (landscapes, food, pets, etc.),
  respond with:
  "This image does not appear to be health-related. The AfyaPlus intake
  assistant is designed for health documentation only."
  Then still append the disclaimer.
- Always end your response with exactly this sentence:
  '{DISCLAIMER}'
"""


def encode_image(path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def caption_image(image_path: str) -> str:
    """Send an image to GPT-4o and return a safe, constrained caption.

    The response always ends with the DISCLAIMER string.
    """
    b64 = encode_image(image_path)

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': [
                {'type': 'text',
                 'text': 'Describe this image for our clinical operations log.'},
                {'type': 'image_url', 'image_url': {
                    'url': f'data:image/jpeg;base64,{b64}'}},
            ]},
        ],
        max_tokens=300,
        temperature=0.2,
    )

    caption = response.choices[0].message.content

    # Safety net: guarantee the disclaimer is always present
    if DISCLAIMER not in caption:
        caption = caption.rstrip() + '\n\n' + DISCLAIMER

    return caption


if __name__ == '__main__':
    import sys
    test_path = sys.argv[1] if len(sys.argv) > 1 else 'test_images/clear.jpg'
    print(caption_image(test_path))
