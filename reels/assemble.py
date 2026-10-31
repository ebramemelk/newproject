#!/usr/bin/env python3
"""Assemble each reel: 5 shot clips + voice-over + burned-in Arabic captions.

Expected clips (from Kling/Runway): reels/clips/<reel_id>/shot1.mp4 ... shot5.mp4
Missing clips are replaced by flat placeholder colours (cool blue -> gold) so
the timing and captions can be checked before the art exists.

Shot timing follows the dialogue (timeline.json from tts.py):
  shot1  close-up praying     0            -> end of line 1
  shot2  pull-back reveal     end line 1   -> end of line 2 (first reply)
  shot3  Youssef turns        end line 2   -> end of line 3
  shot4  Jesus close-up       end line 3   -> end of line 4 (verse)
  shot5  golden wide + fade   end line 4   -> + TAIL_SEC

Output: reels/out/<reel_id>/<reel_id>.mp4 (1080x1920, 30 fps, H.264/AAC).
Exits non-zero if any reel falls outside 20-25 s.

Usage: python3 reels/assemble.py [reel_id ...]
"""
import json
import subprocess
import sys

from common import (CLIPS, FONTS, MAX_SEC, MIN_SEC, TAIL_SEC, load_scripts,
                    load_timeline, reel_dir)

W, H, FPS = 1080, 1920, 30
FADE_SEC = 2.5
PLACEHOLDER = ["0x1b2a44", "0x2a3a55", "0x4a4a50", "0x8a6a3a", "0xc8962e"]


def shot_bounds(tl):
    ends = [l["end"] for l in tl["lines"]]
    cuts = [0.0] + ends + [tl["speech_end"] + TAIL_SEC]
    return [(cuts[i], cuts[i + 1]) for i in range(5)]


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def assemble(reel):
    d = reel_dir(reel["id"])
    tl = load_timeline(reel["id"])
    bounds = shot_bounds(tl)
    total = bounds[-1][1]

    inputs, chains = [], []
    for i, (a, b) in enumerate(bounds):
        dur = b - a
        clip = CLIPS / reel["id"] / f"shot{i + 1}.mp4"
        if clip.exists():
            inputs += ["-stream_loop", "-1", "-i", str(clip)]
        else:
            print(f"  placeholder for {clip.relative_to(CLIPS.parent)}")
            inputs += ["-f", "lavfi", "-i", f"color=c={PLACEHOLDER[i]}:s={W}x{H}:r={FPS}"]
        chains.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                      f"fps={FPS},setsar=1,trim=duration={dur:.3f},setpts=PTS-STARTPTS[v{i}]")

    ass = str(d / "captions.ass").replace(":", r"\:")
    fonts = str(FONTS).replace(":", r"\:")
    graph = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(5)) + \
        f"concat=n=5:v=1:a=0,fade=t=out:st={total - FADE_SEC:.3f}:d={FADE_SEC}," \
        f"ass='{ass}':fontsdir='{fonts}',format=yuv420p[v];" \
        f"[5:a]apad,atrim=duration={total:.3f},afade=t=out:st={total - FADE_SEC:.3f}:d={FADE_SEC}[a]"

    out = d / f"{reel['id']}.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-i", str(d / "dialogue.wav"),
           "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)

    real = probe_duration(out)
    ok = MIN_SEC <= real <= MAX_SEC
    print(f"{reel['id']}: {real:.2f}s {'OK' if ok else 'OUT OF RANGE (20-25s)'} -> {out}")
    return ok


def main():
    reels = [r for r in load_scripts()["reels"] if len(sys.argv) == 1 or r["id"] in sys.argv[1:]]
    results = [assemble(r) for r in reels]
    if not all(results):
        sys.exit("Some reels are outside 20-25 s: trim Youssef's lines in scripts.json, not Jesus's.")


if __name__ == "__main__":
    main()
