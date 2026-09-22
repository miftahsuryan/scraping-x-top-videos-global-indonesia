import asyncio
import json
import logging
import os
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import Page

from src.config import (
    ALLOWED_VIDEO_DOMAINS,
    EXPLORE_MAX_SCROLLS,
    EXPLORE_MIN_FAVES,
    EXPLORE_SINCE_DAYS,
    MAX_SCROLLS,
    NSFW_HANDLE_PATTERNS,
    NSFW_KEYWORDS,
    OUTPUT_DIR,
)
from src.extractor import calculate_engagement, parse_metric_value
from src.models import VideoTweet


def load_recent_tweet_ids(days: int = 7) -> set[str]:
    """Scan all JSON report files from the last N days and collect tweet IDs.

    Args:
        days: Number of days to look back (default: 7).

    Returns:
        Set of tweet ID strings found in recent reports.
    """
    seen_ids: set[str] = set()
    today = date.today()  # noqa: DTZ011
    start_date = today - timedelta(days=days)
    base_dir = Path(OUTPUT_DIR)

    if not base_dir.is_dir():
        return seen_ids

    for f in base_dir.rglob("*.json"):
        if f.name == "index.json":
            continue
        try:
            file_date = date.fromisoformat(f.stem)
            if file_date >= start_date:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, dict) and "tweets" in data:
                        for t in data["tweets"]:
                            url = t.get("tweet_url", "")
                            tid = url.rstrip("/").split("/")[-1].split("?")[0]
                            if tid.isdigit():
                                seen_ids.add(tid)
        except (ValueError, json.JSONDecodeError):
            continue

    return seen_ids

logger = logging.getLogger(__name__)


def _is_nsfw(caption: str, handle: str) -> bool:
    """Check if tweet content or handle matches NSFW keywords/patterns."""
    text = (caption + " " + handle).lower()
    if any(kw in text for kw in NSFW_KEYWORDS):
        return True
    handle_lower = handle.lower()
    return any(pat in handle_lower for pat in NSFW_HANDLE_PATTERNS)


def _validate_media(url: str | None) -> bool:
    """Validate media URL is from a trusted domain."""
    if not url:
        return True
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname in ALLOWED_VIDEO_DOMAINS
    except Exception:  # noqa: BLE001
        return False


async def _check_sensitive_content(article) -> bool:
    """Check if tweet has sensitive content warning from X/Twitter."""
    warning = article.locator("div[data-testid='warningScreen']")
    return await warning.count() > 0


def _matches_custom_keywords(caption: str, keywords: list[str]) -> bool:
    """Check if caption matches any custom keyword (case-insensitive, any match)."""
    text = caption.lower()
    return any(kw.lower() in text for kw in keywords)


async def scrape_top_videos(
    page: Page,
    search_query: str,
    limit: int = 5,
    max_scrolls: int = MAX_SCROLLS,
    exclude_ids: set[str] | None = None,
) -> list[VideoTweet]:
    """Scrape top tweets from X search results, filtered for quality and NSFW content."""
    encoded_query = quote(search_query, safe="")
    search_url = f"https://x.com/search?q={encoded_query}&f=top"
    print(f"[Scraper] Query: {search_query}")
    print(f"[Scraper] URL: {search_url}")

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)
    except Exception as e:  # noqa: BLE001
        logger.warning("Navigation warning: %s", e)

    candidates: list[VideoTweet] = []
    seen_urls: set[str] = set()

    for scroll_idx in range(max_scrolls):
        articles = await page.locator("article[data-testid='tweet']").all()
        print(
            f"[Scraper] Scroll #{scroll_idx + 1} - Mendeteksi {len(articles)} tweet di viewport..."
        )

        for article in articles:
            try:
                if await _check_sensitive_content(article):
                    logger.info("Filtered sensitive content")
                    continue

                data = await _async_extract_tweet(article)
                if data is None:
                    continue

                if data["tweet_url"] in seen_urls:
                    continue
                seen_urls.add(data["tweet_url"])

                tweet_id = data["tweet_url"].rstrip("/").split("/")[-1].split("?")[0]
                if exclude_ids and tweet_id in exclude_ids:
                    continue

                if _is_nsfw(data["caption"], data["handle"]):
                    logger.info("Filtered NSFW: %s", data["tweet_url"])
                    continue

                if not _validate_media(data.get("video_url")):
                    logger.info("Filtered untrusted domain: %s", data["tweet_url"])
                    continue

                candidates.append(VideoTweet(**data))
            except Exception as e:  # noqa: BLE001
                logger.warning("Error processing tweet: %s", e)
                continue

        await page.mouse.wheel(0, 2500)
        await asyncio.sleep(2.5)

        if len(candidates) >= limit * 2:
            break

    candidates.sort(key=lambda t: t.engagement.total_score, reverse=True)
    top_results = candidates[:limit]
    print(
        f"[Scraper] Berhasil memfilter {len(top_results)} tweet teratas "
        f"dari total {len(candidates)} kandidat."
    )
    return top_results


