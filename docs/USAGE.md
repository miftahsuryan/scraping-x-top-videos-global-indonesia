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

### Explore Mode
```
OUTPUT-X/
  index.json
  explore/
    explore_1day_2026-09-18.json
    explore_3days_2026-09-18.json
    explore_weekly_2026-W38.json
    explore_monthly_2026-09.json
  downloads/
    2026-09-18/
      tweet_2101516770255270041.mp4
```

### Search Mode
```
OUTPUT-X/
  index.json
  indonesia/
    engagement/
      engagement_3days_2026-09-14.json
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

## Filename Format

| Period | Filename | Contoh |
|---|---|---|
| 1day | `{prefix}_1day_{YYYY-MM-DD}.json` | `explore_1day_2026-09-18.json` |
| 3days | `{prefix}_3days_{YYYY-MM-DD}.json` | `explore_3days_2026-09-18.json` |
| weekly | `{prefix}_weekly_{YYYY-WWW}.json` | `explore_weekly_2026-W38.json` |
| monthly | `{prefix}_monthly_{YYYY-MM}.json` | `explore_monthly_2026-09.json` |

## Query Construction (Search Mode)

Query dibangun secara otomatis berdasarkan:
```
{keywords} filter:media min_faves:{min_faves} since:{since_date} -is:retweet
```

Contoh:
- Indonesia, 3days: `(heboh OR geger OR gempar) filter:media min_faves:500 since:2026-09-15 -is:retweet`
- Global, weekly: `(went viral OR blew up OR buzzing) filter:media min_faves:1000 since:2026-09-15 -is:retweet`
