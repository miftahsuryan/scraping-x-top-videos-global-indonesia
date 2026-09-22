# Usage Guide

## Quick Start

```bash
# Default: Explore mode, semua period
python main.py

# Explore mode dengan period tertentu
python main.py --period 1day

# Search mode dengan category
python main.py --mode search --category news

# Dengan custom keywords
python main.py --mode search --category news --keywords-id "berita terkini" --keywords-gl "breaking news"

# Download video dari reports
python main.py --download

# Download dari report tertentu
python main.py --download --report OUTPUT-X/explore/explore_latest_2026-09-20.json

# Debugging (browser visible)
python main.py --no-headless
```

## CLI Flags

| Flag | Description | Default | Contoh |
|---|---|---|---|
| `--mode` | Mode scraping | `explore` | `explore`, `search` |
| `--period` | Periode waktu | `all` | `1day`, `3days`, `weekly`, `monthly`, `all` |
| `--category` | Kategori konten (search mode) | `all` | `engagement`, `news`, `economic`, `social`, `technology`, `research`, `business`, `social_media`, `all` |
| `--keywords-id` | Custom keywords Indonesia | Default per kategori | `"berita,ekonomi"` |
| `--keywords-gl` | Custom keywords Global | Default per kategori | `"news,economy"` |
| `--no-headless` | Tampilkan browser | `false` | Flag tanpa value |
| `--explore-limit` | Jumlah tweet explore | `10` | Angka integer |
| `--download` | Download video via twittersaver.net | `false` | Flag tanpa value |
| `--report` | Path file report spesifik (untuk `--download`) | Semua reports | Path ke file JSON |

## Mode Operasi

### Explore Mode (Default)
Scrape konten viral dari halaman **Explore For You** di X/Twitter. Tidak memerlukan kategori atau keyword.

```bash
# Semua periode
python main.py

# Periode tertentu
python main.py --period 1day
python main.py --period 3days
python main.py --period weekly
python main.py --period monthly

# Dengan limit custom
python main.py --period 3days --explore-limit 20
```

### Search Mode
Scrape berdasarkan **kategori dan keyword** dari hasil pencarian X/Twitter.

```bash
# Semua kategori
python main.py --mode search

# Kategori tertentu
python main.py --mode search --category news
python main.py --mode search --category news,economic,social

# Dengan custom keywords
python main.py --mode search --category news --keywords-id "berita terkini" --keywords-gl "breaking news"
```

### Download Mode
Download video dari tweet yang sudah di-scrape menggunakan twittersaver.net sebagai proxy. Mode ini membaca tweet URL dari report JSON yang ada, me-resolve link download MP4, lalu mengunduh file videonya.

```bash
# Download dari semua reports
python main.py --download

# Download dari report tertentu
python main.py --download --report OUTPUT-X/explore/explore_latest_2026-09-20.json

# Debug dengan browser visible
python main.py --download --no-headless
```

**Cara kerja:**
1. Membaca `OUTPUT-X/index.json` atau file report spesifik
2. Memfilter tweet yang sudah di-download (skip jika `download_path` sudah ada)
3. Untuk setiap tweet URL, navigate ke twittersaver.net dan resolve link MP4
4. Download video ke `OUTPUT-X/downloads/{scraped_date}/tweet_{tweet_id}.mp4`
5. Update source report JSON dengan `download_path`

**Rate limiting:** 3-5 detik antar request ke twittersaver.net, max 2 retry dengan exponential backoff.

## Custom Keywords

### Format
```bash
--keywords-id "keyword1,keyword2,keyword3"
--keywords-gl '"multi word keyword",keyword2'
```

### Aturan
- **Comma-separated**: `berita,ekonomi,sosial`
- **Multi-word dengan quote**: `"breaking news","stock market"`
- **Case-insensitive**: `BERITA` = `berita` = `Berita`
- **OR logic**: Match jika salah satu keyword cocok
- **Digabung**: Custom keywords + default keywords

### Contoh
```bash
# Single keyword
python main.py --mode search --category news --keywords-id "berita"

# Multiple keywords
python main.py --mode search --category news --keywords-id "berita,update,terkini"

# Multi-word keywords
python main.py --mode search --category news --keywords-id "berita terkini,kabar terbaru"

# Mixed
python main.py --mode search --category news,economic --keywords-id "berita,ekonomi" --keywords-gl "news,economy"
```

## Period Options

| Period | since_date | Limit | min_faves | Contoh Filename |
|---|---|---|---|---|
| `1day` | Hari ini - 1 hari | 10 | 100 | `explore_1day_2026-09-18.json` |
| `3days` | Hari ini - 3 hari | 10 | 500 | `explore_3days_2026-09-18.json` |
| `weekly` | Senin -> hari ini | 10 | 1000 | `explore_weekly_2026-W38.json` |
| `monthly` | Tanggal 1 -> hari ini | 10 | 1000 | `explore_monthly_2026-09.json` |

## Category Options (Search Mode)