async def _async_extract_tweet(article) -> dict | None:
    """Async extraction of tweet data from an article element."""
    media_locator = article.locator(
        "div[data-testid='videoPlayer'], div[data-testid='videoComponent'], video, div[data-testid='tweetPhoto']"
    )
    if await media_locator.count() == 0:
        return None

    link_locator = article.locator("a[href*='/status/']").first
    if await link_locator.count() == 0:
        return None
    href = await link_locator.get_attribute("href")
    if not href:
        return None

    tweet_url = f"https://x.com{href}" if href.startswith("/") else href
    clean_url = tweet_url.split("?")[0].split("/photo/")[0].split("/video/")[0]

    caption = ""
    tweet_text_el = article.locator("div[data-testid='tweetText']").first
    if await tweet_text_el.count() > 0:
        caption = await tweet_text_el.inner_text()

    name, handle = "Unknown", "@unknown"
    user_el = article.locator("div[data-testid='User-Name']").first
    if await user_el.count() > 0:
        user_raw = await user_el.inner_text()
        lines = [l.strip() for l in user_raw.split("\n") if l.strip()]
        if lines:
            name = lines[0]
        for line in lines:
            if line.startswith("@"):
                handle = line
                break

    direct_video_url = None
    video_tag = article.locator("video").first
    if await video_tag.count() > 0:
        src = await video_tag.get_attribute("src")
        if src and not src.startswith("blob:"):
            direct_video_url = src

    photo_urls: list[str] = []
    has_video_thumb = False
    if not direct_video_url:
        photo_tags = await article.locator("div[data-testid='tweetPhoto'] img").all()
        for img in photo_tags:
            src = await img.get_attribute("src")
            if src:
                photo_urls.append(src)

        VIDEO_THUMB_PATTERNS = ("amplify_video_thumb", "tweet_video_thumb", "ext_tw_video_thumb")
        real_photos = [url for url in photo_urls
                       if not any(pat in url for pat in VIDEO_THUMB_PATTERNS)]
        has_video_thumb = len(photo_urls) != len(real_photos)
        if has_video_thumb:
            photo_urls = []

    has_video_tag = await article.locator("video").count() > 0

    if direct_video_url or has_video_thumb or has_video_tag:
        media_type = "video"
    elif photo_urls:
        media_type = "photo"
    else:
        media_type = "none"

    posted_at = None
    time_el = article.locator("time").first
    if await time_el.count() > 0:
        posted_at = await time_el.get_attribute("datetime")

    likes = views = reposts = replies = 0
    like_btn = article.locator(
        "button[data-testid='like'], button[data-testid='unlike']"
    ).first
    if await like_btn.count() > 0:
        likes = parse_metric_value(await like_btn.inner_text())
    repost_btn = article.locator("button[data-testid='retweet']").first
    if await repost_btn.count() > 0:
        reposts = parse_metric_value(await repost_btn.inner_text())
    reply_btn = article.locator("button[data-testid='reply']").first
    if await reply_btn.count() > 0:
        replies = parse_metric_value(await reply_btn.inner_text())
    views_el = article.locator("a[href*='/analytics']").first
    if await views_el.count() > 0:
        views = parse_metric_value(await views_el.inner_text())

    eng = calculate_engagement(
        likes=likes, reposts=reposts, views=views, replies=replies
    )

    return {
        "tweet_url": clean_url,
        "media_type": media_type,
        "video_url": direct_video_url,
        "photo_urls": photo_urls,
        "caption": caption,
        "username": name,
        "handle": handle,
        "posted_at": posted_at,
        "engagement": eng,
        "source": "search",
    }


