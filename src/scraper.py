import asyncio
import logging

from playwright.async_api import Page

from src.config import (
    ALLOWED_TOPICS,
    ALLOWED_VIDEO_DOMAINS,
    MAX_SCROLLS,
    MIN_ENGAGEMENT_SCORE,
    NSFW_HANDLE_PATTERNS,
    NSFW_KEYWORDS,
    SCRAPE_LIMIT,
)
from src.extractor import calculate_engagement, parse_metric_value
from src.models import VideoTweet

logger = logging.getLogger(__name__)


def _is_nsfw(caption: str, handle: str) -> bool:
    """Check if tweet content or handle matches NSFW keywords/patterns."""
    text = (caption + " " + handle).lower()
    if any(kw in text for kw in NSFW_KEYWORDS):
        return True
    handle_lower = handle.lower()
    return any(pat in handle_lower for pat in NSFW_HANDLE_PATTERNS)


def _validate_video_url(url: str | None) -> bool:
    """Validate video URL is from a trusted domain."""
    if not url:
        return True  # No video URL is allowed (will be null)
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


def _matches_topic(caption: str) -> bool:
    """Check if tweet caption matches any of the allowed topics."""
    text = caption.lower()
    for keywords in ALLOWED_TOPICS.values():
        if any(kw in text for kw in keywords):
            return True
    return False


def _extract_tweet_data(article) -> dict | None:
    """Extract structured data from a single tweet article element."""
    # 1. Must have video
    video_locator = article.locator(
        "div[data-testid='videoPlayer'], div[data-testid='videoComponent'], video"
    )

    async def check():
        return await video_locator.count()

    if not asyncio.get_event_loop().run_until_complete(check()):
        return None

    # 2. Get tweet URL
    link_locator = article.locator("a[href*='/status/']").first

    async def get_href():
        if await link_locator.count() == 0:
            return None
        return await link_locator.get_attribute("href")

    href = asyncio.get_event_loop().run_until_complete(get_href())
    if not href:
        return None

    tweet_url = f"https://x.com{href}" if href.startswith("/") else href
    clean_url = tweet_url.split("?")[0].split("/photo/")[0].split("/video/")[0]

    # 3. Caption
    caption = ""
    tweet_text_el = article.locator("div[data-testid='tweetText']").first

    async def get_caption():
        if await tweet_text_el.count() > 0:
            return await tweet_text_el.inner_text()
        return ""

    caption = asyncio.get_event_loop().run_until_complete(get_caption())

    # 4. User info
    user_el = article.locator("div[data-testid='User-Name']").first

    async def get_user():
        name, handle = "Unknown", "@unknown"
        if await user_el.count() > 0:
            raw = await user_el.inner_text()
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            if lines:
                name = lines[0]
            for line in lines:
                if line.startswith("@"):
                    handle = line
                    break
        return name, handle

    name, handle = asyncio.get_event_loop().run_until_complete(get_user())

    # 5. Video URL
    async def get_video():
        vt = article.locator("video").first
        if await vt.count() > 0:
            src = await vt.get_attribute("src")
            if src and not src.startswith("blob:"):
                return src
        return None

    direct_video_url = asyncio.get_event_loop().run_until_complete(get_video())

    # 6. Engagement metrics
    async def get_metrics():
        likes = views = reposts = replies = 0
        lb = article.locator("button[data-testid='like'], button[data-testid='unlike']").first
        if await lb.count() > 0:
            likes = parse_metric_value(await lb.inner_text())
        rb = article.locator("button[data-testid='retweet']").first
        if await rb.count() > 0:
            reposts = parse_metric_value(await rb.inner_text())
        pb = article.locator("button[data-testid='reply']").first
        if await pb.count() > 0:
            replies = parse_metric_value(await pb.inner_text())
        vl = article.locator("a[href*='/analytics']").first
        if await vl.count() > 0:
            views = parse_metric_value(await vl.inner_text())
        return likes, reposts, views, replies

    likes, reposts, views, replies = asyncio.get_event_loop().run_until_complete(
        get_metrics()
    )
    eng = calculate_engagement(
        likes=likes, reposts=reposts, views=views, replies=replies
    )

    return {
        "tweet_url": clean_url,
        "video_url": direct_video_url,
        "caption": caption,
        "username": name,
        "handle": handle,
        "posted_at": None,
        "engagement": eng,
    }


