"""Generate a simple test WAV audio file containing a synthesised health-worker voice note.

Uses a sine-wave tone (not real speech) as a placeholder. For actual
Whisper testing, replace audio/sample_voice_note.wav with a real recording.
The file is intentionally short to keep API costs near zero.
"""
import struct, wave, math, os

OUT_DIR = os.path.join(os.path.dirname(__file__), 'audio')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'sample_voice_note.wav')

# Parameters
SAMPLE_RATE = 16000
DURATION = 3  # seconds
FREQ = 440    # Hz (A4 note)

samples = []
for i in range(SAMPLE_RATE * DURATION):
    t = i / SAMPLE_RATE
    val = int(16000 * math.sin(2 * math.pi * FREQ * t))
    samples.append(struct.pack('<h', val))

with wave.open(OUT, 'w') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(samples))

print(f'Created {OUT} ({DURATION}s, {SAMPLE_RATE} Hz)')
print('NOTE: Replace this file with a real health-worker voice note for')
print('meaningful Whisper transcription results.')
