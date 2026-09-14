# Usage Guide

## Quick Start

```bash
# Default: semua period, semua category, semua locale
python main.py

# Dengan custom keywords
python main.py --category news --keywords-id "berita terkini" --keywords-gl "breaking news"

# Period tertentu
python main.py --period 3days

# Category tertentu
python main.py --category news,economic

# Debugging (browser visible)
python main.py --no-headless
```

## CLI Flags

| Flag | Description | Default | Contoh |
|---|---|---|---|
| `--period` | Periode waktu | `all` | `3days`, `weekly`, `monthly`, `all` |
| `--category` | Kategori konten | `all` | `engagement`, `news`, `economic`, `social`, `technology`, `research`, `business`, `social_media`, `all` |
| `--keywords-id` | Custom keywords Indonesia | Default per category | `"berita,ekonomi"` |
| `--keywords-gl` | Custom keywords Global | Default per category | `"news,economy"` |
| `--no-headless` | Tampilkan browser | `false` | Flag tanpa value |

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
python main.py --category news --keywords-id "berita"

# Multiple keywords
python main.py --category news --keywords-id "berita,update,terkini"

# Multi-word keywords
python main.py --category news --keywords-id "berita terkini,kabar terbaru"

# Mixed
python main.py --category news,economic --keywords-id "berita,ekonomi" --keywords-gl "news,economy"
```

## Period Options

| Period | since_date | Limit | min_faves |
|---|---|---|---|
| `3days` | Hari ini - 3 hari | 5 | 500 |
| `weekly` | Senin → hari ini | 10 | 1000 |
| `monthly` | Tanggal 1 → hari ini | 10 | 1000 |

## Category Options

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
│   ├── economic/
│   ├── social/
│   ├── technology/
│   ├── research/
│   ├── business/
│   └── social_media/
└── global/
    ├── engagement/
    ├── news/
    ├── economic/
    ├── social/
    ├── technology/
    ├── research/
    ├── business/
    └── social_media/
```

## Filename Format

| Period | Filename | Contoh |
|---|---|---|
| 3days | `{category}_3days_{YYYY-MM-DD}.json` | `engagement_3days_2026-09-14.json` |
| weekly | `{category}_week_{YYYY-WWW}.json` | `engagement_week_2026-W37.json` |
| monthly | `{category}_month_{YYYY-MM}.json` | `engagement_month_2026-09.json` |

## Query Construction

Query dibangun secara otomatis berdasarkan:
```
{keywords} filter:media min_faves:{min_faves} since:{since_date} -is:retweet
```

Contoh:
- Indonesia, 3days: `(heboh OR geger OR gempar) filter:media min_faves:500 since:2026-09-11 -is:retweet`
- Global, weekly: `(went viral OR blew up OR buzzing) filter:media min_faves:1000 since:2026-09-08 -is:retweet`