async def scrape_top_videos(
    page: Page,
    search_query: str,
    limit: int = SCRAPE_LIMIT,
    max_scrolls: int = MAX_SCROLLS,
) -> list[VideoTweet]:
    """
    Scrape top video tweets from X search results, filtered for quality and NSFW content.
    """
    encoded_query = search_query.replace(" ", "%20")
    search_url = f"https://x.com/search?q={encoded_query}&f=top"
    print(f"[Scraper] Mengakses: {search_url}")

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
                # Check sensitive content warning first
                if await _check_sensitive_content(article):
                    logger.info("Filtered sensitive content: tweet in viewport")
                    continue

                data = await _async_extract_tweet(article)
                if data is None:
                    continue

                if data["tweet_url"] in seen_urls:
                    continue
                seen_urls.add(data["tweet_url"])

                if _is_nsfw(data["caption"], data["handle"]):
                    logger.info("Filtered NSFW: %s", data["tweet_url"])
                    continue

                if not _validate_video_url(data.get("video_url")):
                    logger.info("Filtered untrusted video domain: %s", data["tweet_url"])
                    continue

                if not _matches_topic(data["caption"]):
                    logger.debug("Filtered no-topic: %s", data["tweet_url"])
                    continue

                if data["engagement"].total_score < MIN_ENGAGEMENT_SCORE:
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
        f"[Scraper] Berhasil memfilter {len(top_results)} video teratas "
        f"dari total {len(candidates)} kandidat (setelah NSFW & engagement filter)."
    )
    return top_results


async def _async_extract_tweet(article) -> dict | None:
    """Async extraction of tweet data from an article element."""
    video_locator = article.locator(
        "div[data-testid='videoPlayer'], div[data-testid='videoComponent'], video"
    )
    if await video_locator.count() == 0:
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
        "video_url": direct_video_url,
        "caption": caption,
        "username": name,
        "handle": handle,
        "posted_at": posted_at,
        "engagement": eng,
    }


async def scrape_explore_feed(
    page: Page,
    limit: int = SCRAPE_LIMIT,
    max_scrolls: int = MAX_SCROLLS,
) -> list[VideoTweet]:
    """
    Scrape trending video tweets from the X Explore page feed.
    """
    print("[Scraper] Mengakses Explore feed: https://x.com/explore")

    try:
        await page.goto(
            "https://x.com/explore", wait_until="domcontentloaded", timeout=45000
        )
        await asyncio.sleep(5)
    except Exception as e:  # noqa: BLE001
        logger.warning("Navigation warning: %s", e)

    candidates: list[VideoTweet] = []
    seen_urls: set[str] = set()

    for scroll_idx in range(max_scrolls):
        articles = await page.locator("article[data-testid='tweet']").all()
        print(
            f"[Scraper] Explore scroll #{scroll_idx + 1} - "
            f"Mendeteksi {len(articles)} tweet di viewport..."
        )

        for article in articles:
            try:
                # Check sensitive content warning first
                if await _check_sensitive_content(article):
                    logger.info("Filtered sensitive content: tweet in viewport")
                    continue

                data = await _async_extract_tweet(article)
                if data is None:
                    continue

                if data["tweet_url"] in seen_urls:
                    continue
                seen_urls.add(data["tweet_url"])

                if _is_nsfw(data["caption"], data["handle"]):
                    logger.info("Filtered NSFW: %s", data["tweet_url"])
                    continue

                if not _validate_video_url(data.get("video_url")):
                    logger.info("Filtered untrusted video domain: %s", data["tweet_url"])
                    continue

                if not _matches_topic(data["caption"]):
                    logger.debug("Filtered no-topic: %s", data["tweet_url"])
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
        f"[Scraper] Explore feed: {len(top_results)} video teratas "
        f"dari total {len(candidates)} kandidat."
    )
    return top_results
