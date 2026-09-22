#!/usr/bin/env python3
"""
generate_covers_csv.py

Turns scraped tweet metadata into CSVs for Canva Bulk Create.
Generates separate CSVs for video and photo tweets.

Video CSV columns: tweet_id, hook, headline, source
Photo CSV columns: tweet_id, hook, headline, source, content

For photo tweets, the AI receives ALL original photos + screenshot for context.

Setup:
  pip install openai
  Isi DEEPSEEK_API_KEY di file .env (otomatis terbaca)

Usage:
  python3 generate-content/generate_covers_csv.py \
      --json OUTPUT-X/explore/2026-09-22.json \
      --screenshots OUTPUT-X/screenshots/2026-09-22

  # Output:
  # OUTPUT-X/bulk_create/2026-09-22/bulk_create_videos.csv
  # OUTPUT-X/bulk_create/2026-09-22/bulk_create_photos.csv
"""
import argparse
import base64
import csv
import json
import os
import re
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv()

TWEET_ID_RE = re.compile(r"/status/(\d+)")

VIDEO_PROMPT = """You are an Indonesian social media editor for a dark editorial account on TikTok and Instagram Reels. Your audience is young, online, and used to captions that mix Indonesian and English the way real accounts actually write them — not translated, not textbook.

Your job: turn this tweet into a hook + headline that reads like a human wrote it in 10 seconds — whatever kind of tweet it is: news, economy/business, tech, social/relatable, funny, controversial, or anything else.

READ THE TWEET FIRST — match the tone to what's actually there, don't force one default voice onto everything:
- Serious news, tragedy, crime, disaster, official statements → no emoji, calm and factual, no exclamation energy.
- Economic/business/tech news → confident and informative; emoji only if it genuinely fits (📈 🚀), skip it if it feels forced.
- Funny, relatable, meme-y content → playful and casual, humor in the hook is fine.
- Heartwarming, inspiring, personal stories → warm tone, a soft emoji is fine (🥹 ❤️).
- Controversial or debate-worthy → neutral-curious framing, don't take a side; a question-style hook can work well here.
- Never default to hype or excitement just because that's the "safe" choice — the hook's energy should come from the tweet, not from a template.

LANGUAGE MIXING:
- Write the sentence structure and everyday words in Indonesian.
- Keep a word in English when it's a brand, tech term, or loanword already used as-is by Indonesian social media.
- The result should read like a real Indonesian TikTok/IG caption.

HOOK (top text on the cover):
- 2-5 words, matching the tone rules above.
- Emoji is optional, not default.

HEADLINE (one line under the hook):
- One natural sentence, max 14 words.
- Not all caps.

OTHER RULES:
- Never invent facts, emotions, or reactions the tweet doesn't contain.
- Never repeat engagement numbers (likes/views).
- No generic clickbait filler.
- Prefer one specific, concrete detail from the tweet over a vague reaction.

Tweet text: '{tweet_text}'

OUTPUT (compact JSON only, no preamble, no markdown):
{{"hook": "...", "headline": "..."}}"""

PHOTO_PROMPT = """Kamu adalah social media editor. Kamu akan melihat SEMUA foto asli dari carousel tweet ini, plus screenshot tweet untuk konteks pembahasannya.

DATA:
- hook: "{hook}"
- headline: "{headline}"
- source: "{source}"
- tweet_text: "{caption}"

TUGAS:
Berdasarkan foto-foto dan konteks tweet, buatkan:

1. HOOK: 2-5 kata, matching tone konten
2. HEADLINE: 1 kalimat, max 14 kata, menjelaskan isi foto
3. CONTENT: 2-3 kalimat detail tentang apa yang terlihat di foto:
   - Subjek utama (orang, hewan, objek)
   - Aksi/aksi yang terjadi
   - Emosi/mood
   - Detail visual (warna, komposisi, teks di foto)
   - Dikaitkan dengan konteks pembahasan tweetnya

ATURAN:
- Semua teks harus natural, campuran Indonesia-Inggris
- CONTENT harus deskriptif dan detail, bukan泛泛泛泛
- Jangan invent fakta yang tidak ada di foto

OUTPUT (compact JSON only, no preamble, no markdown):
{{"hook": "...", "headline": "...", "content": "..."}}"""


def extract_tweet_id(tweet_url: str) -> str:
    """Extract numeric tweet ID from URL."""
    match = TWEET_ID_RE.search(tweet_url)
    return match.group(1) if match else ""


def find_screenshot(screenshots_dir: Path, tweet_id: str) -> Path | None:
    if not screenshots_dir.is_dir():
        return None
    for f in screenshots_dir.glob(f"*{tweet_id}*"):
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            return f
    return None


