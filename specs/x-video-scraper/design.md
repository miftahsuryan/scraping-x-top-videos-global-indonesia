# Design: X/Twitter Video Engagement Scraper

## Architecture / Overview
Sistem ini dibangun dengan pendekatan modular menggunakan **Python 3.10+** dan **Playwright** untuk otomasi browser serta ekstraksi data web X/Twitter. Playwright digunakan untuk menangani dynamic client-side rendering (SPA), pemutaran video, dan scrolling tak terbatas.

Alur eksekusi:
1. **CLI Parser (`main.py`)**: Parse flag `--period`, `--category`, `--keywords-id`, `--keywords-gl` dengan default behavior (all period, all category).
2. **Config Loader (`src/config.py`)**: Load default keywords per category (6 categories × 2 locale), CATEGORIES list, PERIODS list.
3. **Session Loader (`src/browser.py`)**: Load environment credentials (`auth_token`, `ct0`), inisialisasi Chromium context dengan session cookies & anti-bot headers.
4. **Scraping Engine (`src/scraper.py`)**: Scrape per kombinasi (category × period × locale), gunakan keyword match logic (case-insensitive, any match), filter `filter:media -is:retweet`, dynamic `min_faves` per period.
5. **Data Extractor (`src/extractor.py`)**: Mengekstrak URL media, caption, author info, dan mem-parse angka metrik (K/M to integer).
6. **Ranking & Data Model (`src/models.py`)**: Menghitung `total_score = likes + reposts + views` dan mengurutkan secara descending untuk mengambil Top 5/10 per kategori.
7. **Exporter (`main.py`)**: Menyimpan struktur data JSON ke 36 file output + `index.json`.

*(Requirements: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)*

### Flow Diagram
```
python main.py --period all --category all
  │
  ├── Parse CLI: period, category, keywords-id, keywords-gl
  │
  ├── [Loop Periods] 3days → weekly → monthly
  │   └── [Loop Categories] engagement → news → economic → social → technology → research
  │       └── [Loop Locales] indonesia → global
  │           │
  │           ├── Build query: keywords + filter:media + min_faves + -is:retweet + lang:id
  │           ├── Scrape → filter → rank → Top 5 (3days) / Top 10 (weekly/monthly)
  │           └── Save to output/{locale}/{category}/{category}_{period}_{date}.json
  │
  └── Generate output/index.json (overwrite)
```

### Output Structure
```
output/
├── index.json
├── indonesia/
│   ├── engagement/
│   │   ├── engagement_3days_2026-09-14.json
│   │   ├── engagement_week_2026-W37.json
│   │   └── engagement_month_2026-09.json
│   ├── news/
│   │   ├── news_3days_2026-09-14.json
│   │   ├── news_week_2026-W37.json
│   │   └── news_month_2026-09.json
│   ├── economic/ ...
│   ├── social/ ...
│   ├── technology/ ...
│   └── research/ ...
└── global/
    ├── engagement/ ...
    ├── news/ ...
    ├── economic/ ...
    ├── social/ ...
    ├── technology/ ...
    └── research/ ...
```

## Components and Interfaces

### 1. `src/config.py` (Rewrite)
- `DEFAULT_KEYWORDS_ID`: dict[str, list[str]] — default keywords per category (ID)
- `DEFAULT_KEYWORDS_GL`: dict[str, list[str]] — default keywords per category (GL)
- `CATEGORIES`: list[str] — `["engagement", "news", "economic", "social", "technology", "research"]`
- `PERIODS`: list[str] — `["3days", "weekly", "monthly"]`
- `MIN_FAVES`: dict[str, int] — `{"3days": 500, "weekly": 1000, "monthly": 1000}`
- `parse_keywords(raw: str | None) -> list[str]` — parse comma-separated keywords, support multi-word dengan quote

### 2. `src/models.py` (Update)
- `EngagementMetrics`: `likes: int`, `views: int`, `reposts: int`, `replies: int`, `total_score: int`
- `VideoTweet`: `tweet_url: str`, `video_url: Optional[str]`, `caption: str`, `username: str`, `handle: str`, `posted_at: Optional[str]`, `engagement: EngagementMetrics`
- `ScrapeReport`: `period: str`, `category: str`, `locale: str`, `scraped_date: str`, `scraped_at: str`, `formula: str`, `total_items: int`, `tweets: List[VideoTweet]`

### 3. `src/extractor.py`
- `parse_metric_value(raw: str) -> int`: Mengubah teks seperti `"1.5K"` menjadi `1500`.
- `calculate_engagement(likes, reposts, views, replies) -> EngagementMetrics`: Menghitung total skor formula kombinasi.

### 4. `src/browser.py`
- `init_browser_context(playwright, headless=True) -> Tuple[Browser, BrowserContext]`: Inisialisasi browser dengan stealth viewport, user-agent realistis, dan injeksi cookie X.

### 5. `src/scraper.py` (Rewrite)
- `scrape_top_videos(page, query, limit=5) -> List[VideoTweet]`: Scrape top tweets dari X search results.
- `_async_extract_tweet(article) -> Optional[dict]`: Mengekstrak data tweet termasuk sensitive content check dan validasi media.
- `_is_nsfw(caption, handle) -> bool`: NSFW check.
- `_validate_media(url: str) -> bool`: Validasi media URL.
- `_check_sensitive_content(article) -> bool`: Check sensitive content warning.
- `_matches_custom_keywords(caption, keywords) -> bool`: Keyword match logic (case-insensitive, any match).

### 6. `main.py` (Rewrite)
- CLI parser: `--period`, `--category`, `--keywords-id`, `--keywords-gl`
- Default behavior: all period, all category, all locale
- Folder structure creation: `output/{locale}/{category}/`
- Filename generation: `{category}_{period}_{date}.json`
- Query construction: dynamic keywords + filters
- Index.json generation: overwrite setiap run

## Error Handling
- Penanganan elemen DOM yang hilang secara defensif menggunakan locator timeout dan pengecekan `.count() > 0`.
- Video/media URL dari domain tidak dikenal akan diabaikan (tidak error, hanya skip).
- Penanganan network timeout dengan retry dan backoff singkat saat scrolling.
- Error pada 1 tweet tidak menghentikan proses scraping keseluruhan.

## Enterprise Standard Coverage
1. **Security** — Addressed: Kredensial akun X dimuat dari `.env` dan diabaikan dari git (Req 1.1). Domain whitelist (Req 7.3).
2. **Reliability & Error Handling** — Addressed: Exception handling per tweet; error 1 tidak cascade (Req 1.2). 36 scraping tasks sequential (Req 8.4).
3. **Observability** — Addressed: Logging progres per category, period, locale (Req 6.1).
4. **Testing** — Addressed: Unit testing untuk `parse_metric_value`, `calculate_engagement`, `parse_keywords` (Req 4, 9).
5. **Performance & Scalability** — Addressed: `seen_urls` set, pembatasan scroll, dynamic limit 5/10 (Req 8.1).
6. **Documentation** — Addressed: Type hints, docstrings, `README.md`, `docs/USAGE.md`, `docs/FAQ.md` (Req 12).
7. **Code Quality & Maintainability** — Addressed: PEP 8, modular, Pydantic validation (Req 7).
8. **Compliance & Data Handling** — Addressed: Hanya data publik dari tweet (Req 7).
9. **CI/CD & Versioning** — Explicitly N/A: CLI standalone script lokal.
