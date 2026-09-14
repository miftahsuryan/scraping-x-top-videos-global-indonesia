# Requirements: X/Twitter Video Engagement Scraper (6 Categories, 3 Periods, 2 Locales)

## Introduction
Fitur ini bertujuan untuk mengumpulkan (scraping) dan meranking tweet di X (Twitter) dengan tingkat keterlibatan (engagement) tertinggi, mencakup 6 kategori konten:
- **Engagement**: Video viral dengan tingkat engagement tinggi
- **News**: Headlines dan berita terkini
- **Economic**: Insight ekonomi dan pasar
- **Social**: Isu sosial dan kesejahteraan
- **Technology**: Tech, AI, gadget, dan startup
- **Research**: Penelitian dan studi terbaru

Sistem menghasilkan **36 file output** per sesi scraping:
- 6 kategori × 3 periode (3days, weekly, monthly) × 2 locale (Indonesia, Global)

Output disimpan dalam format JSON terstruktur dengan struktur folder berbeda per category dan period.

## Acceptance Criteria (EARS Format)

### Requirement 1: Autentikasi dan Manajemen Sesi
- **REQ-1.1**: IF variabel lingkungan `X_AUTH_TOKEN` dan `X_CT0` tersedia di `.env`, THEN THE SYSTEM SHALL menginjeksi cookie autentikasi ke dalam browser context Playwright sebelum melakukan navigasi.
- **REQ-1.2**: IF cookie autentikasi tidak valid atau kedaluwarsa, THEN THE SYSTEM SHALL memunculkan pesan peringatan yang jelas dan menghentikan proses scraping secara aman tanpa crash.
- **REQ-1.3**: WHEN melakukan navigasi dan scrolling pada X/Twitter, THEN THE SYSTEM SHALL menerapkan penundaan (delay) dinamis dan user-agent modern untuk menghindari deteksi bot.

### Requirement 2: Pencarian dan Penyaringan Tweet Video (Indonesia & Global)
- **REQ-2.1**: WHEN melakukan scraping untuk Explore Indonesia, THEN THE SYSTEM SHALL mencari tweet video menggunakan filter `lang:id filter:videos` untuk rentang waktu hari tersebut (since tanggal target).
- **REQ-2.2**: WHEN melakukan scraping untuk Explore Global, THEN THE SYSTEM SHALL mencari tweet video global menggunakan filter `filter:videos` untuk rentang waktu hari tersebut.
- **REQ-2.3**: WHEN mengevaluasi tweet yang ditemukan, THEN THE SYSTEM SHALL memastikan bahwa tweet tersebut memuat elemen media video asli.
- **REQ-2.4**: IF tweet berupa teks murni, gambar diam (foto), atau tautan artikel tanpa video player tertanam, THEN THE SYSTEM SHALL mengabaikan tweet tersebut.

### Requirement 3: Ekstraksi Data Tweet dan Media
- **REQ-3.1**: WHEN tweet video yang valid diproses, THEN THE SYSTEM SHALL mengekstrak:
  - Tautan URL tweet (`https://x.com/.../status/...`)
  - Tautan langsung file video (MP4 URL jika dapat diekstrak dari DOM atau network stream)
  - Teks/caption utama tweet
  - Nama dan handle/username pembuat tweet (`@handle`)
  - Metrik keterlibatan: Likes, Views, Reposts (retweets/quotes), dan Replies.
- **REQ-3.2**: WHEN metrik engagement diformat dengan singkatan angka (misal: "1.2K", "3.4M", "500"), THEN THE SYSTEM SHALL mengonversi format tersebut menjadi bilangan bulat (integer).

### Requirement 4: Formula Engagement dan Pemeringkatan
- **REQ-4.1**: WHEN menghitung skor keterlibatan untuk setiap kandidat tweet, THEN THE SYSTEM SHALL menggunakan formula kombinasi:
  $$\text{Engagement Score} = \text{Likes} + \text{Reposts} + \text{Views}$$
- **REQ-4.2**: WHEN melakukan pemeringkatan, THEN THE SYSTEM SHALL mengurutkan tweet secara menurun (descending) berdasarkan `Engagement Score`.
- **REQ-4.3**: WHEN proses pemeringkatan selesai, THEN THE SYSTEM SHALL memilih tepat 15 video peringkat teratas untuk kategori Indonesia dan 15 video peringkat teratas untuk kategori Global (total 30 video).

### Requirement 5: Format dan Penyimpanan Output
- **REQ-5.1**: WHEN pengumpulan dan pemeringkatan data selesai, THEN THE SYSTEM SHALL menyimpan hasilnya ke file JSON di direktori `output/`.
- **REQ-5.2**: IF direktori `output/` belum ada, THEN THE SYSTEM SHALL membuat direktori tersebut secara otomatis.
- **REQ-5.3**: THE SYSTEM SHALL menyusun struktur data JSON dengan metadata (`scraped_date`, `scraped_at`, `formula`, `total_items`) serta daftar terpisah untuk `indonesia_explore` dan `global_explore`.

### Requirement 6: 4 File Output (Bulanan + 3 Hari)
- **REQ-6.1**: WHEN menjalankan scraping, THEN THE SYSTEM SHALL menghasilkan 4 file output terpisah:
  - `top15_indonesia_monthly_YYYY-MM.json` (since tanggal 1 bulan target)
  - `top15_global_monthly_YYYY-MM.json` (since tanggal 1 bulan target)
  - `top15_indonesia_3days_YYYY-MM-DD.json` (since 3 hari sebelum tanggal eksekusi)
  - `top15_global_3days_YYYY-MM-DD.json` (since 3 hari sebelum tanggal eksekusi)
