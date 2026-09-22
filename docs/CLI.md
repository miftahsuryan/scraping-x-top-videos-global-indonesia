# CLI Reference

Semua command untuk mengoperasikan program ini.

---

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # lalu isi X_AUTH_TOKEN dan X_CT0
```

---

## Output Structure

```
OUTPUT-X/
├── index.json
├── explore/
│   └── 2026-09-22.json
├── screenshots/
│   └── 2026-09-22/
├── downloads/
│   └── 2026-09-22/
│       ├── videos/
│       │   └── tweet_{id}/
│       │       └── video.mp4
│       └── photos/
│           └── tweet_{id}/
│               ├── photo_1.jpg
│               ├── photo_2.jpg
│               └── ...
├── bulk_create/
│   └── 2026-09-22/
│       ├── bulk_create_videos.csv      # tweet_id, hook, headline, source
│       └── bulk_create_photos.csv      # tweet_id, hook, headline, source, content
├── captions/
│   └── 2026-09-22/
│       ├── captions_videos.txt
│       └── captions_photos.txt
├── covers/
│   └── 2026-09-22/
│       └── videos/                     # cover video 5 detik dari Canva
│           └── tweet_{id}.mp4
├── ready_to_post/
│   └── 2026-09-22/
│       ├── videos/                     # hasil stitch cover + tweet video
│       │   └── tweet_{id}.mp4
│       └── photos/                     # foto asli dari tweet (siap desain Canva)
│           └── tweet_{id}/
└── recap_2026-09-22.csv
```

---

## Scrape & Download — `main.py`

```bash
python main.py [FLAGS]
```

| Flag | Default | Keterangan |
|---|---|---|
| `--mode` | `explore` | `explore` (viral random) atau `search` (berdasarkan kategori) |
| `--period` | `all` | `1day`, `3days`, `weekly`, `monthly`, `all` |
| `--category` | `all` | `engagement`, `news`, `economic`, `social`, `technology`, `research`, `business`, `social_media`, `all` |
| `--keywords-id` | — | Custom keywords Indonesia (comma-separated) |
| `--keywords-gl` | — | Custom keywords Global (comma-separated) |
| `--explore-limit` | `15` | Jumlah tweet explore |
| `--no-headless` | `false` | Tampilkan browser (debugging) |
| `--download` | `false` | Download video/photo dari report yang sudah ada |
| `--report` | — | Path report JSON spesifik (untuk `--download`) |
| `--max-age-days` | `7` | Skip download jika sudah di-download dalam N hari |

**Contoh:**
```bash
python main.py                                          # explore, semua periode
python main.py --period 3days                           # explore, 3 hari
python main.py --mode search --category news            # search, berita
python main.py --download                               # download semua report
python main.py --download --report OUTPUT-X/explore/2026-09-22.json
python main.py --no-headless                            # debug mode
```

---

## Generate Content — Video Pipeline

### 1. Hook + Headline CSV — `generate_covers_csv.py`

```bash
python3 generate-content/generate_covers_csv.py \
    --json OUTPUT-X/explore/2026-09-22.json \
    --screenshots OUTPUT-X/screenshots/2026-09-22
```

| Flag | Default | Keterangan |
|---|---|---|
| `--json` | — | **wajib.** Path file report JSON |
| `--screenshots` | — | **wajib.** Folder screenshot |
| `--out` | `OUTPUT-X/bulk_create/YYYY-MM-DD/` | Output folder |
| `--model` | `deepseek-flash` | Model DeepSeek (supports vision) |

**Output:**
- `bulk_create_videos.csv` → tweet_id, hook, headline, source
- `bulk_create_photos.csv` → tweet_id, hook, headline, source, content

### 2. Stitch Cover Video + Tweet Video — `stitch_covers.py`

```bash
python3 generate-content/stitch_covers.py \
    --covers OUTPUT-X/covers/2026-09-22/videos \
    --downloads OUTPUT-X/downloads/2026-09-22/videos \
    --output OUTPUT-X/ready_to_post
