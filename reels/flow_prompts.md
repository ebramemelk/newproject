# Google Flow prompts (same workflow as the AromaTech reels)

1. **Images:** Flow → image mode, **9:16**. Generate the two character sheets first and add them as references (Ingredients) to every shot.
2. **Motion:** Flow → video **Frames** mode. Use each image as the start frame, with the motion prompt.
3. Download the clips into `reels/clips/<reel_id>/shot1.mp4 … shot5.mp4`.
4. Run `split_vo.py`, then `captions.py`, then `assemble.py`.

## Character sheets
```
Character sheet, front / three-quarter / side views on plain warm paper background: a slim young Egyptian man in his mid-20s, tan olive skin, messy short black curly hair, light stubble, tired eyes, oversized olive-green bomber jacket, white t-shirt, dark jeans, white sneakers. [STYLE]
```
```
Character sheet, front / three-quarter / side views on plain warm paper background: Jesus, gentle Middle Eastern man, long dark wavy hair, full dark beard, warm kind eyes, simple off-white linen robe with a woven brown sash, small wooden cross pendant. [STYLE]
```

**[STYLE]**
```
stylized 2D painterly illustration, gouache and textured brushwork, elongated expressive proportions, large expressive dark eyes, visible brush strokes and paper grain, soft cinematic depth of field, warm golden light breaking through cool blue city haze, vertical 9:16, no text
```

## Shots (replace [SETTING] with the setting from scripts.json)
| # | Image prompt | Motion prompt (Frames) |
|---|---|---|
| 1 | Close-up of the young man (reference) alone, eyes closed, praying softly, hands clasped near his chest, [SETTING], cool blue tones. [STYLE] | Very slow push-in, he breathes softly, eyelids tremble, background crowd/haze drifts. Then a smooth continuous dolly back. |
| 2 | Wide shot revealing Jesus (reference) quietly standing right beside the young man, [SETTING], first warm light touching Jesus. [STYLE] | Continuous slow dolly back / zoom out, warm light slowly grows on Jesus, Jesus gently turns his head toward the young man. |
| 3 | Medium shot of the young man opening his eyes and turning to Jesus, surprised and softened, tension leaving his face. [STYLE] | He slowly opens his eyes and turns, shoulders drop as he relaxes, subtle handheld drift. |
| 4 | Close-up of Jesus's face, loving smile, eyes glistening, golden rim light. [STYLE] | Slow push-in, soft smile grows, golden light warms, a gentle blink. |
| 5 | Wide shot, golden light flooding [SETTING], the young man smiling with relief, shoulders relaxed beside Jesus. [STYLE] | Slow pull-back, golden light spreads across the scene, light dust particles float, everything calm. |

**Tip:** make shot 1 → shot 2 with the shot 1 image as the start frame and the shot 2 image as the end frame (Frames mode). You get the zoom-out as one continuous move, so there is no cut.
