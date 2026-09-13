# Design: X/Twitter Video Engagement Scraper

## Architecture / Overview
Sistem ini dibangun dengan pendekatan modular menggunakan **Python 3.10+** dan **Playwright** untuk otomasi browser serta ekstraksi data web X/Twitter. Playwright digunakan untuk menangani dynamic client-side rendering (SPA), pemutaran video, dan scrolling tak terbatas.

Alur eksekusi:
1. **Config & Session Loader (`src/browser.py`)**: Memuat environment credentials (`auth_token`, `ct0`), menginisialisasi Chromium context dengan session cookies & anti-bot headers.
2. **Scraping Engine (`src/scraper.py`)**: Melakukan pencarian bertarget untuk Explore Indonesia (`lang:id filter:videos since:YYYY-MM-DD`) dan Global (`filter:videos since:YYYY-MM-DD`).
3. **Data Extractor (`src/extractor.py`)**: Mengekstrak URL video, caption, author info, dan mem-parse angka metrik (K/M to integer).
4. **Ranking & Data Model (`src/models.py`)**: Menghitung `total_score = likes + reposts + views` dan mengurutkan secara descending untuk mengambil Top 15 per kategori.
5. **Exporter (`main.py`)**: Menyimpan struktur data JSON ke 4 file output terpisah.

*(Requirements: 1, 2, 3, 4, 5, 6, 7)*

### Flow Diagram
```
main.py
  ├── hitung since_date_monthly = YYYY-MM-01
  ├── hitung since_date_3days = today - 3 days
  │
  ├── [1/4] scrape Indonesia monthly → top15_indonesia_monthly_YYYY-MM.json
  ├── [2/4] scrape Global monthly → top15_global_monthly_YYYY-MM.json
  ├── [3/4] scrape Indonesia 3days → top15_indonesia_3days_YYYY-MM-DD.json
  └── [4/4] scrape Global 3days → top15_global_3days_YYYY-MM-DD.json
```

## Components and Interfaces

### 1. `src/models.py`
Mendefinisikan skema Pydantic:
- `EngagementMetrics`: `likes: int`, `views: int`, `reposts: int`, `replies: int`, `total_score: int`
- `VideoTweet`: `tweet_url: str`, `video_url: Optional[str]`, `caption: str`, `username: str`, `handle: str`, `posted_at: Optional[str]`, `engagement: EngagementMetrics`
- `ScrapeReport`: `scraped_date: str`, `scraped_at: str`, `formula: str`, `total_items: int`, `indonesia_explore: List[VideoTweet]`, `global_explore: List[VideoTweet]`

### 2. `src/extractor.py`
- `parse_metric_value(raw: str) -> int`: Mengubah teks seperti `"1.5K"` menjadi `1500`, `"2M"` menjadi `2000000`.
- `calculate_engagement(likes, reposts, views, replies) -> EngagementMetrics`: Menghitung total skor formula kombinasi.

### 3. `src/browser.py`
- `init_browser_context(playwright, headless=True) -> Tuple[Browser, BrowserContext]`: Menginisialisasi browser dengan stealth viewport, user-agent realistis, dan injeksi cookie X.

### 4. `src/scraper.py`
- `scrape_top_videos(page, query, limit=15) -> List[VideoTweet]`: Menavigasi ke halaman pencarian X, melakukan scrolling, mengidentifikasi kartu tweet yang memuat video, mengumpulkan kandidat, dan merangking Top 15.
- `_async_extract_tweet(article) -> Optional[dict]`: Mengekstrak data tweet termasuk sensitive content check dan validasi video domain.
- `_is_nsfw(caption, handle) -> bool`: Memeriksa apakah tweet mengandung konten NSFW berdasarkan keyword dan handle patterns.
- `_validate_video_url(url: str) -> bool`: Memvalidasi video URL hanya dari domain trusted.

### 5. `src/config.py` (Updated)
- 4 `OUTPUT_FILE_PATTERN` untuk 4 file output
- `ALLOWED_VIDEO_DOMAINS = frozenset(["video.twimg.com"])` untuk validasi domain video
- `NSFW_KEYWORDS` diperluas dengan keyword Bahasa Indonesia dan English tambahan
- `NSFW_HANDLE_PATTERNS` diperluas dengan pattern Bahasa Indonesia tambahan

## Error Handling
- Penanganan elemen DOM yang hilang secara defensif menggunakan locator timeout dan pengecekan `.count() > 0`.
- Jika URL direct MP4 tidak bisa diekstrak dari DOM secara langsung (karena menggunakan blob atau HLS stream), sistem tetap menyimpan `tweet_url` dan menyetel `video_url` ke source yang terdeteksi atau null dengan graceful degradation.
- Penanganan network timeout dengan retry dan backoff singkat saat scrolling.
- Video URL dari domain tidak dikenal akan diabaikan (tidak error, hanya skip).

## Enterprise Standard Coverage
1. **Security** — Addressed: Kredensial akun X (`auth_token`, `ct0`) wajib dimuat dari `.env` dan diabaikan dari git (`.gitignore`). Tidak ada token yang dicetak ke file log atau console (Req 1.1). Domain whitelist mencegah redirect ke site berbahaya (Req 7.2).
2. **Reliability & Error Handling** — Addressed: Exception handling terstruktur di setiap iterasi kartu tweet; error pada 1 tweet tidak menghentikan proses scraping keseluruhan (Req 1.2, 5.4). 4 scraping tasks berjalan sequential, error 1 tidak mempengaruhi lainnya (Req 6.1).
3. **Observability** — Addressed: Logging progres setiap tahapan (inisialisasi browser, scraping Indonesia/Global × 2 mode, penyimpanan file output) dengan log timestamp (Req 6.1).
4. **Testing** — Addressed: Unit testing untuk `parse_metric_value`, kalkulasi engagement, dan validasi domain di `tests/test_extractor.py` (Req 7.3).
5. **Performance & Scalability** — Addressed: Penggunaan `seen_urls` set untuk mencegah duplikasi pemrosesan tweet yang sama saat scrolling; pembatasan scroll terukur agar tidak menimbulkan pemborosan resource memory.
6. **Documentation** — Addressed: Type hints di seluruh fungsi public, docstrings modular, dan petunjuk setup lengkap di `README.md`.
7. **Code Quality & Maintainability** — Addressed: Mematuhi aturan PEP 8, pemisahan dependensi logic dan scraping, serta validasi skema berbasis Pydantic.
8. **Compliance & Data Handling** — Addressed: Hanya mengumpulkan data publik dari tweet; tidak ada data personal sensitif yang disimpan selain username/handle pembuat tweet publik.
9. **CI/CD & Versioning** — Explicitly N/A: Scraper dijalankan sebagai CLI / scheduled standalone script lokal, tidak mengubah public API contract.