async def _capture_tweet_screenshot(
    page: Page,
    tweet_url: str,
    tweet_id: str,
    date_label: str,
) -> str | None:
    """Navigate to tweet URL and capture a screenshot of the tweet article."""
    if not tweet_id or not tweet_url:
        return None
    screenshots_dir = os.path.join("OUTPUT-X/screenshots", date_label)
    try:
        os.makedirs(screenshots_dir, exist_ok=True)
        await page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        article = page.locator("article[data-testid='tweet']").first
        if await article.count() == 0:
            logger.warning("No article found for tweet %s", tweet_id)
            return None
        filename = f"tweet_{tweet_id}.png"
        filepath = os.path.join(screenshots_dir, filename)
        await article.screenshot(path=filepath, scale="device", timeout=15000)
        return f"OUTPUT-X/screenshots/{date_label}/{filename}"
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to capture screenshot for tweet %s: %s", tweet_id, e)
        return None


async def scrape_explore_for_you(
    page: Page,
    limit: int = 15,
    max_scrolls: int = EXPLORE_MAX_SCROLLS,
    date_label: str = "",
    exclude_ids: set[str] | None = None,
) -> list[VideoTweet]:
    """Scrape top viral tweets using X Search 'Top' with broad media + engagement filters.

    Replaces the Explore 'For You' page, which now surfaces mostly text-only content
    that fails media filters. X Search f=top with filter:media provides engagement-ranked,
    media-rich results reliably.

    Args:
        page: Playwright page object.
        limit: Max tweets to return.
        max_scrolls: Max scroll iterations.
        date_label: Date label for screenshot folder.
        exclude_ids: Set of tweet IDs to skip (already scraped recently).
    """
    since_date = (date.today() - timedelta(days=EXPLORE_SINCE_DAYS)).strftime("%Y-%m-%d")  # noqa: DTZ011
    explore_query = f"filter:media min_faves:{EXPLORE_MIN_FAVES} since:{since_date} -is:retweet"
    encoded_query = quote(explore_query, safe="")
    search_url = f"https://x.com/search?q={encoded_query}&f=top"

    print("[Scraper] Mode: Explore (via Search Top)")
    print(f"[Scraper] Query: {explore_query}")
    print(f"[Scraper] URL: {search_url}")

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)
    except Exception as e:  # noqa: BLE001
        logger.warning("Navigation warning: %s", e)

    candidates: list[VideoTweet] = []
    seen_urls: set[str] = set()

    for scroll_idx in range(max_scrolls):
        articles = await page.locator("article[data-testid='tweet']").all()
        print(
            f"[Scraper] Scroll #{scroll_idx + 1}/{max_scrolls} - Mendeteksi {len(articles)} tweet di viewport..."
        )

        for article in articles:
            try:
                if await _check_sensitive_content(article):
                    logger.info("Filtered sensitive content")
                    continue

                data = await _async_extract_tweet(article)
                if data is None:
                    continue

                if data["tweet_url"] in seen_urls:
                    continue
                seen_urls.add(data["tweet_url"])

                if exclude_ids:
                    tid = data["tweet_url"].rstrip("/").split("/")[-1].split("?")[0]
                    if tid in exclude_ids:
                        logger.info("Skip duplicate (already scraped in last 7 days): %s", tid)
                        continue

                if _is_nsfw(data["caption"], data["handle"]):
                    logger.info("Filtered NSFW: %s", data["tweet_url"])
                    continue

                if not _validate_media(data.get("video_url")):
                    logger.info("Filtered untrusted domain: %s", data["tweet_url"])
                    continue

                data["source"] = "explore"
                candidates.append(VideoTweet(**data))
            except Exception as e:  # noqa: BLE001
                logger.warning("Error processing tweet: %s", e)
                continue

        await page.mouse.wheel(0, 3500)
        await asyncio.sleep(2)

    candidates.sort(key=lambda t: t.engagement.total_score, reverse=True)
    top_results = candidates[:limit]
    print(
        f"[Scraper] Berhasil memfilter {len(top_results)} tweet teratas "
        f"dari total {len(candidates)} kandidat."
    )

    if date_label and top_results:
        print(f"[Scraper] Mengambil screenshot untuk {len(top_results)} tweet teratas...")
        for tweet in top_results:
            tweet_id = tweet.tweet_url.rstrip("/").split("/")[-1].split("?")[0]
            shot_path = await _capture_tweet_screenshot(
                page, tweet.tweet_url, tweet_id, date_label
            )
            tweet.screenshot_path = shot_path

    return top_results
