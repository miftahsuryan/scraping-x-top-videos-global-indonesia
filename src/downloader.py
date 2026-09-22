"""Video downloader module using twittersaver.net as a proxy resolver.

Reads tweet URLs from scrape reports, resolves downloadable MP4 links via
twittersaver.net, and downloads the video files locally using httpx.
"""

import asyncio
import json
import logging
import random
import re
from pathlib import Path

import httpx

from src.config import (
    OUTPUT_DIR,
    TWITTERSAVER_API_EXPIRATION,
    TWITTERSAVER_API_SEARCH,
    TWITTERSAVER_API_TOKEN,
)

logger = logging.getLogger(__name__)

TWITTERSAVER_URL = "https://twittersaver.net/en"
TWITTERSAVER_RESULT_SELECTOR = "#data-result"
TWITTERSAVER_INPUT_SELECTOR = "#s_input"
TWITTERSAVER_BUTTON_SELECTOR = "button.btn-red"
RESULT_WAIT_TIMEOUT_MS = 30_000
RESULT_POLL_INTERVAL_MS = 1_000

DELAY_MIN = 3.0
DELAY_MAX = 5.0
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 2.0

DOWNLOAD_DIR = "OUTPUT-X/downloads"
CHUNK_SIZE = 8192


def _write_file(path: Path, data: bytes) -> None:
    """Write binary data to a file (blocking, for use with asyncio.to_thread)."""
    with open(path, "wb") as f:
        f.write(data)


def resolve_tweet_id(tweet_url: str) -> str:
    """Extract tweet ID from a tweet URL.

    Handles formats:
        https://x.com/user/status/1234567890
        https://twitter.com/user/status/1234567890
        https://x.com/user/status/1234567890?ref=abc
    """
    match = re.search(r"/status/(\d+)", tweet_url)
    if not match:
        return ""
    return match.group(1)


def resolve_tweet_id_from_filename(filename: str) -> str:
    """Extract tweet ID from filename like 'tweet_2101154346583154801.png'."""
    match = re.search(r"tweet_(\d+)", filename)
    return match.group(1) if match else ""


def extract_quality_score(text: str, url: str = "") -> int:
    """Extract numeric quality score from button text or URL path.

    Twittersaver uses pixel-height labels: "Download MP4 (1280p)", "(852p)", etc.
    Maps these to standard resolution tiers for ranking.
    """
    match = re.search(r"\((\d+)p?\)", text)
    if match:
        px = int(match.group(1))
        if px >= 1280:
            return 1080
        elif px >= 854:
            return 720
        elif px >= 640:
            return 480
        elif px >= 426:
            return 360
        return 240

    combined = (text + " " + url).lower()
    for quality in (2160, 1440, 1080, 720, 480, 360, 240):
        if str(quality) in combined:
            return quality
    return 0


def select_best_quality(download_links: list[str], surrounding_texts: list[str]) -> str | None:
    """Select the highest quality MP4 download link from available options.

    Uses three signals in priority order:
    1. Explicit quality label in surrounding text (1080 > 720 > 480)
    2. URL path heuristic (twittersaver lists qualities ascending, later = higher)
    3. Domain preference (video.twimg.com = original quality)
    """
    if not download_links:
        return None

    if len(download_links) == 1:
        return download_links[0]

    scored: list[tuple[int, int, str]] = []
    for idx, (url, text) in enumerate(zip(download_links, surrounding_texts)):
        quality = extract_quality_score(text, url)
        url_heuristic = len(download_links) - idx
        domain_bonus = 10000 if "video.twimg.com" in url else 0
        scored.append((quality, url_heuristic + domain_bonus, url))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return scored[0][2]


def download_path_for(tweet_id: str, scraped_date: str) -> Path:
    """Build the output file path for a downloaded video."""
    return Path(DOWNLOAD_DIR) / scraped_date / "videos" / tweet_id / "video.mp4"


def photo_path_for(tweet_id: str, scraped_date: str, index: int = 1) -> Path:
    """Build the output file path for a downloaded photo."""
    return Path(DOWNLOAD_DIR) / scraped_date / "photos" / tweet_id / f"photo_{index}.jpg"


