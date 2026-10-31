#!/usr/bin/env python3
"""Build burned-in captions (ASS) plus an SRT copy for each reel.

Reads out/<reel_id>/timeline.json (from tts.py), splits each line into chunks
of 2-4 words and spreads the line's duration over the chunks by character
count. Pauses ("...") and punctuation end a chunk early. The first chunk
starts at t=0 so the hook is on screen from the first frame.

Usage: python3 reels/captions.py [reel_id ...]
"""
import re
import sys

from common import TAIL_SEC, load_scripts, load_timeline, reel_dir

MAX_WORDS = 4
BREAK_AFTER = re.compile(r"(\.\.\.|[.،,؟?!:»])$")

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Cairo,82,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,2,5,60,60,0,178
Style: Ref,Cairo,52,&H0080D8FF,&H0080D8FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,1,5,60,60,0,178
Style: Page,Cairo,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,60,60,0,178

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
CAP_POS = r"{\an5\pos(540,1180)}"  # centre, just under the face
REF_POS = r"{\an5\pos(540,1290)}"
PAGE_POS = r"{\an5\pos(540,960)\fad(400,0)}"


def chunk_words(text):
    words = text.replace("...", "... ").split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= MAX_WORDS or (len(cur) >= 2 and BREAK_AFTER.search(w)):
            chunks.append(cur)
            cur = []
    if cur:
        if len(cur) == 1 and chunks and len(chunks[-1]) < MAX_WORDS + 1:
            chunks[-1] += cur  # avoid a lonely one-word chunk
        else:
            chunks.append(cur)
    # a full stop right before a closing » renders in the wrong place under bidi
    return [" ".join(c).replace("... ", "...").replace(".»", "»").strip() for c in chunks]


def cues_for(timeline):
    cues = []
    for n, line in enumerate(timeline["lines"]):
        chunks = chunk_words(line["text"])
        weights = [max(len(c), 4) for c in chunks]
        t, span = line["start"], line["end"] - line["start"]
        for c, w in zip(chunks, weights):
            d = span * w / sum(weights)
            cues.append([t, t + d, c])
            t += d
        # hold the last chunk across the gap so captions never blink off
        if n + 1 < len(timeline["lines"]):
            cues[-1][1] = timeline["lines"][n + 1]["start"]
    cues[0][0] = 0.0  # hook visible from the first frame
    return cues


def ts_ass(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ts_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(reel, page_name):
    tl = load_timeline(reel["id"])
    cues = cues_for(tl)
    total = tl["speech_end"] + TAIL_SEC
    last = tl["lines"][-1]

    ev = [f"Dialogue: 0,{ts_ass(a)},{ts_ass(b)},Cap,,0,0,0,,{CAP_POS}{t}" for a, b, t in cues]
    ev.append(f"Dialogue: 0,{ts_ass(last['start'])},{ts_ass(last['end'] + 1.0)},Ref,,0,0,0,,"
              f"{REF_POS}{reel['verse_ref']}")
    ev.append(f"Dialogue: 1,{ts_ass(total - 2.0)},{ts_ass(total)},Page,,0,0,0,,{PAGE_POS}{page_name}")

    d = reel_dir(reel["id"])
    (d / "captions.ass").write_text(ASS_HEADER + "\n".join(ev) + "\n", encoding="utf-8")
    srt = [f"{i}\n{ts_srt(a)} --> {ts_srt(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1)]
    (d / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"{reel['id']}: {len(cues)} caption cues")


def main():
    cfg = load_scripts()
    for reel in cfg["reels"]:
        if len(sys.argv) == 1 or reel["id"] in sys.argv[1:]:
            build(reel, cfg["page_name"])


if __name__ == "__main__":
    main()
