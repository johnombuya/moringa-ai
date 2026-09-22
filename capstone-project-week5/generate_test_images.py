"""Generate 3 test images for captioning evaluation:
  1. clear.jpg    — a sharp, clear health poster (copy from index)
  2. ambiguous.jpg — a deliberately blurry / noisy health image
  3. out_of_scope.jpg — a non-health image (sunset landscape)
"""
import os, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), 'test_images')
os.makedirs(OUT, exist_ok=True)

# 1. Clear — reuse a sharp poster
src = os.path.join(os.path.dirname(__file__), 'images', 'poster_01_malaria_prevention.jpg')
if os.path.exists(src):
    shutil.copy2(src, os.path.join(OUT, 'clear.jpg'))
    print('Created clear.jpg (copy of malaria poster)')
else:
    # fallback: generate a clean card
    img = Image.new('RGB', (600, 800), (0, 100, 180))
    d = ImageDraw.Draw(img)
    d.text((120, 350), 'Malaria Prevention', fill='white')
    img.save(os.path.join(OUT, 'clear.jpg'))
    print('Created clear.jpg (generated fallback)')

# 2. Ambiguous — apply extreme blur + noise
img2 = Image.new('RGB', (600, 800), (120, 120, 120))
draw2 = ImageDraw.Draw(img2)
try:
    font = ImageFont.truetype('arial.ttf', 36)
except OSError:
    font = ImageFont.load_default()
draw2.text((80, 350), 'Health Poster Text', fill=(160, 160, 160), font=font)
img2 = img2.filter(ImageFilter.GaussianBlur(radius=12))
img2.save(os.path.join(OUT, 'ambiguous.jpg'))
print('Created ambiguous.jpg (blurred, unreadable)')

# 3. Out-of-scope — a sunset landscape (nothing health-related)
img3 = Image.new('RGB', (800, 600), (255, 140, 0))
draw3 = ImageDraw.Draw(img3)
# sky gradient
for y in range(300):
    r = int(30 + (225 * y / 300))
    g = int(30 + (110 * y / 300))
    b = int(80 + (0 * y / 300))
    draw3.line([(0, y), (800, y)], fill=(r, g, b))
# ground
draw3.rectangle([(0, 300), (800, 600)], fill=(34, 100, 34))
# sun
draw3.ellipse([(340, 200), (460, 320)], fill=(255, 200, 50))
img3.save(os.path.join(OUT, 'out_of_scope.jpg'))
print('Created out_of_scope.jpg (sunset landscape)')

print('Done — 3 test images ready.')
