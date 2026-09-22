# X/Twitter Video Scraper (Explore Mode + Search Mode)

Scraper otomatis untuk mengumpulkan dan memeringkat tweet di X (Twitter) dengan dua mode operasi:
- **Explore Mode (Default)**: Konten viral dari halaman Explore For You
- **Search Mode**: Pencarian berdasarkan 8 kategori konten

**4 periode waktu** | **10 item per periode** | **Video + Infographic**

---

## Mode Operasi

| Mode | Deskripsi | Default |
|---|---|---|
| `explore` | Konten viral dari Explore For You | Yes |
| `search` | Pencarian berdasarkan kategori & keyword | No |

---

## Periode

| Periode | Deskripsi | since_date | Limit | min_faves |
|---|---|---|---|---|
| `1day` | 24 jam terakhir | Hari ini - 1 hari | 10 | 100 |
| `3days` | 3 hari terakhir | Hari ini - 3 hari | 10 | 500 |
| `weekly` | Senin -> hari ini | Senin minggu ini | 10 | 1000 |
| `monthly` | Tanggal 1 -> hari ini | Tanggal 1 bulan ini | 10 | 1000 |

---

## Kategori (Search Mode)

| Kategori | Deskripsi |
|---|---|
| `engagement` | Video viral dengan engagement tinggi |
| `news` | Headlines dan berita terkini |
| `economic` | Insight ekonomi dan pasar |
| `social` | Isu sosial dan kesejahteraan |
| `technology` | Tech, AI, gadget, dan startup |
| `research` | Penelitian dan studi terbaru |
| `business` | Bisnis, perusahaan, dan investasi |
| `social_media` | Tren media sosial dan platform |

---

## Formula Pemeringkatan

```
Engagement Score = Likes + Reposts + Views
```

---

## Setup & Instalasi

Lihat [Local Setup Guide](docs/SETUP.md) untuk panduan lengkap.

**Cepat:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Isi X_AUTH_TOKEN dan X_CT0 di .env, lalu:
python main.py
```

### Dependensi

| Package | Versi | Fungsi |
|---|---|---|
| playwright | >= 1.40.0 | Otomasi browser |
| pydantic | >= 2.5.0 | Validasi data |
| python-dotenv | >= 1.0.0 | Environment variables |
| fastapi | >= 0.115.0 | Web dashboard |
| uvicorn | >= 0.30.0 | Web server |
| httpx | >= 0.27.0 | Async HTTP client (video download) |
| pytest | >= 7.4.0 | Testing |

---

## CLI Usage

### Default (Explore Mode, Semua Periode)
```bash
python main.py
```

### Explore Mode dengan Periode Tertentu
```bash
python main.py --period 1day
python main.py --period 3days
python main.py --period weekly
python main.py --period monthly
```

### Search Mode
```bash
python main.py --mode search --category news
python main.py --mode search --category news,economic,social
```

### Custom Keywords (Search Mode)
```bash
python main.py --mode search --category news --keywords-id "berita terkini,update" --keywords-gl "breaking news"
```

### Download Video (via TwitterSaver.net)
```bash
# Download dari semua reports
python main.py --download

# Download dari report tertentu
python main.py --download --report OUTPUT-X/explore/explore_latest_2026-09-20.json

# Debug (browser visible)
python main.py --download --no-headless
```

### Debugging (Browser Visible)
```bash
python main.py --no-headless
```

### Kombinasi
```bash
python main.py --mode search --period 3days --category news,economic --keywords-id "ekonomi,berita"
```

---

## CLI Flags

| Flag | Deskripsi | Default | Pilihan |
|---|---|---|---|
| `--mode` | Mode scraping | `explore` | `explore`, `search` |
| `--period` | Periode waktu | `all` | `1day`, `3days`, `weekly`, `monthly`, `all` |
| `--category` | Kategori konten | `all` | `engagement`, `news`, `economic`, `social`, `technology`, `research`, `business`, `social_media`, `all` |
| `--keywords-id` | Custom keywords Indonesia | Default per kategori | `"berita,ekonomi"` |
| `--keywords-gl` | Custom keywords Global | Default per kategori | `"news,economy"` |
| `--no-headless` | Tampilkan browser | `false` | Flag tanpa value |
| `--explore-limit` | Jumlah tweet explore | `10` | Angka integer |
| `--download` | Download video via twittersaver.net | `false` | Flag tanpa value |
| `--report` | Path file report spesifik (untuk `--download`) | Semua reports | Path ke file JSON |

---

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

---

## Web Dashboard

Dashboard browser untuk mengontrol scraper tanpa CLI.

### Menjalankan Dashboard
```bash
python web_ui.py
```

Buka `http://127.0.0.1:8000` di browser.

### Fitur Dashboard
- **Mode Selection**: Pilih Explore atau Search mode
- **Start Scraping**: Pilih periode dan jalankan scraper
- **Status Monitoring**: Polling status job secara real-time
- **Report Browser**: Filter dan lihat hasil scraping
- **Report Detail**: Lihat ranked tweets dengan metrics

### API Endpoints

| Endpoint | Method | Deskripsi |
|---|---|---|
| `/` | GET | Dashboard HTML |
| `/api/health` | GET | Health check |
| `/api/jobs` | POST | Start scraper job |
| `/api/jobs/current` | GET | Current job status |
| `/api/reports` | GET | List reports (filterable) |
| `/api/reports/{id}` | GET | Get specific report |

### Keamanan
- Hanya berjalan di `127.0.0.1` (localhost)
- Cookie X/Twitter tidak pernah ditampilkan ke browser
- Tidak ada CORS, tidak ada remote access

---

## Struktur Output

```
OUTPUT-X/
├── index.json                          # Master index
├── explore/                            # Report JSON per tanggal
│   └── 2026-09-21.json
├── screenshots/                        # Screenshot per tanggal
│   └── 2026-09-21/
├── downloads/                          # Video/image download
│   └── 2026-09-21/
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

---

## Testing

```bash
pytest tests/
```

---

## Struktur Folder Proyek

```
SCRAPING-CONTENT-X/
├── AGENTS.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── conftest.py
├── main.py
├── web_ui.py
├── generate-content/
│   ├── generate_covers_csv.py    # Hook + headline CSV (Canva)
│   ├── generate_captions.py      # Caption + hashtags + opening
│   ├── stitch_covers.py          # Cover + video stitching
│   └── export_recap_csv.py       # Recap CSV (Google Sheets)
├── docs/
│   ├── CLI.md
│   ├── USAGE.md
│   ├── SETUP.md
│   ├── FAQ.md
│   └── GENERATE_CONTENT_GUIDE.md
├── OUTPUT-X/
├── specs/
├── src/
│   ├── __init__.py
│   ├── browser.py
│   ├── config.py
│   ├── downloader.py
│   ├── extractor.py
│   ├── models.py
│   ├── scraper.py
│   └── web/
├── standards/
└── tests/
```
