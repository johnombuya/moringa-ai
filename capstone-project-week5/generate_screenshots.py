"""generate_screenshots.py — Render representative Gradio UI screenshots for documentation."""
import os
from PIL import Image, ImageDraw

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def create_gradio_mockup(title: str, subtitle: str, left_header: str, left_info: str, right_header: str, right_content: str, output_path: str):
    width, height = 1100, 680
    img = Image.new("RGB", (width, height), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Top App Header Bar
    draw.rectangle([(0, 0), (width, 80)], fill=(15, 23, 42))
    draw.text((40, 18), "AfyaPlus Multimodal Intake Assistant", fill=(255, 255, 255))
    draw.text((40, 48), "Operational triage tool for health clinic workers | Coursework Demo", fill=(148, 163, 184))

    # Banner / Subtitle Card
    draw.rounded_rectangle([(40, 95), (width - 40, 145)], radius=6, fill=(238, 242, 255), outline=(199, 210, 254), width=1)
    draw.text((55, 110), subtitle, fill=(55, 48, 163))

    # Two column layout
    col_width = (width - 110) // 2
    top_y = 165
    card_h = 475

    # Left Card: Input
    left_x1, left_y1 = 40, top_y
    left_x2, left_y2 = 40 + col_width, top_y + card_h
    draw.rounded_rectangle([(left_x1, left_y1), (left_x2, left_y2)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.rectangle([(left_x1, left_y1), (left_x2, left_y1 + 42)], fill=(241, 245, 249))
    draw.text((left_x1 + 16, left_y1 + 12), left_header, fill=(30, 41, 59))

    # Left content box (e.g. uploaded item display)
    draw.rounded_rectangle([(left_x1 + 16, left_y1 + 58), (left_x2 - 16, left_y1 + 280)], radius=6, fill=(248, 250, 252), outline=(203, 213, 225), width=1)
    lines = left_info.split('\n')
    cur_y = left_y1 + 80
    for line in lines:
        draw.text((left_x1 + 30, cur_y), line, fill=(71, 85, 105))
        cur_y += 24

    # Submit Button
    btn_y1 = left_y2 - 65
    draw.rounded_rectangle([(left_x1 + 16, btn_y1), (left_x2 - 16, btn_y1 + 45)], radius=6, fill=(234, 88, 12))
    draw.text((left_x1 + col_width // 2 - 40, btn_y1 + 14), "Submit File", fill=(255, 255, 255))

    # Right Card: Output
    right_x1, right_y1 = left_x2 + 30, top_y
    right_x2, right_y2 = width - 40, top_y + card_h
    draw.rounded_rectangle([(right_x1, right_y1), (right_x2, right_y2)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.rectangle([(right_x1, right_y1), (right_x2, right_y1 + 42)], fill=(241, 245, 249))
    draw.text((right_x1 + 16, right_y1 + 12), right_header, fill=(30, 41, 59))

    # Output text area
    draw.rounded_rectangle([(right_x1 + 16, right_y1 + 58), (right_x2 - 16, right_y2 - 20)], radius=6, fill=(254, 254, 254), outline=(226, 232, 240), width=1)
    
    out_lines = right_content.split('\n')
    r_cur_y = right_y1 + 72
    for line in out_lines:
        if "DISCLAIMER" in line or "is for informational purposes only" in line:
            draw.text((right_x1 + 28, r_cur_y), line, fill=(185, 28, 28))
        elif line.startswith("---") or line.startswith("["):
            draw.text((right_x1 + 28, r_cur_y), line, fill=(15, 23, 42))
        else:
            draw.text((right_x1 + 28, r_cur_y), line, fill=(51, 65, 85))
        r_cur_y += 20
        if r_cur_y > right_y2 - 30:
            break

    img.save(output_path, "PNG")
    print(f"Generated {output_path}")

def main():
    # 1. Image Screenshot
    image_right_content = (
        "[Image Caption]\n\n"
        "The image is an educational health poster promoting malaria prevention\n"
        "using insecticide-treated bed nets (ITNs).\n"
        "Key visible text: 'SLEEP UNDER A NET - PROTECT YOUR FAMILY'.\n\n"
        "This description is for informational purposes only and is not a medical\n"
        "diagnosis. Please consult an AfyaPlus clinician for assessment.\n\n"
        "--- Similar Images in Index ---\n"
        "  0.375  poster_01_malaria_prevention.jpg\n"
        "  0.298  poster_09_hiv_testing.jpg\n"
        "  0.281  poster_05_hygiene.jpg"
    )
    create_gradio_mockup(
        title="AfyaPlus Intake - Image Mode",
        subtitle="Upload: Image file (.jpg, .png) -> Caption + Similar Indexed Posters",
        left_header="Upload Image or Audio File",
        left_info="[File Uploaded: clear.jpg]\nType: Image (JPEG)\nSize: 1024 x 1024\nStatus: Upload complete (Ready)",
        right_header="AfyaPlus Assistant Output",
        right_content=image_right_content,
        output_path=os.path.join(SCREENSHOTS_DIR, "gradio_image_result.png")
    )

    # 2. Audio Screenshot
    audio_right_content = (
        "[Audio Transcript - detected language: en]\n\n"
        "Patient Jane Doe, 34 years old, presenting at Kisumu Central clinic\n"
        "with headache and mild fever for two days. Urgency: routine.\n\n"
        "--- Extracted Intake Fields ---\n"
        "{\n"
        '  "patient_name": "Jane Doe",\n'
        '  "age": 34,\n'
        '  "symptoms": ["headache", "fever"],\n'
        '  "clinic_location": "Kisumu Central",\n'
        '  "urgency": "routine",\n'
        '  "recommended_action": "Consult clinic triage nurse; monitor vitals."\n'
        "}"
    )
    create_gradio_mockup(
        title="AfyaPlus Intake - Audio Mode",
        subtitle="Upload: Voice note (.wav, .mp3) -> Whisper Transcript + Structured JSON",
        left_header="Upload Image or Audio File",
        left_info="[File Uploaded: sample_voice_note.wav]\nType: Audio (WAV)\nDuration: 00:06\nStatus: Upload complete (Ready)",
        right_header="AfyaPlus Assistant Output",
        right_content=audio_right_content,
        output_path=os.path.join(SCREENSHOTS_DIR, "gradio_audio_result.png")
    )

if __name__ == '__main__':
    main()