def find_photos(downloads_dir: Path, scraped_date: str, tweet_id: str) -> list[Path]:
    """Find all downloaded photos for a tweet."""
    photos_dir = downloads_dir / scraped_date / "photos" / tweet_id
    if not photos_dir.is_dir():
        return []
    return sorted(photos_dir.glob("photo_*.jpg"))


def encode_image(image_path: Path) -> str:
    """Read image file and return base64-encoded string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="path to the day's explore/*.json")
    ap.add_argument("--screenshots", required=True, help="folder of screenshot images")
    ap.add_argument("--out", default="", help="output folder (default: OUTPUT-X/bulk_create/YYYY-MM-DD/)")
    ap.add_argument("--model", default="deepseek-flash")
    args = ap.parse_args()

    json_path = Path(args.json)
    raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    tweets = raw_data.get("tweets", []) if isinstance(raw_data, dict) else raw_data
    screenshots_dir = Path(args.screenshots)
    downloads_dir = Path("OUTPUT-X/downloads")
    client = openai.OpenAI(
        base_url="https://api.deepseek.com",
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    )

    m = re.search(r"(\d{4}-\d{2}-\d{2})", json_path.stem)
    scraped_date = m.group(1) if m else "unknown"

    out_dir = Path(args.out) if args.out else Path(f"OUTPUT-X/bulk_create/{scraped_date}")
    out_dir.mkdir(parents=True, exist_ok=True)

    video_rows = []
    photo_rows = []

    for t in tweets:
        tweet_url = t.get("tweet_url", "")
        tid = extract_tweet_id(tweet_url)
        text = (t.get("caption") or "").strip()
        handle = t.get("handle", "").strip()
        media_type = t.get("media_type", "none")
        if not tid or not text:
            continue

        screenshot_path = find_screenshot(screenshots_dir, tid)
        has_screenshot = screenshot_path is not None

        if media_type == "photo":
            # Photo: kirim semua foto original + screenshot ke AI
            photo_files = find_photos(downloads_dir, scraped_date, tid)
            prompt = PHOTO_PROMPT.format(hook="", headline="", source=handle, caption=text)
            content_parts: list[dict] = [{"type": "text", "text": prompt}]

            for pf in photo_files:
                b64 = encode_image(pf)
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

            if has_screenshot:
                b64 = encode_image(screenshot_path)
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})

            try:
                resp = client.chat.completions.create(
                    model=args.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": content_parts}],
                )
                raw = resp.choices[0].message.content.strip()
                data = json.loads(raw)
            except (json.JSONDecodeError, Exception) as e:  # noqa: BLE001
                print(f"skip {tid}: photo headline failed ({e})", file=sys.stderr)
                continue

            photo_rows.append({
                "tweet_id": tid,
                "hook": data.get("hook", ""),
                "headline": data.get("headline", ""),
                "source": handle,
                "content": data.get("content", ""),
            })
            print(f"ok {tid} [photo]: {data.get('hook')} / {data.get('headline')} [{len(photo_files)} photos]")

        else:
            # Video: prompt sama seperti sekarang
            prompt = VIDEO_PROMPT.format(tweet_text=text)

            try:
                if has_screenshot:
                    b64 = encode_image(screenshot_path)
                    suffix = screenshot_path.suffix.lower().lstrip(".")
                    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
                    api_content = [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                    ]
                else:
                    api_content = prompt
                resp = client.chat.completions.create(
                    model=args.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": api_content}],
                )
                raw = resp.choices[0].message.content.strip()
                data = json.loads(raw)
            except (json.JSONDecodeError, Exception) as e:  # noqa: BLE001
                print(f"skip {tid}: video headline failed ({e})", file=sys.stderr)
                continue

            video_rows.append({
                "tweet_id": tid,
                "hook": data.get("hook", ""),
                "headline": data.get("headline", ""),
                "source": handle,
            })
            print(f"ok {tid} [video]: {data.get('hook')} / {data.get('headline')}")

    video_fieldnames = ["tweet_id", "hook", "headline", "source"]
    photo_fieldnames = ["tweet_id", "hook", "headline", "source", "content"]

    video_path = out_dir / "bulk_create_videos.csv"
    photo_path = out_dir / "bulk_create_photos.csv"

    with open(video_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=video_fieldnames)
        writer.writeheader()
        writer.writerows(video_rows)

    with open(photo_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=photo_fieldnames)
        writer.writeheader()
        writer.writerows(photo_rows)

    print(f"\nwrote {len(video_rows)} video rows to {video_path}")
    print(f"wrote {len(photo_rows)} photo rows to {photo_path}")
    print("Upload to Canva: Edit -> Bulk create -> Upload CSV.")


if __name__ == "__main__":
    main()