async def resolve_video_url(page: "Page", tweet_url: str) -> str | None:  # noqa: F821
    """Resolve a tweet URL to a downloadable MP4 link via twittersaver.net.

    Navigates to twittersaver.net, inputs the tweet URL, waits for the
    result HTML, then parses it for the best quality download link.

    Args:
        page: Playwright page instance.
        tweet_url: The X/Twitter tweet URL to resolve.

    Returns:
        Direct MP4 download URL, or None if resolution failed.
    """
    try:
        await page.goto(TWITTERSAVER_URL, wait_until="domcontentloaded", timeout=45_000)
        await asyncio.sleep(2)

        input_el = page.locator(TWITTERSAVER_INPUT_SELECTOR)
        await input_el.fill("")
        await input_el.fill(tweet_url)
        await asyncio.sleep(0.5)

        await page.locator(TWITTERSAVER_BUTTON_SELECTOR).click()

        try:
            await page.wait_for_selector(
                f"{TWITTERSAVER_RESULT_SELECTOR} a, {TWITTERSAVER_RESULT_SELECTOR} img",
                timeout=RESULT_WAIT_TIMEOUT_MS,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Timeout waiting for result on twittersaver.net for %s", tweet_url)
            return None

        await asyncio.sleep(2)

        result_html = await page.inner_html(TWITTERSAVER_RESULT_SELECTOR)

        download_links, surrounding_texts = _parse_download_links(result_html)

        if not download_links:
            logger.warning("No download links found for %s", tweet_url)
            return None

        best_url = select_best_quality(download_links, surrounding_texts)
        logger.info(
            "Resolved %s -> %s (%d links found)",
            tweet_url,
            best_url[:80] + "..." if len(best_url) > 80 else best_url,
            len(download_links),
        )
        return best_url

    except Exception as e:  # noqa: BLE001
        logger.error("Failed to resolve video URL for %s: %s", tweet_url, e)
        return None


def _parse_download_links(html: str) -> tuple[list[str], list[str]]:
    """Parse twittersaver.net result HTML for download links and their quality labels.

    Uses HTMLParser to extract <a class="dl-success"> elements with their full text,
    which contains quality labels like "Download MP4 (1280p)".
    """
    from html.parser import HTMLParser

    urls: list[str] = []
    texts: list[str] = []

    class LinkExtractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self._in_a = False
            self._href = ""
            self._classes = ""
            self._text = ""

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "a":
                attr_dict = dict(attrs)
                self._href = attr_dict.get("href", "")
                self._classes = attr_dict.get("class", "")
                self._text = ""
                self._in_a = True

        def handle_data(self, data: str) -> None:
            if self._in_a:
                self._text += data

        def handle_endtag(self, tag: str) -> None:
            if tag == "a" and self._in_a:
                self._in_a = False
                href = self._href
                text = self._text.strip()
                is_video = (
                    "dl-success" in self._classes
                    and href.startswith("http")
                    and "Convert to MP3" not in text
                    and "Download Photo" not in text
                )
                if is_video:
                    urls.append(href)
                    texts.append(text)
                self._href = ""
                self._classes = ""
                self._text = ""

    parser = LinkExtractor()
    parser.feed(html)

    if not urls:
        video_pattern = re.compile(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', re.IGNORECASE)
        for match in video_pattern.finditer(html):
            url = match.group(1)
            start = max(0, match.start() - 200)
            end = min(len(html), match.end() + 200)
            context = re.sub(r"<[^>]+>", " ", html[start:end])
            urls.append(url)
            texts.append(context)

    return urls, texts


def _parse_photo_links(html: str) -> list[str]:
    """Parse twittersaver.net result HTML for photo download links.

    Photo HTML structure uses <a class="abutton is-success"> with "Download Photo" text.
    """
    from html.parser import HTMLParser

    urls: list[str] = []

    class PhotoExtractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self._in_a = False
            self._href = ""
            self._text = ""

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "a":
                attr_dict = dict(attrs)
                self._href = attr_dict.get("href", "")
                self._text = ""
                self._in_a = True

        def handle_data(self, data: str) -> None:
            if self._in_a:
                self._text += data

        def handle_endtag(self, tag: str) -> None:
            if tag == "a" and self._in_a:
                self._in_a = False
                text = self._text.strip()
                if "Download Photo" in text and self._href.startswith("http"):
                    urls.append(self._href)
                self._href = ""
                self._text = ""

    parser = PhotoExtractor()
    parser.feed(html)
    return urls


async def download_photo(url: str, output_path: Path) -> bool:
    """Download a photo file from the given URL using httpx."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            await asyncio.to_thread(_write_file, output_path, response.content)

        file_size = output_path.stat().st_size
        logger.info("Downloaded photo %s (%d bytes)", output_path.name, file_size)
        return True

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error downloading photo %s: %s", url, e.response.status_code)
        return False
    except httpx.RequestError as e:
        logger.error("Request error downloading photo %s: %s", url, e)
        return False
    except OSError as e:
        logger.error("File write error for photo %s: %s", output_path, e)
        return False


def _is_api_token_expired() -> bool:
    """Check if the twittersaver API token has expired."""
    import time

    if not TWITTERSAVER_API_EXPIRATION:
        return True
    try:
        exp_timestamp = int(TWITTERSAVER_API_EXPIRATION)
        return time.time() > exp_timestamp
    except (ValueError, TypeError):
        return True


async def resolve_video_url_api(tweet_url: str) -> str | None:
    """Resolve a tweet URL to a downloadable MP4 link via twittersaver.net API.

    Uses the AJAX search endpoint to avoid Playwright browser overhead.
    Falls back to None if the API token is expired or the request fails.
    """
    if _is_api_token_expired():
        logger.info("TwitterSaver API token expired, skipping API path")
        return None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Referer": "https://twittersaver.net/en",
        "Origin": "https://twittersaver.net",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
    }

    form_data = {
        "q": tweet_url,
        "t": "media",
        "lang": "en",
        "token": TWITTERSAVER_API_TOKEN,
        "exp": TWITTERSAVER_API_EXPIRATION,
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.post(
                TWITTERSAVER_API_SEARCH,
                data=form_data,
                headers=headers,
            )
            response.raise_for_status()

            result = response.json()
            html_data = result.get("data", "")
            if not html_data:
                logger.warning("API search returned no data for %s", tweet_url)
                return None

            download_links, surrounding_texts = _parse_download_links(html_data)
            if not download_links:
                logger.warning("No download links in API response for %s", tweet_url)
                return None

            best_url = select_best_quality(download_links, surrounding_texts)
            logger.info(
                "API resolved %s -> %s (%d links)",
                tweet_url,
                best_url[:80] + "..." if best_url and len(best_url) > 80 else best_url,
                len(download_links),
            )
            return best_url

    except httpx.HTTPStatusError as e:
        logger.error("API HTTP error for %s: %s", tweet_url, e.response.status_code)
        return None
    except httpx.RequestError as e:
        logger.error("API request error for %s: %s", tweet_url, e)
        return None
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("API parse error for %s: %s", tweet_url, e)
        return None


async def download_video(url: str, output_path: Path) -> bool:
    """Download a video file from the given URL using httpx streaming.

    Args:
        url: Direct MP4 download URL.
        output_path: Local file path to save the video.

    Returns:
        True if download succeeded, False otherwise.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client, \
                client.stream("GET", url) as response:
            response.raise_for_status()
            data = await response.aread()
            await asyncio.to_thread(_write_file, output_path, data)

        file_size = output_path.stat().st_size
        logger.info("Downloaded %s (%d bytes)", output_path.name, file_size)
        return True

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error downloading %s: %s", url, e.response.status_code)
        return False
    except httpx.RequestError as e:
        logger.error("Request error downloading %s: %s", url, e)
        return False
    except OSError as e:
        logger.error("File write error for %s: %s", output_path, e)
        return False


def _load_reports(index_path: Path, single_report: Path | None) -> list[dict]:
    """Load report data from index or single report file.

    Returns:
        List of dicts with keys: report_path, report_data, scraped_date.
    """
    reports: list[dict] = []

    if single_report:
        if not single_report.exists():
            logger.error("Report file not found: %s", single_report)
            return []
        data = json.loads(single_report.read_text(encoding="utf-8"))
        reports.append({
            "report_path": single_report,
            "report_data": data,
            "scraped_date": data.get("scraped_date", "unknown"),
        })
        return reports

    if not index_path.exists():
        logger.error("Index file not found: %s", index_path)
        return []

    index = json.loads(index_path.read_text(encoding="utf-8"))
    results = index.get("results", [])

    for entry in results:
        filename = entry.get("filename", "")
        if not filename:
            continue
        report_path = index_path.parent / filename
        if not report_path.exists():
            logger.warning("Report file not found: %s, skipping", report_path)
            continue
        data = json.loads(report_path.read_text(encoding="utf-8"))
        reports.append({
            "report_path": report_path,
            "report_data": data,
            "scraped_date": data.get("scraped_date", "unknown"),
        })

    return reports


def _should_skip(tweet: dict, already_downloaded_ids: set[str] | None = None) -> bool:
    """Check if a tweet should be skipped (already downloaded)."""
    download_path = tweet.get("download_path")
    if download_path and Path(download_path).exists():
        return True
    photo_paths = tweet.get("photo_paths", [])
    if photo_paths and all(Path(p).exists() for p in photo_paths if p):
        return True
    if already_downloaded_ids is not None:
        tid = resolve_tweet_id(tweet.get("tweet_url", ""))
        return tid in already_downloaded_ids
    return False


def _collect_downloaded_ids(downloads_dir: Path) -> set[str]:
    """Scan downloads folder and collect tweet IDs that have been downloaded."""
    downloaded_ids: set[str] = set()
    if not downloads_dir.is_dir():
        return downloaded_ids
    for f in downloads_dir.rglob("tweet_*.mp4"):
        tid = resolve_tweet_id_from_filename(f.name)
        if tid:
            downloaded_ids.add(tid)
    for f in downloads_dir.rglob("tweet_*.jpg"):
        tid = resolve_tweet_id_from_filename(f.name)
        if tid:
            downloaded_ids.add(tid)
    return downloaded_ids


def sync_downloads_with_screenshots(screenshots_dir: Path, downloads_dir: Path) -> int:
    """Delete download files that have no corresponding screenshot.

    Returns the number of files deleted.
    """
    screenshot_ids: set[str] = set()
    if screenshots_dir.is_dir():
        for f in screenshots_dir.rglob("tweet_*.png"):
            tid = resolve_tweet_id_from_filename(f.name)
            if tid:
                screenshot_ids.add(tid)

    if not downloads_dir.is_dir():
        return 0

    deleted = 0
    for ext in ("*.mp4", "*.jpg"):
        for f in downloads_dir.rglob(ext):
            tid = resolve_tweet_id_from_filename(f.name)
            if tid and tid not in screenshot_ids:
                f.unlink()
                logger.info("Deleted download (no screenshot): %s", f.name)
                deleted += 1
    return deleted


def _update_report(report_path: Path, report_data: dict, tweet_url: str, download_path: str) -> None:
    """Update the report JSON file with the download_path for a tweet."""
    for tweet in report_data.get("tweets", []):
        if tweet.get("tweet_url") == tweet_url:
            tweet["download_path"] = download_path
            break

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)


def _update_photo_paths(report_path: Path, report_data: dict, tweet_url: str, paths: list[str]) -> None:
    """Update the report JSON file with photo_paths for a tweet."""
    for tweet in report_data.get("tweets", []):
        if tweet.get("tweet_url") == tweet_url:
            tweet["photo_paths"] = paths
            break

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)


