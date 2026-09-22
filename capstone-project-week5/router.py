"""router.py — Input-routing logic for the AfyaPlus Multimodal Intake Assistant.

Inspects the file extension of an uploaded file and dispatches to the
appropriate pipeline:
  - Image → caption_image() + search() for similar indexed images
  - Audio → transcribe_audio() + extract_fields()
  - Other → friendly error message

Usage:
    from router import process_input
    result = process_input('/path/to/uploaded/file.jpg')
"""
import os
import json
from caption_image import caption_image
from transcribe_audio import transcribe_audio, extract_fields

# ── Supported file types ────────────────────────────────────────────
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}


def _format_search_results(results: list[tuple[str, float]]) -> str:
    """Format CLIP search results as a readable string."""
    if not results:
        return '  No similar images found above threshold.'
    lines = []
    for path, score in results:
        lines.append(f'  {score:.3f}  {os.path.basename(path)}')
    return '\n'.join(lines)


def process_input(file_path: str) -> str:
    """Route an uploaded file to the correct processing pipeline.

    Returns a formatted string with the results, suitable for display
    in the Gradio interface.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # ── Image path ──────────────────────────────────────────────────
    if ext in IMAGE_EXTENSIONS:
        caption = caption_image(file_path)

        # Try to find similar indexed images (optional — graceful if no index)
        search_section = ''
        try:
            from search import search
            results = search(
                'health education poster related to this image', top_k=3)
            if results:
                search_section = (
                    '\n\n--- Similar Images in Index ---\n'
                    + _format_search_results(results)
                )
        except Exception:
            pass  # index not built yet — skip silently

        return f'[Image Caption]\n\n{caption}{search_section}'

    # ── Audio path ──────────────────────────────────────────────────
    elif ext in AUDIO_EXTENSIONS:
        transcript = transcribe_audio(file_path)
        transcript_text = getattr(transcript, 'text', str(transcript))
        detected_lang = getattr(transcript, 'language', 'unknown')

        # Extract structured fields from the transcript
        fields = extract_fields(transcript_text)
        fields_json = json.dumps(fields, indent=2)

        return (
            f'[Audio Transcript - detected language: {detected_lang}]\n\n'
            f'{transcript_text}\n\n'
            f'--- Extracted Intake Fields ---\n{fields_json}'
        )

    # ── Unsupported ─────────────────────────────────────────────────
    else:
        return (
            f'Unsupported file type: {ext}\n\n'
            f'Please upload an image (.jpg, .png) or an audio file '
            f'(.mp3, .wav) for processing.'
        )