- **REQ-6.2**: Setiap file output SHALL menggunakan struktur `ScrapeReport` yang sama.
- **REQ-6.3**: `since_date` untuk mode 3 days dihitung dari tanggal eksekusi dikurangi 3 hari (format: `YYYY-MM-DD`).
- **REQ-6.4**: Total video yang dihasilkan per sesi scraping adalah 60 video (4 × 15).

### Requirement 7: NSFW Filter Diperkuat
- **REQ-7.1**: THE SYSTEM SHALL memperluas daftar `NSFW_KEYWORDS` dengan keyword Bahasa Indonesia tambahan (misal: "bokep", "bugil", "telanjang", "ngentot", "memek", "kontol") dan keyword English tambahan.
- **REQ-7.2**: THE SYSTEM SHALL memperluas daftar `NSFW_HANDLE_PATTERNS` dengan pattern Bahasa Indonesia tambahan (misal: "bugil", "telanjang", "bokep", "sarung").
- **REQ-7.3**: THE SYSTEM SHALL memvalidasi `video_url` hanya berasal dari domain trusted yang terdaftar di `ALLOWED_VIDEO_DOMAINS` (misal: `video.twimg.com`). IF video_url berasal dari domain tidak dikenal, THEN video_url diabaikan.
- **REQ-7.4**: THE SYSTEM SHALL mendeteksi sensitive content warning dari X/Twitter dengan mengecek keberadaan `div[data-testid='warningScreen']` pada tweet. IF sensitive content warning terdeteksi, THEN tweet tersebut diabaikan.
- **REQ-7.5**: IF tweet terdeteksi sebagai NSFW berdasarkan kombinasi caption, handle, domain video, atau sensitive content warning, THEN THE SYSTEM SHALL mengabaikan tweet tersebut dari hasil scraping.

### Requirement 8: 6 Categories, 3 Periods, 2 Locales
- **REQ-8.1**: THE SYSTEM SHALL mendukung 6 kategori: `engagement`, `news`, `economic`, `social`, `technology`, `research`.
- **REQ-8.2**: THE SYSTEM SHALL mendukung 3 periode: `3days` (3 hari terakhir), `weekly` (Senin → hari ini), `monthly` (tanggal 1 → hari ini).
- **REQ-8.3**: THE SYSTEM SHALL mendukung 2 locale: `indonesia` (filter `lang:id`) dan `global` (tanpa filter bahasa).
- **REQ-8.4**: Total output per sesi scraping adalah 36 file (6 × 3 × 2).
- **REQ-8.5**: List categories dan periods SHALL didefinisikan di `config.py` untuk memudahkan penambahan di masa depan.

### Requirement 9: Custom Keywords via CLI
- **REQ-9.1**: THE SYSTEM SHALL mendukung flag CLI `--keywords-id` untuk custom keywords Indonesia.
- **REQ-9.2**: THE SYSTEM SHALL mendukung flag CLI `--keywords-gl` untuk custom keywords Global.
- **REQ-9.3**: Custom keywords SHALL di-parse dengan format comma-separated, support multi-word dengan quote (misal: `"berita terkini,update,breaking news"`).
- **REQ-9.4**: Keyword match SHALL case-insensitive (match tanpa peduli huruf besar/kecil).
- **REQ-9.5**: Match logic SHALL menggunakan `any(keyword in caption.lower())` (OR logic — match jika salah satu keyword cocok).
- **REQ-9.6**: Custom keywords SHALL digabung dengan default keywords (gabungan, bukan mengganti).
- **REQ-9.7**: Jika user tidak input custom keyword, THEN sistem menggunakan default keywords per category.

### Requirement 10: Filtering & Query
- **REQ-10.1**: Query SHALL menggunakan `filter:media` (video + image/infographic).
- **REQ-10.2**: Query SHALL mengecualikan retweets dengan `-is:retweet`.
- **REQ-10.3**: `min_faves` untuk periode `3days` adalah 500 (Indonesia) dan 500 (Global).
- **REQ-10.4**: `min_faves` untuk periode `weekly` dan `monthly` adalah 1000 (Indonesia) dan 1000 (Global).
- **REQ-10.5**: Query Indonesia SHALL menambahkan `lang:id`.

### Requirement 11: Output Structure
- **REQ-11.1**: Output SHALL disimpan dalam struktur folder: `output/{locale}/{category}/{category}_{period}_{date}.json`.
- **REQ-11.2**: Filename format: `{category}_{period}_{date}.json`.
  - 3days: `engagement_3days_2026-09-14.json`
  - weekly: `engagement_week_2026-W37.json`
  - monthly: `engagement_month_2026-09.json`
- **REQ-11.3**: THE SYSTEM SHALL menghasilkan `index.json` di root folder `output/` yang berisi list semua results per run.
- **REQ-11.4**: `index.json` SHALL di-overwrite setiap run (bukan append).

### Requirement 12: Default Behavior
- **REQ-12.1**: Jika user menjalankan `python main.py` tanpa flag, THEN sistem SHALL scrape semua period (`all`), semua category (`all`), semua locale.
- **REQ-12.2**: Default keywords per category SHALL didefinisikan di `config.py` dalam format list.
