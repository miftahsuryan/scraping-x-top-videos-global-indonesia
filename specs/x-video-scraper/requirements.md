# Requirements: X/Twitter Video Engagement Scraper (Top 15 Global & Indonesia)

## Introduction
Fitur ini bertujuan untuk mengumpulkan (scraping) dan meranking tweet video di X (Twitter) dengan tingkat keterlibatan (engagement) tertinggi. Sistem menghasilkan 4 file output:
- Top 15 video Indonesia bulanan (since awal bulan)
- Top 15 video Global bulanan (since awal bulan)
- Top 15 video Indonesia 3 hari terakhir
- Top 15 video Global 3 hari terakhir

Total: 60 video per sesi scraping, disimpan dalam format JSON terstruktur.

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
