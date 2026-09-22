#!/usr/bin/env python3
"""
stitch_covers.py

Combines a Canva-exported cover video (5 seconds) with a downloaded tweet
video into one 9:16 (1080x1920) MP4, ready to post.

Cover video holds for cover_seconds, then the tweet video plays.
Audio is preserved from the tweet video; cover video audio is handled
with silence fallback if missing.

Matching modes:
  --mode id (default): match by tweet ID in filename
  --mode order: match by sorted file order (Canva export order = CSV row order)

Requires ffmpeg and ffprobe on PATH.

Usage:
  python3 stitch_covers.py \
      --covers OUTPUT-X/covers/2026-09-22/videos \
      --downloads OUTPUT-X/downloads/2026-09-22/videos \
      --output OUTPUT-X/ready_to_post
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TWEET_ID_RE = re.compile(r"(\d{15,20})")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


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


def index_by_order(folder: Path, exts: set[str]) -> list[Path]:
    files = sorted(
        [f for f in folder.iterdir()
         if f.is_file() and f.suffix.lower().lstrip(".") in exts],
        key=lambda f: f.name,
    )
    return files


def has_audio_stream(path: Path) -> bool:
    """Check if a video file has an audio stream using ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "json", str(path)],
        check=False, capture_output=True, text=True,
    )
    return bool(json.loads(r.stdout or "{}").get("streams"))


def stitch(cover_video: Path, tweet_video: Path, out_path: Path, cover_seconds: float):
    """Stitch cover video + tweet video with proper audio handling."""
    video_filter = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];"
        "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[outv]"
    )

    cover_audio = has_audio_stream(cover_video)
    tweet_audio = has_audio_stream(tweet_video)

    cmd = ["ffmpeg", "-y", "-i", str(cover_video), "-i", str(tweet_video)]

    if cover_audio and tweet_audio:
        filt = video_filter + ";[0:a][1:a]concat=n=2:v=0:a=1[outa]"
        cmd += ["-filter_complex", filt, "-map", "[outv]", "-map", "[outa]"]
    elif tweet_audio:
        # Cover tanpa audio → tambal silence lalu concat
        filt = (
            video_filter
            + f";anullsrc=channel_layout=stereo:sample_rate=44100:d={cover_seconds}[sil]"
            + ";[sil][1:a]concat=n=2:v=0:a=1[outa]"
        )
        cmd += ["-filter_complex", filt, "-map", "[outv]", "-map", "[outa]"]
    else:
        cmd += ["-filter_complex", video_filter, "-map", "[outv]"]

    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def stitch_by_id(covers_dir, downloads_dir, out_dir, cover_seconds):
    covers = index_by_tweet_id(covers_dir, {"mp4", "mov", "webm"})
    videos = index_by_tweet_id(downloads_dir, {"mp4", "mov", "webm"})

    matched = sorted(set(covers) & set(videos))
    missing = set(covers) - set(videos)

    print(f"{len(matched)} video pairs, {len(missing)} covers with no tweet video")

    for tid in matched:
        out_path = out_dir / f"tweet_{tid}.mp4"
        print(f"-> {out_path.name} (video)")
        try:
            stitch(covers[tid], videos[tid], out_path, cover_seconds)
        except subprocess.CalledProcessError as e:
            print(f"   ffmpeg failed for {tid}: {e.stderr[-500:]}", file=sys.stderr)

    if missing:
        print(f"no tweet video for: {', '.join(sorted(missing))}", file=sys.stderr)


def stitch_by_order(covers_dir, downloads_dir, out_dir, cover_seconds):
    covers = index_by_order(covers_dir, {"mp4", "mov", "webm"})
    downloads = index_by_order(downloads_dir, {"mp4", "mov", "webm"})

    if not covers:
        print("No cover video files found in covers folder.", file=sys.stderr)
        return

    if not downloads:
        print("No tweet video files found in downloads folder.", file=sys.stderr)
        return

    print(f"{len(covers)} covers, {len(downloads)} videos")

    matched = min(len(covers), len(downloads))
    if len(covers) != len(downloads):
        print(f"Warning: mismatch ({len(covers)} covers vs {len(downloads)} videos), "
              f"matching first {matched} pairs", file=sys.stderr)

    for i in range(matched):
        cover = covers[i]
        download = downloads[i]
        tid = extract_tweet_id(download.name) or f"cover_{i+1:03d}"

        out_path = out_dir / f"tweet_{tid}.mp4"
        print(f"-> {out_path.name} (video)")
        try:
            stitch(cover, download, out_path, cover_seconds)
        except subprocess.CalledProcessError as e:
            print(f"   ffmpeg failed for {tid}: {e.stderr[-500:]}", file=sys.stderr)

    unmatched_covers = covers[matched:]
    unmatched_downloads = downloads[matched:]
    if unmatched_covers:
        print(f"unmatched covers: {len(unmatched_covers)}", file=sys.stderr)
    if unmatched_downloads:
        print(f"unmatched videos: {len(unmatched_downloads)}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--covers", required=True, help="folder of cover videos (MP4) from Canva")
    ap.add_argument("--downloads", required=True, help="folder of downloaded tweet videos")
    ap.add_argument("--output", required=True, help="folder for finished content")
    ap.add_argument("--cover-seconds", type=float, default=5.0,
                     help="how long the cover video plays before tweet video (default: 5.0)")
    ap.add_argument("--mode", choices=["id", "order"], default="id",
                     help="id: match by tweet ID in filename (default); order: match by sorted file order")
    args = ap.parse_args()

    covers_dir = Path(args.covers)
    downloads_dir = Path(args.downloads)
    out_dir = Path(args.output)

    if not covers_dir.is_dir():
        print(f"Error: covers folder not found: {covers_dir}", file=sys.stderr)
        print("Export your Canva cover videos first, then pass the folder path.", file=sys.stderr)
        sys.exit(1)

    if not downloads_dir.is_dir():
        print(f"Error: downloads folder not found: {downloads_dir}", file=sys.stderr)
        print("Run 'python main.py --download' first.", file=sys.stderr)
        sys.exit(1)

    if not DATE_RE.search(out_dir.name):
        m = DATE_RE.search(str(downloads_dir))
        date_str = m.group(0) if m else __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).strftime("%Y-%m-%d")
        out_dir = out_dir / "videos" / date_str

    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "order":
        stitch_by_order(covers_dir, downloads_dir, out_dir, args.cover_seconds)
    else:
        stitch_by_id(covers_dir, downloads_dir, out_dir, args.cover_seconds)


if __name__ == "__main__":
    main()
