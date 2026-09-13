# X/Twitter Video Engagement Scraper (Top 15 Global & Indonesia)

Proyek ini adalah scraper otomatis untuk mengumpulkan dan memeringkat video di X (Twitter) yang memiliki tingkat keterlibatan (*engagement*) tertinggi. Scraper menghasilkan **4 file output** per sesi:
- **Top 15 Video Indonesia Bulanan** (since awal bulan)
- **Top 15 Video Global Bulanan** (since awal bulan)
- **Top 15 Video Indonesia 3 Hari Terakhir**
- **Top 15 Video Global 3 Hari Terakhir**

**Total: 60 video** dengan URL tweet, direct MP4 link (jika terdeteksi), teks/caption tweet, metrik keterlibatan lengkap, serta username pembuat tweet.

Proyek ini dibangun mengikuti alur kerja **OpenCode Spec Kit** (*spec-first workflow*), di mana setiap fitur memiliki spesifikasi kebutuhan formal (`requirements.md`), rancangan arsitektur (`design.md`), dan daftar tugas implementasi (`tasks.md`).

---

## Formula Pemeringkatan Engagement

Pemeringkatan video tweet dihitung berdasarkan kombinasi metrik dalam 24 jam tanggal target:

$$\text{Engagement Score} = \text{Likes} + \text{Reposts} + \text{Views}$$

---

## Struktur Folder

```text
scraping/
├── AGENTS.md                                # Panduan dan aturan kerja AI agent (Playwright, Python, Security)
├── README.md                                # Dokumentasi proyek dan panduan instalasi
├── requirements.txt                         # Dependensi Python
├── .env.example                             # Template kredensial cookie X/Twitter
├── .gitignore                               # File yang dikecualikan dari Git
├── main.py                                  # Script CLI utama untuk menjalankan scraper
├── docs/
│   └── prompt.md                            # Prompt / catatan proyek
├── output/                                  # Direktori output file JSON hasil scraping
│   ├── top15_indonesia_monthly_YYYY-MM.json
│   ├── top15_global_monthly_YYYY-MM.json
│   ├── top15_indonesia_3days_YYYY-MM-DD.json
│   └── top15_global_3days_YYYY-MM-DD.json
├── specs/
│   └── x-video-scraper/                     # Spesifikasi fitur scraper
│       ├── requirements.md                  # Acceptance criteria berformat EARS
│       ├── design.md                        # Desain arsitektur & pemetaan Enterprise Standards
│       └── tasks.md                         # Checklist tugas implementasi
├── src/                                     # Source code modul scraper
│   ├── __init__.py
│   ├── browser.py                           # Manajemen Playwright browser context & injeksi cookies
│   ├── config.py                            # Konfigurasi lingkungan & konstanta
│   ├── extractor.py                         # Parser angka metrik (K/M ke integer) & kalkulator engagement
│   ├── models.py                            # Pydantic schema (EngagementMetrics, VideoTweet, ScrapeReport)
│   └── scraper.py                           # Engine scraping Explore Indonesia & Global
├── standards/
│   └── enterprise-standards.md              # Standar kualitas enterprise OpenCode
└── tests/
    └── test_extractor.py                    # Pengujian unit untuk parsing metrik & scoring
```

---

## Format Output JSON

Setiap file output memiliki format `ScrapeReport`:

```json
{
  "scraped_date": "2026-09",
  "scraped_at": "2026-09-13T01:00:00.000Z",
  "formula": "likes + reposts + views",
  "total_items": 15,
  "indonesia_explore": [
    {
      "tweet_url": "https://x.com/username/status/1234567890",
      "video_url": "https://video.twimg.com/ext_tw_video/.../vid/...mp4",
      "caption": "Teks caption tweet...",
      "username": "Nama Akun",
      "handle": "@username",
      "posted_at": "2026-09-01T12:34:56.000Z",
      "engagement": {
        "likes": 25000,
        "views": 450000,
        "reposts": 8000,
        "replies": 1200,
        "total_score": 483000
      }
    }
  ],
  "global_explore": []
}
```

### 4 File Output:
| File | Deskripsi |
|---|---|
| `top15_indonesia_monthly_YYYY-MM.json` | Top 15 Indonesia, since awal bulan |
| `top15_global_monthly_YYYY-MM.json` | Top 15 Global, since awal bulan |
| `top15_indonesia_3days_YYYY-MM-DD.json` | Top 15 Indonesia, since 3 hari lalu |
| `top15_global_3days_YYYY-MM-DD.json` | Top 15 Global, since 3 hari lalu |

---

## Fitur Filtering

Scraper menerapkan beberapa lapisan filtering otomatis sebelum menentukan video teratas:

- **NSFW Filter**: Tweet yang mengandung kata kunci eksplisit (Bahasa Indonesia + English) atau berasal dari akun NSFW akan difilter otomatis.
- **Video Domain Filter**: Hanya video dari domain trusted (`video.twimg.com`) yang diterima.
- **Sensitive Content Check**: Tweet dengan sensitive content warning dari X/Twitter akan diabaikan.
- **Topic Filter**: Hanya tweet yang cocok dengan kategori tertentu (highlight, culture, social, technology) yang dipertahankan.
- **Engagement Minimum**: Tweet dengan skor engagement di bawah 5.000 (likes + reposts + views) akan diabaikan.
- **Deduplikasi**: URL tweet yang sama tidak akan dihitung dua kali.

---

## Panduan Instalasi & Persiapan

### 1. Prasyarat
- Python 3.10 atau versi yang lebih baru
- Akun X (Twitter) yang aktif

### 2. Instalasi Dependensi
Jalankan perintah berikut di terminal:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Konfigurasi Cookie Sesi X (`.env`)
Karena X memiliki *login wall* dan proteksi bot, scraper menggunakan session cookie dari browser Anda:

1. Salin `.env.example` menjadi `.env`:
   ```bash
   cp .env.example .env
   ```
2. Buka [x.com](https://x.com) di browser Chrome/Firefox Anda dalam kondisi sudah login.
3. Buka **Developer Tools** (`F12` atau `Cmd + Option + I`).
4. Buka tab **Application** (Chrome) atau **Storage** (Firefox) → **Cookies** → `https://x.com`.
5. Salin nilai cookie berikut ke `.env`:
   * `auth_token`: nilai token login Anda.
   * `ct0`: nilai CSRF token Anda.
6. (Opsional) Tambahkan `CF_CLEARANCE` jika Anda memiliki Cloudflare clearance token untuk menghindari captcha.
7. (Opsional) Ubah `HEADLESS=true` ke `false` jika ingin melihat jendela browser saat scraping berjalan.

---

## Cara Menjalankan Scraper

### Menjalankan Scraping Bulan Ini (Default UTC)
```bash
python main.py
```

### Menjalankan Scraping untuk Bulan Tertentu
```bash
python main.py --month 2026-09
```

### Menjalankan dengan Tampilan Browser Visual (Debugging)
```bash
python main.py --no-headless
```

---

## Menjalankan Pengujian (Testing)

Untuk memastikan modul parser metrik dan formula kalkulasi engagement berjalan dengan benar:

```bash
pytest tests/
```
