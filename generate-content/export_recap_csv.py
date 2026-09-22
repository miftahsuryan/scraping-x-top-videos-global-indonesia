#!/usr/bin/env python3
"""
export_recap_csv.py

Combines bulk_create.csv (hook, headline, source) and captions.txt (caption, hashtags, opening_comment)
into a single recap CSV ready for Google Sheets import.

Captions format per block (separated by double newlines):
    [1-3 kata caption]
    cr: [source]
    #hashtag1 #hashtag2 #hashtag3 #hashtag4
    [pertanyaan atau ajakan]

Usage:
  python3 generate-content/export_recap_csv.py \
      --csv bulk_create.csv \
      --captions captions.txt \
      --out OUTPUT-X/recap_2026-09-21.csv
"""
import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_captions(captions_text: str) -> list[dict]:
    """Parse captions.txt into list of dicts with caption, hashtags, and opening_comment.

    Format per block (separated by double newlines):
        [1-3 kata caption]
        cr: [source]
        #hashtag1 #hashtag2 #hashtag3 #hashtag4
        [pertanyaan atau ajakan]
    """
    blocks = re.split(r"\n\n+", captions_text.strip())
    results = []
    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue

        caption_line = lines[0] if len(lines) >= 1 else ""
        hashtags_line = ""
        opening_comment = ""
        for line in lines:
            if line.startswith("#"):
                hashtags_line = line
            elif line != caption_line and not line.startswith("cr:"):
                opening_comment = line

        results.append({
            "caption": caption_line,
            "hashtags": hashtags_line,
            "opening_comment": opening_comment,
        })
    return results


def main():
    ap = argparse.ArgumentParser(
        description="Export recap CSV (hook + headline + caption + hashtags + opening_comment) for Google Sheets import"
    )
    ap.add_argument("--csv", required=True, help="path to bulk_create.csv")
    ap.add_argument("--captions", required=True, help="path to captions.txt")
    ap.add_argument("--scraped-date", default="", help="scraped date (YYYY-MM-DD), default: auto-detect from CSV filename")
    ap.add_argument("--out", required=True, help="output recap CSV path")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    captions_path = Path(args.captions)

    if not csv_path.is_file():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    if not captions_path.is_file():
        print(f"Error: captions file not found: {captions_path}", file=sys.stderr)
        sys.exit(1)

    with open(csv_path, "r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))

    if not csv_rows:
        print("No rows found in CSV.", file=sys.stderr)
        sys.exit(1)

    with open(captions_path, "r", encoding="utf-8") as f:
        captions_data = parse_captions(f.read())

    if not captions_data:
        print("No captions found in captions file.", file=sys.stderr)
        sys.exit(1)

    if len(csv_rows) != len(captions_data):
        print(
            f"Warning: CSV has {len(csv_rows)} rows but captions has {len(captions_data)} entries. "
            f"Matching first {min(len(csv_rows), len(captions_data))} pairs.",
            file=sys.stderr,
        )

    match_count = min(len(csv_rows), len(captions_data))

    scraped_date = args.scraped_date
    if not scraped_date:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", csv_path.stem)
        scraped_date = m.group(1) if m else ""

    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    fieldnames = ["tweet_id", "hook", "headline", "source", "content", "caption", "hashtags", "opening_comment", "scraped_date", "run_date"]

    rows = []
    for i in range(match_count):
        csv_row = csv_rows[i]
        cap = captions_data[i]
        rows.append({
            "tweet_id": csv_row.get("tweet_id", ""),
            "hook": csv_row.get("hook", ""),
            "headline": csv_row.get("headline", ""),
            "source": csv_row.get("source", ""),
            "content": csv_row.get("content", ""),
            "caption": cap["caption"],
            "hashtags": cap["hashtags"],
            "opening_comment": cap["opening_comment"],
            "scraped_date": scraped_date,
            "run_date": run_date,
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {out_path}")
    print("Import to Google Sheets: File -> Import -> Upload -> Select file -> Replace spreadsheet")


if __name__ == "__main__":
    main()
