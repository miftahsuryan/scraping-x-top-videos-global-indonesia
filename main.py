import argparse
import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    from playwright.async_api import async_playwright  # type: ignore[import-not-found]
except ImportError as exc:
    raise ImportError(
        "Playwright is not installed. Install it with: pip install playwright"
    ) from exc

from src.browser import init_browser_context
from src.config import (
    CATEGORIES,
    DEFAULT_KEYWORDS_GL,
    DEFAULT_KEYWORDS_ID,
    EXPLORE_LIMIT,
    EXPLORE_MAX_SCROLLS,
    HEADLESS,
    MAX_SCROLLS,
    MIN_FAVES,
    OUTPUT_DIR,
    PERIODS,
    SCRAPE_LIMIT,
    parse_keywords,
)
from src.downloader import run_downloader
from src.models import ScrapeReport
from src.scraper import scrape_explore_for_you, scrape_top_videos


def get_since_date(period: str) -> str:
    """Calculate since_date based on period."""
    today = date.today()  # noqa: DTZ011
    if period == "1day":
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif period == "3days":
        return (today - timedelta(days=3)).strftime("%Y-%m-%d")
    elif period == "weekly":
        days_since_monday = today.weekday()
        start_of_week = today - timedelta(days=days_since_monday)
        return start_of_week.strftime("%Y-%m-%d")
    else:  # monthly
        return today.strftime("%Y-%m-01")


def get_date_label(period: str) -> str:
    """Get date label for filename — always YYYY-MM-DD."""
    today = date.today()  # noqa: DTZ011
    return today.strftime("%Y-%m-%d")


def get_query(category: str, locale: str, keywords: list[str], period: str) -> str:
    """Build search query for a category, locale, and period."""
    min_faves = MIN_FAVES[period]
    since_date = get_since_date(period)

    if keywords:
        quoted = []
        for kw in keywords:
            if " " in kw:
                quoted.append(f'"{kw}"')
            else:
                quoted.append(kw)
        keyword_str = " OR ".join(quoted)
        query = f"{keyword_str} filter:media min_faves:{min_faves} since:{since_date} -is:retweet"
    else:
        query = f"filter:media min_faves:{min_faves} since:{since_date} -is:retweet"

    return query


def get_merged_keywords(category: str, locale: str, custom_id: list[str], custom_gl: list[str]) -> list[str]:
    """Get merged keywords (custom + default) for a category and locale."""
    if locale == "indonesia":
        default = DEFAULT_KEYWORDS_ID.get(category, [])
        custom = custom_id
    else:
        default = DEFAULT_KEYWORDS_GL.get(category, [])
        custom = custom_gl

    return custom + default


def write_report(filepath: Path, report: ScrapeReport) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)


async def run_scraper(
    periods: list[str],
    categories: list[str],
    custom_keywords_id: list[str],
    custom_keywords_gl: list[str],
    headless: bool = True,
):
    print("=" * 60)
    print("X/Twitter Video Scraper")
    print(f"Periods: {', '.join(periods)}")
    print(f"Categories: {', '.join(categories)}")
    print("Formula: Likes + Reposts + Views")
    print("=" * 60)

    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []
    total_tweets = 0

    async with async_playwright() as p:
        browser, context = await init_browser_context(p, headless=headless)
        page = await context.new_page()

        task_num = 0
        total_tasks = len(periods) * len(categories) * 2

        for period in periods:
            since_date = get_since_date(period)
            date_label = get_date_label(period)
            limit = SCRAPE_LIMIT[period]

            for category in categories:
                for locale in ["indonesia", "global"]:
                    task_num += 1
                    print(f"\n[{task_num}/{total_tasks}] {category} | {locale} | {period}")

                    keywords = get_merged_keywords(category, locale, custom_keywords_id, custom_keywords_gl)
                    query = get_query(category, locale, keywords, period)
                    print(f"  Query: {query}")

                    tweets = await scrape_top_videos(page, query, limit=limit, max_scrolls=MAX_SCROLLS)
                    print(f"  Scraped: {len(tweets)} tweets")

                    tweets.sort(key=lambda t: t.engagement.total_score, reverse=True)
                    top_tweets = tweets[:limit]

                    report = ScrapeReport(
                        period=period,
                        category=category,
                        locale=locale,
                        scraped_date=since_date,
                        scraped_at=datetime.now(timezone.utc).isoformat(),
                        formula="likes + reposts + views",
                        total_items=len(top_tweets),
                        tweets=top_tweets,
                    )

                    folder = output_dir / locale / category
                    folder.mkdir(parents=True, exist_ok=True)
                    filename = f"{date_label}.json"
                    filepath = folder / filename
                    write_report(filepath, report)

                    total_tweets += len(top_tweets)
                    print(f"  → {len(top_tweets)} tweets saved to {filepath}")

                    all_results.append({
                        "locale": locale,
                        "category": category,
                        "period": period,
                        "filename": f"{locale}/{category}/{filename}",
                        "total_items": len(top_tweets),
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    })

        await browser.close()

    index = {
        "run_date": datetime.now(timezone.utc).isoformat(),
        "results": all_results,
    }
    index_path = output_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:  # noqa: ASYNC230
        json.dump(index, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"SELESAI! Total {total_tweets} tweets tersimpan dalam {len(all_results)} files.")
    print(f"Index: {index_path.resolve()}")
    print("=" * 60)


