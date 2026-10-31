#!/usr/bin/env python3
"""Use a voice-over you recorded yourself (e.g. sawty / Puck) instead of tts.py.

Put one WAV/MP3 per reel in reels/vo/<reel_id>.wav (whole dialogue, all four
lines in order). This finds the three longest pauses, treats them as the line
breaks, and writes out/<reel_id>/dialogue.wav + timeline.json, the same files
tts.py makes, so captions.py and assemble.py work unchanged.

Usage: python3 reels/split_vo.py [reel_id ...]
"""
import json
import re
import subprocess
import sys

from common import ROOT, SAMPLE_RATE, load_scripts, reel_dir, wav_duration

VO = ROOT / "vo"
NOISE_DB = -35
MIN_PAUSE = 0.3


def find_vo(reel_id):
    for ext in ("wav", "mp3", "m4a"):
        p = VO / f"{reel_id}.{ext}"
        if p.exists():
            return p


def silences(path):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                          f"silencedetect=noise={NOISE_DB}dB:d={MIN_PAUSE}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(starts, ends))


def process(reel):
    src = find_vo(reel["id"])
    if not src:
        print(f"{reel['id']}: no file in reels/vo/, skipped")
        return
    d = reel_dir(reel["id"])
    wav = d / "dialogue.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1",
                    "-ar", str(SAMPLE_RATE), "-sample_fmt", "s16", str(wav)], check=True)
    total = wav_duration(wav)

    gaps = silences(wav)
    lead = gaps[0][1] if gaps and gaps[0][0] < 0.05 else 0.0
    tail = gaps[-1][0] if gaps and gaps[-1][1] >= total - 0.05 else total
    inner = [g for g in gaps if g[0] > lead and g[1] < tail]
    n = len(reel["lines"])
    if len(inner) < n - 1:
        sys.exit(f"{reel['id']}: found {len(inner)} pauses, need {n - 1}. "
                 "Leave a clear pause between the lines, or lower NOISE_DB.")
    breaks = sorted(sorted(inner, key=lambda g: g[1] - g[0], reverse=True)[:n - 1])

    bounds = [lead] + [x for g in breaks for x in g] + [tail]
    lines = [{"index": i + 1, "speaker": l["speaker"], "text": l["text"],
              "start": round(bounds[2 * i], 3), "end": round(bounds[2 * i + 1], 3)}
             for i, l in enumerate(reel["lines"])]
    (d / "timeline.json").write_text(json.dumps(
        {"id": reel["id"], "speech_end": round(tail, 3), "lines": lines},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{reel['id']}: " + ", ".join(f"{l['start']:.1f}-{l['end']:.1f}" for l in lines))


def main():
    for reel in load_scripts()["reels"]:
        if len(sys.argv) == 1 or reel["id"] in sys.argv[1:]:
            process(reel)


if __name__ == "__main__":
    main()
