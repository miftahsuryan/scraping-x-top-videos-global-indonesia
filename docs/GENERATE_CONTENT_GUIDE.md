# Generate Content Guide

Dark editorial template for Indonesian social media content.

## Brand System

| Element | Setting |
|---------|---------|
| Canvas | 1080 × 1920 px |
| Background | `#0D0D0D` |
| Text | `#F5F5F5` |
| Accent | `#FF7300` |
| Secondary | `#8A8A8A` |
| Font | Plus Jakarta Sans |
| Logo | SNSI (small, bottom) |

**No views. No likes. No category tags.**

## Workflow

```
Scrape → Download → Generate CSV → Canva (text only) → Add images manually → Export → Stitch → Generate Captions → Post
```

## Step 1: Scrape & Download

```bash
python main.py
python main.py --download
```

## Step 2: Generate Editorial CSV

```bash
python3 generate-content/generate_covers_csv.py \
    --json OUTPUT-X/explore/2026-09-22.json \
    --screenshots OUTPUT-X/screenshots/2026-09-22 \
    --out bulk_create.csv
```

**CSV columns (4 fields — text only, no photo):**

| Column | Purpose | Example |
|--------|---------|---------|
| `tweet_id` | ID for matching | `2100584082811797805` |
| `hook` | Short reaction (orange) | `SALAH PILIH 😭` |
| `headline` | Natural sentence | `Pria ini ternyata salah pilih orang buat diganggu` |
| `source` | Attribution | `@Rainmaker1973` |

## Step 3: Create Canva Template

```
┌──────────────────────┐
│                      │
│      PHOTO           │  ← YOU drag screenshot here manually
│                      │
│   SALAH PILIH 😭     │  ← hook, orange #FF7300, bold
│                      │
│   Pria ini ternyata  │  ← headline, white #F5F5F5, ExtraBold
│   salah pilih orang  │
│   buat diganggu      │
│                      │
│   ─────              │
│   @Rainmaker1973     │  ← source, gray #8A8A8A
│              SNSI    │  ← logo, small
└──────────────────────┘
```

## Step 4: Bulk Create in Canva

1. Open Canva → create **1080 × 1920** design
2. Set background to `#0D0D0D`
3. Add text elements: hook, headline, source
4. Add image placeholder for photo
5. Add SNSI logo (small, bottom)
6. **Edit → Bulk create → Upload CSV**
7. Map: `hook` → hook text, `headline` → headline text, `source` → source text
8. Generate designs
9. **Manually drag the correct screenshot into each design**
10. Download PNG to `OUTPUT-X/covers/2026-09-20/`

## Step 5: Stitch

### If Canva exports have tweet IDs in filenames:

```bash
python3 generate-content/stitch_covers.py \
    --covers OUTPUT-X/covers/2026-09-20 \
    --downloads OUTPUT-X/downloads/2026-09-20 \
    --output OUTPUT-X/ready_to_post
```

### If Canva exports DON'T have tweet IDs (e.g., 1.png, 2.png):

```bash
python3 generate-content/stitch_covers.py \
    --covers OUTPUT-X/covers/2026-09-20 \
    --downloads OUTPUT-X/downloads/2026-09-20 \
    --output OUTPUT-X/ready_to_post \
    --mode order
```

**Output:** Video MP4 (1080x1920) tersimpan di `OUTPUT-X/ready_to_post/{date}/` (misal: `OUTPUT-X/ready_to_post/2026-09-20/`), siap diposting ke TikTok/Reels/Shorts.

## Step 6: Generate Captions (Instagram/TikTok)

Generate caption siap posting dari CSV (hook + headline + source).

### Prerequisites

```bash
pip install openai
# Pastikan DEEPSEEK_API_KEY sudah diisi di .env
```

### Generate Captions

```bash
python3 generate-content/generate_captions.py \
    --csv bulk_create.csv \
    --out captions.txt
```

### Output Format

File `captions.txt` berisi caption siap copy-paste:

```
Siang bolong langit di Kalimantan Tengah berubah orange kayak kulit jeruk, fenomena alam yang bikin warga sekitar kaget 😭
cr: @rapunsey

#langit #orange #kalimantan #fenomena #alam

---

GPT-5.5 baru rilis, sekarang bisa generate video langsung dari text 🔥
cr: @openai

#ai #gpt #openai #teknologi #video

---
```

### Fitur

- Caption gabungan hook + headline (bukan tempel langsung)
- 5 hashtag lowercase, 1 kata, relevan dengan konten
- Credit ke sumber asli (`cr: @source`)
- Output dipisah dengan `---` untuk copy-paste mudah

## Step 7: Export Recap CSV (Google Sheets Import)

Gabungkan hasil hook/headline (CSV) dan caption (TXT) menjadi satu recap CSV siap import ke Google Sheets.

```bash
python3 generate-content/export_recap_csv.py \
    --csv bulk_create.csv \
    --captions captions.txt \
    --scraped-date 2026-09-21 \
    --out OUTPUT-X/recap_2026-09-21.csv
```

### Kolom Output

| Kolom | Sumber |
|---|---|
| `tweet_id` | dari bulk_create.csv |
| `hook` | dari bulk_create.csv |
| `headline` | dari bulk_create.csv |
| `source` | dari bulk_create.csv |
| `caption` | dari captions.txt |
| `hashtags` | dari captions.txt |
| `scraped_date` | dari JSON report |
| `run_date` | timestamp saat export |

### Import ke Google Sheets

1. Buka Google Sheets baru
2. **File → Import → Upload** → pilih `recap_YYYY-MM-DD.csv`
3. Pilih **Replace spreadsheet** → **Import data**

## English Terms

Keep these in English (do not translate):
- AI, iPhone, TikTok, viral, Claude, GPT, crypto, SEO
- Brand names, tech terms, internet slang

## Design Rules

**Always:**
- Dark background `#0D0D0D`
- Orange accent `#FF7300` for hook
- Plus Jakarta Sans font
- SNSI logo small
- Natural capitalization (NOT all caps)

**Never:**
- Views/likes in visual
- Category tags (CERITA HARI INI, TRENDING, etc.)
- Boxes, borders, tables
- Too many text elements
- AI-generated clickbait