| Category | Default Keywords (ID) | Default Keywords (GL) |
|---|---|---|
| `engagement` | heboh, geger, gempar, syok, kaget, ramai dibicarakan, bikin heboh, jadi sorotan, curi perhatian, banjir komentar | went viral, blew up, buzzing, sensation, can't stop watching, took the internet by storm, everyone's talking about, internet is obsessed, gone viral |
| `news` | berita terkini, kabar terbaru, info terkini, kabar terhangat, berita hari ini, berita mengejutkan, update terbaru, kabar duka, kabar gembira | breaking news, headlines, just in, developing story, top story, news alert, live update, world news, latest news |
| `economic` | pasar saham, ihsg, rupiah melemah, rupiah menguat, harga naik, harga turun, harga bbm, inflasi, resesi ekonomi, bi rate | stock market, wall street, inflation, recession, interest rate, federal reserve, nasdaq, s&p 500, market crash, crypto crash |
| `social` | bansos, kemiskinan, kesejahteraan sosial, unjuk rasa, demo buruh, bantuan sosial, korban bencana, penggalangan dana | welfare, food bank, protest, homelessness, wage strike, human rights, charity, relief fund, refugees, social justice |
| `technology` | teknologi terbaru, aplikasi lokal, startup lokal, inovasi anak bangsa, hp terbaru, gawai terbaru, kecerdasan buatan, robot canggih | tech news, ai breakthrough, new gadget, startup funding, app launch, tech giant, silicon valley, product launch |
| `research` | penelitian, riset, studi, discovery | research, study, discovery |
| `business` | bisnis, perusahaan, ceo perusahaan, direktur utama, merger perusahaan, akuisisi bisnis, ipo saham, pendapatan perusahaan | business, CEO resigns, CEO steps down, merger, acquisition, IPO, quarterly earnings, company profits, layoffs |
| `social_media` | media sosial, fitur baru instagram, update tiktok, algoritma twitter, x down, instagram down, kebijakan media sosial, konten kreator | social media, new feature, algorithm change, platform outage, app update, blue checkmark, account verification, content creator |

## Output Structure

```
OUTPUT-X/
├── index.json                          # Master index
├── explore/                            # Report JSON per tanggal
│   └── 2026-09-21.json
├── screenshots/                        # Screenshot per tanggal
│   └── 2026-09-21/
├── downloads/                          # Video/image download
│   └── 2026-09-21/
│       ├── tweet_ID.mp4
│       └── tweet_ID.jpg
├── bulk_create/                        # CSV untuk Canva Bulk Create
│   └── 2026-09-21/
│       └── bulk_create.csv
├── captions/                           # Caption + hashtags + opening
│   └── 2026-09-21/
│       └── captions.txt
├── covers/                             # Cover PNG dari Canva export
│   └── 2026-09-21/
├── ready_to_post/                      # Video final (cover + video)
│   └── 2026-09-21/
└── recap_2026-09-21.csv                # Recap CSV untuk Google Sheets
```

## Filename Format

| Tipe | Format | Contoh |
|---|---|---|
| Explore report | `YYYY-MM-DD.json` | `2026-09-21.json` |
| Download | `tweet_{tweet_id}.mp4` | `tweet_2101325555010539820.mp4` |
| Bulk CSV | `bulk_create.csv` | `bulk_create.csv` |
| Captions | `captions.txt` | `captions.txt` |
| Recap | `recap_YYYY-MM-DD.csv` | `recap_2026-09-21.csv` |

## Query Construction (Search Mode)

Query dibangun secara otomatis berdasarkan:
```
{keywords} filter:media min_faves:{min_faves} since:{since_date} -is:retweet
```

Contoh:
- Indonesia, 3days: `(heboh OR geger OR gempar) filter:media min_faves:500 since:2026-09-15 -is:retweet`
- Global, weekly: `(went viral OR blew up OR buzzing) filter:media min_faves:1000 since:2026-09-15 -is:retweet`

## Generate Content

### Quick Recap (One Command)

```bash
python3 generate-content/generate_covers_csv.py \
    --json OUTPUT-X/explore/2026-09-21.json \
    --screenshots OUTPUT-X/screenshots/2026-09-21
```

### Full Pipeline

```bash
# Step 1: Generate CSV untuk Canva Bulk Create
python3 generate-content/generate_covers_csv.py \
    --json OUTPUT-X/explore/2026-09-21.json \
    --screenshots OUTPUT-X/screenshots/2026-09-21

# Step 2: Upload CSV ke Canva → Edit → Bulk Create → Export PNG ke OUTPUT-X/covers/2026-09-21/

# Step 3: Generate captions + hashtags + opening comment
python3 generate-content/generate_captions.py \
    --csv OUTPUT-X/bulk_create/2026-09-21/bulk_create.csv \
    --screenshots OUTPUT-X/screenshots/2026-09-21

# Step 4: Stitch cover + video
python3 generate-content/stitch_covers.py \
    --covers OUTPUT-X/covers/2026-09-21 \
    --downloads OUTPUT-X/downloads/2026-09-21 \
    --output OUTPUT-X/ready_to_post

# Step 5: Export recap CSV untuk Google Sheets
python3 generate-content/export_recap_csv.py \
    --csv OUTPUT-X/bulk_create/2026-09-21/bulk_create.csv \
    --captions OUTPUT-X/captions/2026-09-21/captions.txt \
    --out OUTPUT-X/recap_2026-09-21.csv
```

Lihat [Generate Content Guide](GENERATE_CONTENT_GUIDE.md) untuk panduan lengkap.