async def run_explore_scraper(
    headless: bool = True,
    limit: int = EXPLORE_LIMIT,
    **_kwargs,
):
    print("=" * 60)
    print("X/Twitter Video Scraper — EXPLORE MODE")
    print("Source: X Search Top — 15 Best Viral Media (Engagement Ranked)")
    print("Formula: Likes + Reposts + Views")
    print("=" * 60)

    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []
    total_tweets = 0

    async with async_playwright() as p:
        browser, context = await init_browser_context(p, headless=headless)
        page = await context.new_page()

        since_date = date.today().strftime("%Y-%m-%d")  # noqa: DTZ011
        date_label = date.today().strftime("%Y-%m-%d")  # noqa: DTZ011

        tweets = await scrape_explore_for_you(
            page, limit=limit, max_scrolls=EXPLORE_MAX_SCROLLS, date_label=date_label
        )
        print(f"  Scraped: {len(tweets)} tweets")

        tweets.sort(key=lambda t: t.engagement.total_score, reverse=True)
        top_tweets = tweets[:limit]

        report = ScrapeReport(
            period="explore",
            category="explore",
            locale="mixed",
            scraped_date=since_date,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            formula="likes + reposts + views",
            mode="explore",
            total_items=len(top_tweets),
            tweets=top_tweets,
        )

        folder = output_dir / "explore"
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{date_label}.json"
        filepath = folder / filename
        write_report(filepath, report)

        total_tweets += len(top_tweets)
        print(f"  → {len(top_tweets)} tweets saved to {filepath}")

        all_results.append({
            "locale": "mixed",
            "category": "explore",
            "period": "explore",
            "mode": "explore",
            "filename": f"explore/{filename}",
            "total_items": len(top_tweets),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

        await browser.close()

    index = {
        "run_date": datetime.now(timezone.utc).isoformat(),
        "mode": "explore",
        "results": all_results,
    }
    index_path = output_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:  # noqa: ASYNC230
        json.dump(index, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"SELESAI! Total {total_tweets} tweets tersimpan dalam {len(all_results)} files.")
    print(f"Index: {index_path.resolve()}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="X/Twitter Video Scraper — Explore Mode Default (4 Periods), Search Mode Available"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="explore",
        choices=["search", "explore"],
        help="Mode scraping: explore (halaman Explore For You / random viral, default) atau search (berdasarkan kategori/keywords)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="all",
        choices=["1day", "3days", "weekly", "monthly", "all"],
        help="Periode scraping: 1day, 3days, weekly, monthly, all (default: all)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="all",
        help="Kategori: engagement,news,economic,social,technology,research,business,social_media,all (default: all)",
    )
    parser.add_argument(
        "--keywords-id",
        type=str,
        default=None,
        help="Custom keywords Indonesia (comma-separated, support multi-word dengan quote)",
    )
    parser.add_argument(
        "--keywords-gl",
        type=str,
        default=None,
        help="Custom keywords Global (comma-separated, support multi-word dengan quote)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Buka browser secara visual (debugging)",
    )
    parser.add_argument(
        "--explore-limit",
        type=int,
        default=EXPLORE_LIMIT,
        help=f"Jumlah tweet untuk mode explore (default: {EXPLORE_LIMIT})",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download videos via twittersaver.net untuk tweet yang sudah di-scrape",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Path spesifik file report JSON (untuk digunakan dengan --download)",
    )

    args = parser.parse_args()
    headless = HEADLESS and not args.no_headless

    if args.download:
        asyncio.run(run_downloader(
            report_path=args.report,
            headless=headless,
        ))
        return

    if args.mode == "explore":
        asyncio.run(run_explore_scraper(
            headless=headless,
            limit=args.explore_limit,
        ))
        return

    if args.period == "all":
        periods = PERIODS
    else:
        periods = [args.period]

    if args.category == "all":
        categories = CATEGORIES
    else:
        categories = [c.strip() for c in args.category.split(",")]

    custom_keywords_id = parse_keywords(args.keywords_id)
    custom_keywords_gl = parse_keywords(args.keywords_gl)

    asyncio.run(run_scraper(
        periods=periods,
        categories=categories,
        custom_keywords_id=custom_keywords_id,
        custom_keywords_gl=custom_keywords_gl,
        headless=headless,
    ))


if __name__ == "__main__":
    main()
