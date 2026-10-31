# ريلز «حوار مع يسوع»: خط الإنتاج

```bash
export GEMINI_API_KEY=...                # من environment، مش في الكود
# اختياري: export GEMINI_TTS_MODEL=...   # لو جوجل غيّرت اسم موديل الـ TTS
python3 reels/tts.py                     # صوت لكل سطر + dialogue.wav + نسخة multi-speaker
python3 reels/captions.py                # captions.ass (محروق) + captions.srt
python3 reels/assemble.py                # MP4 مقاس 1080×1920 + فحص المدة 20–25 ث
```

- السكريبتات في `scripts.json` (غيّر `page_name`). الريل 4 عليه `order: 1` لأنه أقوى هوك.
- كليبات Kling/Runway تتحط في `reels/clips/<reel_id>/shot1.mp4 … shot5.mp4`. لو كليب ناقص بيتحط مكانه لون (أزرق ← دهبي) عشان تقدر تراجع التوقيت.
- اللقطة 2 (zoom out) بتبدأ مع آخر كلمة في صلاة يوسف، فخلّي shot1 وshot2 حركة واحدة متصلة في Kling.
- توقيت الكابشن والفيديو مبني على ملفات السطور (`dialogue.wav`). نسخة الـ multi-speaker للسمع والمقارنة بس.
- `python3 reels/tts.py --mock` بيطلع صوت تجريبي من غير API عشان تختبر الخط كله.
- الخط: Cairo Bold (OFL)، ودمجت فيه الحروف العربي واللاتيني عشان libass يعرضهم صح.
