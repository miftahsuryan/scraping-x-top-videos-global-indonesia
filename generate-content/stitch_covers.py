#!/usr/bin/env python3
"""
stitch_covers.py

Combines a Canva-exported cover image with its matching scraped tweet
video into one 9:16 (1080x1920) MP4, ready to post: cover holds for a
couple seconds, then the tweet video plays.

Matches files by tweet ID, found anywhere in the filename (works with
names like "tweet_2100019334013....png" and "tweet_2100019334013....mp4").

Requires ffmpeg on PATH.

Usage:
  python3 stitch_covers.py \
      --covers ./bulk_create_exports \
      --videos ./downloads/2026-09-20 \
      --output ./ready_to_post \
      --cover-seconds 1.75
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

TWEET_ID_RE = re.compile(r"(\d{15,20})")  # tweet ids are long numeric strings


def extract_tweet_id(filename: str):
    m = TWEET_ID_RE.search(filename)
    return m.group(1) if m else None


def index_by_tweet_id(folder: Path, exts: set[str]) -> dict[str, Path]:
    index = {}
    for f in folder.iterdir():
        if f.is_file() and f.suffix.lower().lstrip(".") in exts:
            tid = extract_tweet_id(f.name)
            if tid:
                index[tid] = f
    return index


def stitch(cover: Path, video: Path, out_path: Path, cover_seconds: float):
    # Scale + pad both segments to the same 1080x1920 canvas before concatenating,
    # since the cover is a still image and the tweet video may be a different size.
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[cov];"
        "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[vid];"
        "[cov][vid]concat=n=2:v=1:a=0[outv]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(cover_seconds), "-i", str(cover),
        "-i", str(video),
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "1:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--covers", required=True, help="folder of exported cover PNG/JPGs")
    ap.add_argument("--videos", required=True, help="folder of downloaded tweet videos")
    ap.add_argument("--output", required=True, help="folder for finished MP4s")
    ap.add_argument("--cover-seconds", type=float, default=1.75)
    args = ap.parse_args()

    covers_dir, videos_dir, out_dir = Path(args.covers), Path(args.videos), Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    covers = index_by_tweet_id(covers_dir, {"png", "jpg", "jpeg"})
    videos = index_by_tweet_id(videos_dir, {"mp4", "mov", "webm"})

    matched = sorted(set(covers) & set(videos))
    missing_video = set(covers) - set(videos)
    missing_cover = set(videos) - set(covers)

    print(f"{len(matched)} matched pairs, {len(missing_video)} covers with no video, "
          f"{len(missing_cover)} videos with no cover")

    for tid in matched:
        out_path = out_dir / f"tweet_{tid}.mp4"
        print(f"-> {out_path.name}")
        try:
            stitch(covers[tid], videos[tid], out_path, args.cover_seconds)
        except subprocess.CalledProcessError as e:
            print(f"   ffmpeg failed for {tid}: {e.stderr[-500:]}", file=sys.stderr)

    if missing_video:
        print(f"no video for: {', '.join(sorted(missing_video))}", file=sys.stderr)
    if missing_cover:
        print(f"no cover for: {', '.join(sorted(missing_cover))}", file=sys.stderr)


if __name__ == "__main__":
    main()
