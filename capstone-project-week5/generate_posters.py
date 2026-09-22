"""Generate simple health-poster placeholder images using Pillow.

Run once to fill the images/ folder up to 16 images.
These are solid-colour cards with large centred text — enough
for CLIP to differentiate by topic keyword.
"""
import os
from PIL import Image, ImageDraw, ImageFont

POSTERS = [
    ('poster_12_dental_care.jpg',   'Dental Health\nBrush Twice Daily',    (41, 128, 185)),
    ('poster_13_eye_care.jpg',      'Protect Your Eyes\nGet Regular Checkups', (142, 68, 173)),
    ('poster_14_snake_bite.jpg',    'Snake Bite\nFirst Aid Steps',          (192, 57, 43)),
    ('poster_15_cholera.jpg',       'Prevent Cholera\nDrink Clean Water',   (39, 174, 96)),
    ('poster_16_family_planning.jpg','Family Planning\nAsk Your Health Worker', (230, 126, 34)),
]

OUT_DIR = os.path.join(os.path.dirname(__file__), 'images')
os.makedirs(OUT_DIR, exist_ok=True)

for fname, text, colour in POSTERS:
    img = Image.new('RGB', (600, 800), colour)
    draw = ImageDraw.Draw(img)
    # try to use a readable font; fall back to default
    try:
        font = ImageFont.truetype('arial.ttf', 48)
    except OSError:
        font = ImageFont.load_default()
    # centre the text
    bbox = draw.multiline_textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (600 - w) // 2
    y = (800 - h) // 2
    draw.multiline_text((x, y), text, fill='white', font=font, align='center')
    # add a footer disclaimer
    try:
        small = ImageFont.truetype('arial.ttf', 20)
    except OSError:
        small = ImageFont.load_default()
    draw.text((30, 740), 'AfyaPlus Health Education', fill=(255, 255, 255, 180), font=small)
    img.save(os.path.join(OUT_DIR, fname))
    print(f'Created {fname}')

print(f'Done — {len(POSTERS)} poster images created in {OUT_DIR}/')
