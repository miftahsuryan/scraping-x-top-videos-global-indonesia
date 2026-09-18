# Design: X/Twitter Video Engagement Scraper

## Architecture / Overview
Sistem ini dibangun dengan pendekatan modular menggunakan **Python 3.10+** dan **Playwright** untuk otomasi browser serta ekstraksi data web X/Twitter. Playwright digunakan untuk menangani dynamic client-side rendering (SPA), pemutaran video, dan scrolling tak terbatas.

Dua mode operasi utama:
- **Explore Mode (Default)**: Scrape konten viral dari halaman Explore For You
- **Search Mode**: Scrape berdasarkan kategori dan keyword

Alur eksekusi:
1. **CLI Parser (`main.py`)**: Parse flag `--mode`, `--period`, `--category`, `--keywords-id`, `--keywords-gl` dengan default mode `explore`.
2. **Config Loader (`src/config.py`)**: Load default keywords per category (8 categories), CATEGORIES list, PERIODS list (`1day`, `3days`, `weekly`, `monthly`), SCRAPE_LIMIT (10 per periode).
3. **Session Loader (`src/browser.py`)**: Load environment credentials (`auth_token`, `ct0`), inisialisasi Chromium context dengan session cookies & anti-bot headers.
4. **Scraping Engine (`src/scraper.py`)**:
   - Explore: `scrape_explore_for_you()` - scrape dari halaman Explore
   - Search: `scrape_top_videos()` - scrape dari hasil pencarian
5. **Data Extractor (`src/extractor.py`)**: Mengekstrak URL media, caption, author info, dan mem-parse angka metrik (K/M to integer).
6. **Ranking & Data Model (`src/models.py`)**: Menghitung `total_score = likes + reposts + views` dan mengurutkan secara descending untuk mengambil Top 10 per periode.
7. **Exporter (`main.py`)**: Menyimpan struktur data JSON ke output files + `index.json`.

*(Requirements: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)*

### Flow Diagram

#### Explore Mode (Default)
```
python main.py
  |
  +-- Parse CLI: period, mode=explore
  |
  +-- [Loop Periods] 1day -> 3days -> weekly -> monthly
  |     |
  |     +-- Scrape Explore For You -> filter -> rank -> Top 10
  |     +-- Save to OUTPUT-X/explore/explore_{period}_{date}.json
  |
  +-- Generate OUTPUT-X/index.json (overwrite)
```

#### Search Mode
```
python main.py --mode search --category news
  |
  +-- Parse CLI: period, category, keywords-id, keywords-gl
  |
  +-- [Loop Periods] 1day -> 3days -> weekly -> monthly
  |   +-- [Loop Categories] engagement -> news -> economic -> ...
  |     +-- [Loop Locales] indonesia -> global
  |           |
  |           +-- Build query: keywords + filter:media + min_faves + -is:retweet + lang:id
  |           +-- Scrape -> filter -> rank -> Top 10
  |           +-- Save to OUTPUT-X/{locale}/{category}/{category}_{period}_{date}.json
  |
  +-- Generate OUTPUT-X/index.json (overwrite)
```

### Output Structure

#### Explore Mode
```
OUTPUT-X/
  index.json
  explore/
    explore_1day_2026-09-18.json
    explore_3days_2026-09-18.json
    explore_weekly_2026-W38.json
    explore_monthly_2026-09.json
```

#### Search Mode
```
OUTPUT-X/
  index.json
  indonesia/
    engagement/
      engagement_1day_2026-09-18.json
      engagement_3days_2026-09-18.json
      engagement_weekly_2026-W38.json
      engagement_monthly_2026-09.json
    news/
    economic/
    social/
    technology/
    research/
    business/
    social_media/
  global/
    engagement/
    news/
    economic/
    social/
    technology/
    research/
    business/
    social_media/
```

## Components and Interfaces

### 1. `src/config.py`
- `DEFAULT_KEYWORDS_ID`: dict[str, list[str]] - default keywords per category (ID)
- `DEFAULT_KEYWORDS_GL`: dict[str, list[str]] - default keywords per category (GL)
- `CATEGORIES`: list[str] - `["engagement", "news", "economic", "social", "technology", "research", "business", "social_media"]`
- `PERIODS`: list[str] - `["1day", "3days", "weekly", "monthly"]`
- `MIN_FAVES`: dict[str, int] - `{"1day": 100, "3days": 500, "weekly": 1000, "monthly": 1000}`
- `SCRAPE_LIMIT`: dict[str, int] - `{"1day": 10, "3days": 10, "weekly": 10, "monthly": 10}`
- `parse_keywords(raw: str | None) -> list[str]` - parse comma-separated keywords, support multi-word dengan quote