async def run_downloader(report_path: str | None = None, headless: bool = True, max_age_days: int | None = None) -> None:
    """Main orchestrator for the video download process.

    Reads tweet URLs from scrape reports, resolves download links via
    twittersaver.net, and downloads MP4 files locally.

    Args:
        report_path: Optional specific report file path. If None, reads from index.
        headless: Whether to run Playwright in headless mode.
        max_age_days: Skip download for tweets already scraped within last N days.
    """
    from src.browser import init_browser_context

    print("=" * 60)
    print("Video Downloader — TwitterSaver.net Proxy")
    print("=" * 60)

    index_path = Path(OUTPUT_DIR) / "index.json"
    single_report = Path(report_path) if report_path else None

    reports = _load_reports(index_path, single_report)
    if not reports:
        print("No reports found. Nothing to download.")
        return

    downloads_dir = Path(DOWNLOAD_DIR)
    already_downloaded_ids = _collect_downloaded_ids(downloads_dir)
    print(f"Found {len(already_downloaded_ids)} previously downloaded tweets")

    screenshots_dir = Path("OUTPUT-X/screenshots")
    screenshot_ids: set[str] = set()
    if screenshots_dir.is_dir():
        for f in screenshots_dir.rglob("tweet_*.png"):
            tid = resolve_tweet_id_from_filename(f.name)
            if tid:
                screenshot_ids.add(tid)
    print(f"Found {len(screenshot_ids)} tweets with screenshots")

    deleted = sync_downloads_with_screenshots(screenshots_dir, downloads_dir)
    if deleted:
        print(f"Synced: deleted {deleted} download files (no matching screenshot)")
        already_downloaded_ids = _collect_downloaded_ids(downloads_dir)

    total_tweets = 0
    skipped = 0
    resolved = 0
    downloaded = 0
    failed = 0

    try:
        from playwright.async_api import (
            async_playwright,  # type: ignore[import-not-found]
        )

        async with async_playwright() as p:
            browser, context = await init_browser_context(p, headless=headless)
            page = await context.new_page()

            for report_info in reports:
                report_path_obj = report_info["report_path"]
                report_data = report_info["report_data"]
                scraped_date = report_info["scraped_date"]
                tweets = report_data.get("tweets", [])

                print(f"\n[Report] {report_path_obj.name} — {len(tweets)} tweets")

                for tweet in tweets:
                    total_tweets += 1
                    tweet_url = tweet.get("tweet_url", "")
                    tweet_id = resolve_tweet_id(tweet_url)

                    if not tweet_id:
                        logger.warning("Could not extract tweet ID from %s, skipping", tweet_url)
                        failed += 1
                        continue

                    if _should_skip(tweet, already_downloaded_ids):
                        logger.info("Already downloaded: tweet_%s, skipping", tweet_id)
                        skipped += 1
                        continue

                    if screenshot_ids and tweet_id not in screenshot_ids:
                        logger.info("No screenshot for tweet_%s, skipping download", tweet_id)
                        skipped += 1
                        continue

                    media_type = tweet.get("media_type", "none")

                    if media_type == "video":
                        video_url = tweet.get("video_url")
                        if not video_url:
                            video_url = await resolve_video_url_api(tweet_url)
                        if not video_url:
                            for attempt in range(1, MAX_RETRIES + 1):
                                logger.info(
                                    "Resolving URL via Playwright (attempt %d/%d): %s",
                                    attempt, MAX_RETRIES, tweet_url,
                                )
                                video_url = await resolve_video_url(page, tweet_url)
                                if video_url:
                                    break
                                if attempt < MAX_RETRIES:
                                    wait = RETRY_BACKOFF_BASE ** attempt
                                    logger.info("Retrying in %.1fs...", wait)
                                    await asyncio.sleep(wait)

                        if video_url:
                            output_path = download_path_for(tweet_id, scraped_date)
                            resolved += 1
                            success = False
                            for attempt in range(1, MAX_RETRIES + 1):
                                logger.info(
                                    "Downloading video (attempt %d/%d): tweet_%s.mp4",
                                    attempt, MAX_RETRIES, tweet_id,
                                )
                                success = await download_video(video_url, output_path)
                                if success:
                                    break
                                if attempt < MAX_RETRIES:
                                    wait = RETRY_BACKOFF_BASE ** attempt
                                    logger.info("Retrying download in %.1fs...", wait)
                                    await asyncio.sleep(wait)
                            if success:
                                _update_report(report_path_obj, report_data, tweet_url, str(output_path))
                                downloaded += 1
                            else:
                                logger.error("Failed to download video for %s after retries", tweet_url)
                                failed += 1
                        else:
                            logger.warning("No video URL resolved for %s", tweet_url)
                            failed += 1

                    elif media_type == "photo":
                        photo_urls = tweet.get("photo_urls", [])
                        if not photo_urls and tweet.get("photo_url"):
                            photo_urls = [tweet["photo_url"]]

                        if photo_urls:
                            paths = []
                            for idx, url in enumerate(photo_urls, 1):
                                output_path = photo_path_for(tweet_id, scraped_date, idx)
                                success = await download_photo(url, output_path)
                                if success:
                                    paths.append(str(output_path))
                            resolved += 1
                            if paths:
                                _update_photo_paths(report_path_obj, report_data, tweet_url, paths)
                                downloaded += 1
                            else:
                                logger.error("Failed to download photos for %s", tweet_url)
                                failed += 1
                        else:
                            logger.warning("No photo URLs for %s", tweet_url)
                            failed += 1

                    else:
                        logger.info("Unknown media_type '%s' for tweet_%s, skipping", media_type, tweet_id)
                        skipped += 1

                    await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

            await browser.close()

    except Exception as e:  # noqa: BLE001
        logger.error("Fatal error in downloader: %s", e)

    print("\n" + "=" * 60)
    print("Download Summary:")
    print(f"  Total tweets processed: {total_tweets}")
    print(f"  Skipped (already downloaded): {skipped}")
    print(f"  URLs resolved: {resolved}")
    print(f"  Files downloaded: {downloaded}")
    print(f"  Failed: {failed}")
    print("=" * 60)
