"""Shared paths, script loading and WAV helpers for the reels pipeline."""
import json
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts.json"
OUT = ROOT / "out"
CLIPS = ROOT / "clips"
FONTS = ROOT / "fonts"

SAMPLE_RATE = 24000  # Gemini TTS returns 16-bit mono PCM at 24 kHz
GAP_SEC = 0.45       # silence between dialogue lines
LEAD_SEC = 0.3       # silence before the first line
TAIL_SEC = 3.0       # golden wide shot + fade to black after the last line
MIN_SEC, MAX_SEC = 20.0, 25.0


def load_scripts():
    return json.loads(SCRIPTS.read_text(encoding="utf-8"))


def reel_dir(reel_id):
    d = OUT / reel_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_wav(path, pcm, rate=SAMPLE_RATE):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def read_pcm(path):
    with wave.open(str(path), "rb") as w:
        return w.readframes(w.getnframes())


def wav_duration(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def silence(sec):
    return b"\x00\x00" * int(sec * SAMPLE_RATE)


def load_timeline(reel_id):
    return json.loads((OUT / reel_id / "timeline.json").read_text(encoding="utf-8"))
