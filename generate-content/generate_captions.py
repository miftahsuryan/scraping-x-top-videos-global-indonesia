#!/usr/bin/env python3
"""
generate_captions.py

Generate short Instagram/TikTok captions from CSV + screenshots.
Uses DeepSeek Flash API (supports vision/image input).

Setup:
  pip install openai
  Isi DEEPSEEK_API_KEY di file .env (otomatis terbaca)

Usage:
  python3 generate-content/generate_captions.py \
      --csv bulk_create_2026-09-21.csv \
      --screenshots OUTPUT-X/screenshots/2026-09-21

  # Output otomatis ke OUTPUT-X/captions/2026-09-21/captions.txt
"""
import argparse
import base64
import csv
import os
import re
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv()

CAPTION_PROMPT_WITH_IMAGE = """Kamu adalah social media caption writer. Kamu akan melihat screenshot postingan social media.

DATA:
- hook: "{hook}"
- headline: "{headline}"
- source: "{source}"

TUGAS:
Berdasarkan screenshot yang kamu lihat, buatkan:

1. CAPTION: reaksi singkat 1-3 kata, emotional, semua lowercase, seperti manusia bereaksi spontan. Tambahkan 1 emoji yang relevan.
2. HASHTAG: tepat 4 hashtag, semua lowercase, 1 kata, relevan dengan isi konten di screenshot.
3. OPENING: pertanyaan atau ajakan singkat untuk memancing interaksi, semua lowercase, berkaitan dengan konten.

ATURAN:
- Semua teks HARUS lowercase (tidak ada capslock sama sekali)
- Caption hanya 1-3 kata, bukan kalimat panjang
- Hashtag harus spesifik ke konten, bukan generik (#viral #fyp #trending dilarang)
- Hashtag tidak boleh duplikat makna
- Opening harus memancing reply atau interaksi
- Jangan gunakan tanda kutip, asterisk, atau markdown

OUTPUT (hanya 4 baris, tanpa penjelasan, tanpa nomor urut):
[1-3 kata caption]
cr: [source]
#hashtag1 #hashtag2 #hashtag3 #hashtag4
[pertanyaan atau ajakan]"""

CAPTION_PROMPT_TEXT_ONLY = """Kamu adalah social media caption writer.

DATA:
- hook: "{hook}"
- headline: "{headline}"
- source: "{source}"

TUGAS:
Berdasarkan data di atas, buatkan:

1. CAPTION: reaksi singkat 1-3 kata, emotional, semua lowercase, seperti manusia bereaksi spontan. Tambahkan 1 emoji yang relevan.
2. HASHTAG: tepat 4 hashtag, semua lowercase, 1 kata, relevan dengan isi konten.
3. OPENING: pertanyaan atau ajakan singkat untuk memancing interaksi, semua lowercase, berkaitan dengan konten.

ATURAN:
- Semua teks HARUS lowercase (tidak ada capslock sama sekali)
- Caption hanya 1-3 kata, bukan kalimat panjang
- Hashtag harus spesifik ke konten, bukan generik (#viral #fyp #trending dilarang)
- Hashtag tidak boleh duplikat makna
- Opening harus memancing reply atau interaksi
- Jangan gunakan tanda kutip, asterisk, atau markdown

OUTPUT (hanya 4 baris, tanpa penjelasan, tanpa nomor urut):
[1-3 kata caption]
cr: [source]
#hashtag1 #hashtag2 #hashtag3 #hashtag4
[pertanyaan atau ajakan]"""

