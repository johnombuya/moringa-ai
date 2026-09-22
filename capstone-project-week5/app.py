"""app.py — Gradio application for the AfyaPlus Multimodal Intake Assistant.

A single unified interface that accepts an image OR an audio file and
routes it through the appropriate processing pipeline via router.py.

Launch:
    python app.py
    # Then open the printed local URL in your browser.
"""
import gradio as gr
from router import process_input


def handle_upload(file):
    """Handle a file upload from the Gradio interface."""
    if file is None:
        return 'Please upload an image or audio file to get started.'
    return process_input(file)


# ── Gradio Interface ────────────────────────────────────────────────
demo = gr.Interface(
    fn=handle_upload,
    inputs=gr.File(
        label='Upload a patient image or a health-worker voice note',
        file_types=['image', 'audio'],
        type='filepath',
    ),
    outputs=gr.Textbox(
        label='AfyaPlus Assistant Output',
        lines=15,
    ),
    title='AfyaPlus Multimodal Intake Assistant',
    description=(
        'Upload an image (photo, poster, or medication label) for a safe, '
        'non-diagnostic description, or upload an audio file (voice note) '
        'for an automatic transcript with extracted patient details. '
        'All image descriptions include a mandatory clinical disclaimer. '
        'This tool is for informational and operational purposes only.'
    ),
    flagging_mode='never',
)


if __name__ == '__main__':
    demo.launch()