```

| Flag | Default | Keterangan |
|---|---|---|
| `--covers` | — | **wajib.** Folder cover video (MP4) dari Canva |
| `--downloads` | — | **wajib.** Folder video tweet |
| `--output` | — | **wajib.** Folder output |
| `--cover-seconds` | `5.0` | Durasi cover video (detik) |
| `--mode` | `id` | `id` (match by tweet ID) atau `order` (match by urutan file) |

### 3. Caption Generator — `generate_captions.py`

```bash
python3 generate-content/generate_captions.py \
    --csv OUTPUT-X/bulk_create/2026-09-22/bulk_create_videos.csv \
    --screenshots OUTPUT-X/screenshots/2026-09-22
```

---

## Generate Content — Photo Pipeline

### 1. CSV sudah di-generate otomatis (satu command dengan video)

`bulk_create_photos.csv` berisi: tweet_id, hook, headline, source, **content**

### 2. Foto asli sudah di-download otomatis

Foto ada di `OUTPUT-X/downloads/{date}/photos/tweet_{id}/photo_*.jpg`

### 3. Desain manual di Canva

- Upload `bulk_create_photos.csv` ke Canva Bulk Create
- Mapping kolom ke template desain
- Export hasil desain ke `OUTPUT-X/ready_to_post/{date}/photos/tweet_{id}/design.png`

### 4. Caption Generator — `generate_captions.py`

```bash
python3 generate-content/generate_captions.py \
    --csv OUTPUT-X/bulk_create/2026-09-22/bulk_create_photos.csv \
    --screenshots OUTPUT-X/screenshots/2026-09-22
```

---

## Recap CSV — `export_recap_csv.py`

```bash
python3 generate-content/export_recap_csv.py \
    --csv OUTPUT-X/bulk_create/2026-09-22/bulk_create_videos.csv \
    --captions OUTPUT-X/captions/2026-09-22/captions_videos.txt \
    --out OUTPUT-X/recap_2026-09-22.csv
```

| Flag | Default | Keterangan |
|---|---|---|
| `--csv` | — | **wajib.** Path bulk_create CSV |
| `--captions` | — | **wajib.** Path captions file |
| `--scraped-date` | auto | Tanggal scrape (YYYY-MM-DD) |
| `--out` | — | **wajib.** Output recap CSV |

---

## Web Dashboard — `web_ui.py`

```bash
python web_ui.py
```

Buka `http://127.0.0.1:8000` di browser. Tidak ada flags.

---

## Workflow Lengkap

### Video
```
1. python main.py                                         ← scrape
2. python main.py --download                              ← download ke videos/tweet_{id}/video.mp4
3. python generate-content/generate_covers_csv.py \
    --json OUTPUT-X/explore/2026-09-22.json \
    --screenshots OUTPUT-X/screenshots/2026-09-22
4. Canva: upload bulk_create_videos.csv → buat cover VIDEO 5 detik → export MP4 ke covers/videos/
5. python generate-content/stitch_covers.py \
    --covers OUTPUT-X/covers/2026-09-22/videos \
    --downloads OUTPUT-X/downloads/2026-09-22/videos \
    --output OUTPUT-X/ready_to_post
6. python generate-content/generate_captions.py \
    --csv OUTPUT-X/bulk_create/2026-09-22/bulk_create_videos.csv \
    --screenshots OUTPUT-X/screenshots/2026-09-22
```

### Photo
```
1. python main.py                                         ← scrape
2. python main.py --download                              ← download ke photos/tweet_{id}/photo_*.jpg
3. python generate-content/generate_covers_csv.py \
    --json OUTPUT-X/explore/2026-09-22.json \
    --screenshots OUTPUT-X/screenshots/2026-09-22
4. Foto asli sudah ada di downloads/photos/tweet_{id}/
5. Desain manual di Canva → export ke ready_to_post/photos/tweet_{id}/design.png
6. python generate-content/generate_captions.py \
    --csv OUTPUT-X/bulk_create/2026-09-22/bulk_create_photos.csv \
    --screenshots OUTPUT-X/screenshots/2026-09-22
```