### 2. `src/models.py`
- `EngagementMetrics`: `likes: int`, `views: int`, `reposts: int`, `replies: int`, `total_score: int`
- `VideoTweet`: `tweet_url: str`, `video_url: Optional[str]`, `caption: str`, `username: str`, `handle: str`, `posted_at: Optional[str]`, `engagement: EngagementMetrics`, `source: str`
- `ScrapeReport`: `period: str`, `category: str`, `locale: str`, `scraped_date: str`, `scraped_at: str`, `formula: str`, `mode: str`, `total_items: int`, `tweets: List[VideoTweet]`

### 3. `src/extractor.py`
- `parse_metric_value(raw: str) -> int`: Mengubah teks seperti `"1.5K"` menjadi `1500`.
- `calculate_engagement(likes, reposts, views, replies) -> EngagementMetrics`: Menghitung total skor formula kombinasi.

### 4. `src/browser.py`
- `init_browser_context(playwright, headless=True) -> Tuple[Browser, BrowserContext]`: Inisialisasi browser dengan stealth viewport, user-agent realistis, dan injeksi cookie X.

### 5. `src/scraper.py`
- `scrape_top_videos(page, query, limit=10) -> List[VideoTweet]`: Scrape top tweets dari X search results (Search Mode).
- `scrape_explore_for_you(page, limit=10) -> List[VideoTweet]`: Scrape top tweets dari X Explore For You (Explore Mode).
- `_async_extract_tweet(article) -> Optional[dict]`: Mengekstrak data tweet termasuk sensitive content check dan validasi media.
- `_is_nsfw(caption, handle) -> bool`: NSFW check.
- `_validate_media(url: str) -> bool`: Validasi media URL.
- `_check_sensitive_content(article) -> bool`: Check sensitive content warning.

### 6. `main.py`
- CLI parser: `--mode`, `--period`, `--category`, `--keywords-id`, `--keywords-gl`, `--explore-limit`
- Default mode: `explore`
- `run_explore_scraper()`: Fungsi utama untuk Explore Mode
- `run_scraper()`: Fungsi utama untuk Search Mode
- `get_since_date(period)`: Hitung since_date berdasarkan periode (termasuk `1day`)
- `get_date_label(period)`: Generate label tanggal untuk filename
- Folder structure creation: `OUTPUT-X/explore/` atau `OUTPUT-X/{locale}/{category}/`
- Filename generation: `{prefix}_{period}_{date}.json`
- Index.json generation: overwrite setiap run

## Error Handling
- Penanganan elemen DOM yang hilang secara defensif menggunakan locator timeout dan pengecekan `.count() > 0`.
- Video/media URL dari domain tidak dikenal akan diabaikan (tidak error, hanya skip).
- Penanganan network timeout dengan retry dan backoff singkat saat scrolling.
- Error pada 1 tweet tidak menghentikan proses scraping keseluruhan.

## Enterprise Standard Coverage
1. **Security** -- Addressed: Kredensial akun X dimuat dari `.env` dan diabaikan dari git. Domain whitelist.
2. **Reliability & Error Handling** -- Addressed: Exception handling per tweet; error 1 tidak cascade. 4 scraping tasks sequential (Explore Mode).
3. **Observability** -- Addressed: Logging progres per period, mode.
4. **Testing** -- Addressed: Unit testing untuk `parse_metric_value`, `calculate_engagement`, `parse_keywords`, web schemas.
5. **Performance & Scalability** -- Addressed: `seen_urls` set, pembatasan scroll, limit 10 per periode.
6. **Documentation** -- Addressed: Type hints, docstrings, `README.md`, `docs/USAGE.md`, `docs/FAQ.md`.
7. **Code Quality & Maintainability** -- Addressed: PEP 8, modular, Pydantic validation.
8. **Compliance & Data Handling** -- Addressed: Hanya data publik dari tweet.
9. **CI/CD & Versioning** -- Explicitly N/A: CLI standalone script lokal.