CAPTION_PROMPT_PHOTO = """Kamu adalah social media editor dan visual content writer.

Kamu akan menerima:
1. foto dari sebuah postingan/carousel
2. headline
3. hook
4. deskripsi konten

Tugasmu adalah memahami FOTO + KONTEKS lalu membuat copy yang cocok untuk konten Instagram/TikTok.

DATA:

- hook: "{hook}"
- headline: "{headline}"
- source: "{source}"
- content: "{content}"

ANALISIS DULU:
- Apa yang sebenarnya terlihat di foto?
- Apa kejadian utama?
- Apa detail visual yang paling menarik?
- Apa fakta/konteks yang membuat foto tersebut menarik?
- Apakah ada kemungkinan informasi yang tidak bisa dipastikan hanya dari foto?

JANGAN:
- mengarang detail visual
- mengarang identitas orang/hewan/tempat
- mengarang angka
- mengklaim sesuatu hanya karena terlihat seperti itu
- menggunakan clickbait yang tidak sesuai isi

COPY HARUS:
- natural
- conversational
- singkat
- spesifik
- mudah dibaca
- cocok untuk desain social media
- terasa seperti tulisan editor manusia

BUAT:

HOOK:
Maksimal 8 kata.
Fokus pada aspek paling menarik dari foto.

HEADLINE:
Maksimal 12 kata.
Jelaskan kejadian/fakta utama.

CAPTION:
1-2 kalimat.
Maksimal 25 kata.
Berikan konteks tambahan yang relevan.

REACTION:
1-3 kata + 1 emoji.
Reaksi spontan yang sesuai dengan foto.

HASHTAGS:
Tepat 4 hashtag.
Semua lowercase.
Spesifik terhadap konten.
Jangan gunakan #viral #fyp #trending #reels #tiktok.

OPENING:
Satu pertanyaan pendek yang spesifik terhadap foto/konten.
Tujuannya memancing orang berkomentar.

CREDIT:
cr: {source}

FORMAT OUTPUT WAJIB:

HOOK: [hook]

HEADLINE: [headline]

CAPTION: [caption]

REACTION: [reaction]

HASHTAGS: [hashtag1] [hashtag2] [hashtag3] [hashtag4]

OPENING: [opening]

CREDIT: cr: [source]

Jangan memberikan penjelasan tambahan.
Jangan gunakan markdown.
"""


def find_screenshot(screenshots_dir: Path, tweet_id: str) -> Path | None:
    """Find screenshot file matching tweet_id."""
    if not screenshots_dir.is_dir():
        return None
    for f in screenshots_dir.glob(f"*{tweet_id}*"):
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            return f
    return None


def encode_image(image_path: Path) -> str:
    """Read image file and return base64-encoded string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def main():
    ap = argparse.ArgumentParser(
        description="Generate short Instagram/TikTok captions from CSV + screenshots"
    )
    ap.add_argument("--csv", required=True, help="path to CSV file (tweet_id,hook,headline,source)")
    ap.add_argument("--screenshots", required=True, help="folder of screenshot images")
    ap.add_argument("--out", default="", help="output text file (default: OUTPUT-X/captions/YYYY-MM-DD/captions.txt)")
    ap.add_argument("--model", default="deepseek-flash", help="DeepSeek model (default: deepseek-flash)")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    screenshots_dir = Path(args.screenshots)

    if not csv_path.is_file():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    client = openai.OpenAI(
        base_url="https://api.deepseek.com",
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    )

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No rows found in CSV.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(rows)} rows from {csv_path.name}")

    is_photo_csv = "content" in (rows[0].keys() if rows else [])

    captions = []
    for i, row in enumerate(rows, 1):
        hook = row.get("hook", "").strip()
        headline = row.get("headline", "").strip()
        source = row.get("source", "").strip()
        tweet_id = row.get("tweet_id", "").strip()
        content = row.get("content", "").strip() if is_photo_csv else ""

        if not hook and not headline:
            print(f"  skip row {i}: empty hook and headline", file=sys.stderr)
            continue

        screenshot_path = find_screenshot(screenshots_dir, tweet_id)
        has_screenshot = screenshot_path is not None

        if is_photo_csv:
            prompt = CAPTION_PROMPT_PHOTO.format(
                hook=hook, headline=headline, source=source, content=content,
            )
        else:
            prompt = (CAPTION_PROMPT_WITH_IMAGE if has_screenshot else CAPTION_PROMPT_TEXT_ONLY).format(
                hook=hook, headline=headline, source=source,
            )

        try:
            if has_screenshot:
                b64 = encode_image(screenshot_path)
                suffix = screenshot_path.suffix.lower().lstrip(".")
                mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
                content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                ]
            else:
                content = prompt

            resp = client.chat.completions.create(
                model=args.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": content}],
            )
            caption_text = resp.choices[0].message.content.strip()
        except Exception as e:  # noqa: BLE001
            print(f"  skip row {i} ({tweet_id}): API failed ({e})", file=sys.stderr)
            continue

        captions.append(caption_text)
        has_img = "w/ image" if has_screenshot else "text only"
        print(f"  ok row {i} ({tweet_id}) [{has_img}]: {caption_text[:60]}...")

    m = re.search(r"(\d{4}-\d{2}-\d{2})", csv_path.stem)
    scraped_date = m.group(1) if m else "unknown"

    output_path = Path(args.out) if args.out else Path(f"OUTPUT-X/captions/{scraped_date}/captions.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(captions))
        f.write("\n")

    print(f"\nwrote {len(captions)} captions to {output_path}")
    print("Copy-paste each block (separated by ---) to Instagram/TikTok.")


if __name__ == "__main__":
    main()
