import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from playwright.async_api import async_playwright  # type: ignore[import-not-found]
except ImportError as exc:
    raise ImportError(
        "Playwright is not installed. Install it with: pip install playwright"
    ) from exc

from src.browser import init_browser_context
from src.config import (
    HEADLESS,
    OUTPUT_DIR,
    OUTPUT_FILE_PATTERN_3DAYS_GL,
    OUTPUT_FILE_PATTERN_3DAYS_ID,
    OUTPUT_FILE_PATTERN_MONTHLY_GL,
    OUTPUT_FILE_PATTERN_MONTHLY_ID,
    QUERY_GLOBAL,
    QUERY_INDONESIA,
    SCRAPE_LIMIT,
)
from src.models import ScrapeReport
from src.scraper import scrape_top_videos


def write_report(filepath: Path, report: ScrapeReport) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)


async def run_scraper(target_month: str, headless: bool = True):
    today = datetime.now(timezone.utc)
    since_date_monthly = f"{target_month}-01"
    since_date_3days = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    print("=" * 60)
    print("X/Twitter Video Engagement Scraper")
    print(f"Bulan target: {target_month}")
    print(f"Since bulanan: {since_date_monthly}")
    print(f"Since 3 hari: {since_date_3days}")
    print("Formula: Likes + Reposts + Views")
    print("=" * 60)

    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    query_id_monthly = f"{QUERY_INDONESIA} since:{since_date_monthly}"
    query_gl_monthly = f"{QUERY_GLOBAL} since:{since_date_monthly}"
    query_id_3days = f"{QUERY_INDONESIA} since:{since_date_3days}"
    query_gl_3days = f"{QUERY_GLOBAL} since:{since_date_3days}"

    async with async_playwright() as p:
        browser, context = await init_browser_context(p, headless=headless)
        page = await context.new_page()

        # [1/4] Indonesia Monthly
        print("\n[1/4] Scraping Top 15 Indonesia Monthly...")
        top_id_monthly = await scrape_top_videos(page, query_id_monthly, limit=SCRAPE_LIMIT)

        # [2/4] Global Monthly
        print("\n[2/4] Scraping Top 15 Global Monthly...")
        top_gl_monthly = await scrape_top_videos(page, query_gl_monthly, limit=SCRAPE_LIMIT)

        # [3/4] Indonesia 3 Days
        print("\n[3/4] Scraping Top 15 Indonesia 3 Days...")
        top_id_3days = await scrape_top_videos(page, query_id_3days, limit=SCRAPE_LIMIT)

        # [4/4] Global 3 Days
        print("\n[4/4] Scraping Top 15 Global 3 Days...")
        top_gl_3days = await scrape_top_videos(page, query_gl_3days, limit=SCRAPE_LIMIT)

        await browser.close()

    # Save 4 reports
    reports = [
        (OUTPUT_FILE_PATTERN_MONTHLY_ID.format(target_month), "Indonesia Monthly", top_id_monthly),
        (OUTPUT_FILE_PATTERN_MONTHLY_GL.format(target_month), "Global Monthly", top_gl_monthly),
        (OUTPUT_FILE_PATTERN_3DAYS_ID.format(today_str), "Indonesia 3 Days", top_id_3days),
        (OUTPUT_FILE_PATTERN_3DAYS_GL.format(today_str), "Global 3 Days", top_gl_3days),
    ]

    total_videos = 0
    for filename, label, videos in reports:
        report = ScrapeReport(
            scraped_date=target_month,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            formula="likes + reposts + views",
            total_items=len(videos),
            indonesia_explore=videos if "Indonesia" in label else [],
            global_explore=videos if "Global" in label else [],
        )
        filepath = output_dir / filename
        write_report(filepath, report)
        total_videos += len(videos)
        print(f"[Output] {label}: {len(videos)} video → {filepath.resolve()}")

    print("\n" + "=" * 60)
    print(f"SELESAI! Total {total_videos} video tersimpan dalam 4 file.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Top 15 Engaged Videos from X/Twitter (Indonesia & Global) - 4 Output Files"
    )
    parser.add_argument(
        "--month",
        type=str,
        default=datetime.now(timezone.utc).strftime("%Y-%m"),
        help="Bulan target dalam format YYYY-MM (default: bulan ini UTC)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Buka browser secara visual (berguna untuk inspeksi / debugging)",
    )

    args = parser.parse_args()
    headless = HEADLESS and not args.no_headless

    asyncio.run(run_scraper(target_month=args.month, headless=headless))


if __name__ == "__main__":
    main()
