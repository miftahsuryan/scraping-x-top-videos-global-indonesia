#!/usr/bin/env python3
"""
generate_covers_csv.py

Turns your scraped tweet metadata into a CSV you upload to Canva's
Bulk Create (Edit > Bulk create, on the cover template). The template
has 3 fields already tagged: hook_word, headline, photo.

>>> Adjust the block below to match your scraper's actual JSON keys. <<<
These are reasonable guesses -- open one record in your explore/*.json
and change ID_FIELD / TEXT_FIELD if the names differ.

Setup:
  pip install openai
  export DEEPSEEK_API_KEY=sk-...

Usage:
  python3 generate_covers_csv.py \
      --json explore/2026-09-20.json \
      --screenshots screenshots/2026-09-20 \
      --out bulk_create.csv
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

import openai

ID_FIELD = "id"        # key holding the tweet id in each JSON record
TEXT_FIELD = "text"    # key holding the tweet's text/caption

PROMPT = """You write short, punchy Indonesian captions for a tech/business \
"viral facts" content account. Given the tweet text below, produce:

1. hook_word: 1-3 words, ALL CAPS -- the single most provocative word, \
number, or stat from the tweet (this gets rendered in the brand's orange \
accent color, above the headline)
2. headline: one punchy ALL-CAPS sentence, max ~8 words, written to make \
someone stop scrolling

Tweet:
\"\"\"{tweet_text}\"\"\"

Respond with ONLY compact JSON, no other text:
{{"hook_word": "...", "headline": "..."}}"""


def find_screenshot(screenshots_dir: Path, tweet_id: str) -> str:
    for f in screenshots_dir.glob(f"*{tweet_id}*"):
        return str(f.resolve())
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="path to the day's explore/*.json")
    ap.add_argument("--screenshots", required=True, help="folder of screenshot images")
    ap.add_argument("--out", default="bulk_create.csv")
    ap.add_argument("--model", default="deepseek-chat")
    args = ap.parse_args()

    tweets = json.loads(Path(args.json).read_text(encoding="utf-8"))
    screenshots_dir = Path(args.screenshots)
    client = openai.OpenAI(
        base_url="https://api.deepseek.com",
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    )

    rows = []
    for t in tweets:
        tid = str(t.get(ID_FIELD, "")).strip()
        text = (t.get(TEXT_FIELD) or "").strip()
        if not tid or not text:
            continue

        photo = find_screenshot(screenshots_dir, tid)
        if not photo:
            print(f"skip {tid}: no matching screenshot in {screenshots_dir}", file=sys.stderr)
            continue

        resp = client.chat.completions.create(
            model=args.model,
            max_tokens=200,
            messages=[{"role": "user", "content": PROMPT.format(tweet_text=text)}],
        )
        raw = resp.choices[0].message.content.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"skip {tid}: unparseable model output: {raw!r}", file=sys.stderr)
            continue

        rows.append({
            "tweet_id": tid,
            "hook_word": data.get("hook_word", ""),
            "headline": data.get("headline", ""),
            "photo": photo,
        })
        print(f"ok {tid}: {data.get('hook_word')} / {data.get('headline')}")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tweet_id", "hook_word", "headline", "photo"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nwrote {len(rows)} rows to {args.out}")
    print("Upload this CSV in Canva: open the template -> Edit -> Bulk create -> Upload CSV.")
    print("When Canva asks which field names the columns map to, match hook_word / headline / photo.")
    print("Set the file-name field to tweet_id in the review step, so exports line up with your videos.")


if __name__ == "__main__":
    main()
