#!/usr/bin/env python3
"""Generate voice-over for each reel with Gemini TTS.

For every reel it writes to out/<reel_id>/:
  line_01_youssef.wav ...   one file per line (single-speaker call, for editing)
  dialogue.wav              the per-line files joined with fixed gaps (used for
                            captions + final video, so timings are exact)
  dialogue_multispeaker.wav one multi-speaker take of the whole dialogue
  timeline.json             start/end of each line inside dialogue.wav

Usage:
  export GEMINI_API_KEY=...            # never hard-code the key
  python3 reels/tts.py                 # all reels
  python3 reels/tts.py reel1_loneliness --skip-multi
  python3 reels/tts.py --mock          # offline placeholder audio for testing

The model name comes from GEMINI_TTS_MODEL (default below). Check the current
TTS model ID at https://ai.google.dev/gemini-api/docs/speech-generation and
override the env var if Google has renamed it.
"""
import argparse
import base64
import json
import math
import os
import struct
import sys
import time
import urllib.error
import urllib.request

from common import (GAP_SEC, LEAD_SEC, SAMPLE_RATE, load_scripts, read_pcm,
                    reel_dir, silence, wav_duration, write_wav)

MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

DIRECTION = """اقرأ الحوار ده باللهجة المصرية العامية، مش فصحى.
يوسف: شاب مصري تعبان ومكسوف، بيتكلم بصوت واطي ومكسور كأنه بيصلي، وبيهدى تدريجيًا لحد ما يبقى مرتاح في الآخر.
يسوع: هادي جدًا ودافي وبطيء، فيه ابتسامة في صوته، من غير أي نبرة وعظ. الآية تتقال أبطأ وبحنية.
«...» معناها سكتة نص ثانية تقريبًا."""

# Latin labels for the multi-speaker config; the API matches them against the
# "Name:" prefixes in the prompt text.
SPEAKER_TAGS = {"youssef": "Youssef", "jesus": "Jesus"}


def call_tts(prompt, speech_config, api_key, retries=4):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": speech_config},
    }
    req = urllib.request.Request(
        ENDPOINT.format(MODEL),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            return base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            if e.code in (429, 500, 503) and attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            sys.exit(f"TTS error {e.code}: {msg}")
        except (KeyError, IndexError):
            sys.exit(f"Unexpected TTS response: {json.dumps(data)[:500]}")


def voice(name):
    return {"prebuiltVoiceConfig": {"voiceName": name}}


def mock_pcm(text, speaker):
    """Soft tone whose length tracks the text, so the pipeline runs offline."""
    sec = 0.5 + 0.075 * len(text) + 0.4 * text.count("...")
    freq = 180 if speaker == "youssef" else 130
    n = int(sec * SAMPLE_RATE)
    return b"".join(
        struct.pack("<h", int(2500 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
                              * min(1, i / 2400, (n - i) / 2400)))
        for i in range(n))


def process(reel, cfg, api_key, mock, skip_multi):
    d = reel_dir(reel["id"])
    voices = cfg["voices"]
    pcm_all, timeline, t = silence(LEAD_SEC), [], LEAD_SEC

    for i, line in enumerate(reel["lines"], 1):
        path = d / f"line_{i:02d}_{line['speaker']}.wav"
        if mock:
            write_wav(path, mock_pcm(line["text"], line["speaker"]))
        elif not path.exists():
            prompt = f"{DIRECTION}\n\n{cfg['speakers'][line['speaker']]}: {line['text']}"
            write_wav(path, call_tts(prompt, {"voiceConfig": voice(voices[line["speaker"]])}, api_key))
        dur = wav_duration(path)
        timeline.append({"index": i, "speaker": line["speaker"], "text": line["text"],
                         "start": round(t, 3), "end": round(t + dur, 3), "file": path.name})
        pcm_all += read_pcm(path)
        t += dur
        if i < len(reel["lines"]):
            pcm_all += silence(GAP_SEC)
            t += GAP_SEC

    write_wav(d / "dialogue.wav", pcm_all)
    (d / "timeline.json").write_text(json.dumps(
        {"id": reel["id"], "speech_end": round(t, 3), "lines": timeline},
        ensure_ascii=False, indent=2), encoding="utf-8")

    multi = d / "dialogue_multispeaker.wav"
    if not (mock or skip_multi or multi.exists()):
        dialogue = "\n".join(f"{SPEAKER_TAGS[l['speaker']]}: {l['text']}" for l in reel["lines"])
        prompt = f"{DIRECTION}\nYoussef = يوسف، Jesus = يسوع.\n\n{dialogue}"
        cfg_multi = {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": SPEAKER_TAGS[k], "voiceConfig": voice(v)} for k, v in voices.items()]}}
        write_wav(multi, call_tts(prompt, cfg_multi, api_key))

    print(f"{reel['id']}: speech {t:.2f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="reel ids (default: all)")
    ap.add_argument("--mock", action="store_true", help="offline placeholder audio")
    ap.add_argument("--skip-multi", action="store_true", help="skip the multi-speaker take")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not (api_key or args.mock):
        sys.exit("Set GEMINI_API_KEY (or use --mock).")

    cfg = load_scripts()
    for reel in cfg["reels"]:
        if not args.ids or reel["id"] in args.ids:
            process(reel, cfg, api_key, args.mock, args.skip_multi)


if __name__ == "__main__":
    main()
