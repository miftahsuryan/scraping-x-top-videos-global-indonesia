# FAQ

## Q: Bagaimana cara custom keywords?

```bash
python main.py --category news --keywords-id "berita terkini,update" --keywords-gl "breaking news"
```

Custom keywords digabung dengan default keywords. Match logic: OR (jika salah satu keyword cocok).

## Q: Bagaimana cara scrape multiple categories?

```bash
python main.py --category news,economic,social
```

Gunakan comma-separated untuk multiple categories.

## Q: Bagaimana cara cek output files?

```bash
# Lihat semua files
ls -R output/

# Lihat index.json
cat output/index.json | python -m json.tool

# Lihat file tertentu
cat output/indonesia/news/news_3days_2026-09-14.json | python -m json.tool
```

## Q: Kenapa beberapa tweets di-filter?

Beberapa alasan tweets di-filter:
1. **NSFW**: Mengandung kata kunci eksplisit
2. **Sensitive Content**: Memiliki warning dari X/Twitter
3. **Untrusted Domain**: Video tidak dari domain trusted (`video.twimg.com`)
4. **Duplicate**: URL tweet yang sama sudah dihitung

## Q: Bagaimana cara ganti default keywords?

Edit `src/config.py` dan ubah `DEFAULT_KEYWORDS_ID` atau `DEFAULT_KEYWORDS_GL`:

```python
DEFAULT_KEYWORDS_ID = {
    "news": ["berita", "terkini", "breaking news"],
    # ...
}
```

## Q: Apakah support infographics?

Ya. Query menggunakan `filter:media` yang mencakup video dan gambar (infographics).

## Q: Bagaimana cara scrape hanya 1 period?

```bash
python main.py --period 3days
python main.py --period weekly
python main.py --period monthly
```

## Q: Bagaimana cara scrape hanya 1 locale?

Saat ini scraper selalu scrape Indonesia dan Global. Untuk single locale, gunakan custom keywords yang spesifik:

```bash
# Hanya Indonesia
python main.py --keywords-id "berita"

# Hanya Global
python main.py --keywords-gl "news"
```

## Q: Apa itu index.json?

`index.json` adalah master index yang berisi list semua hasil scraping per run. File ini di-overwrite setiap run.

Format:
```json
{
  "run_date": "2026-09-14T10:00:00Z",
  "results": [
    {
      "locale": "indonesia",
      "category": "news",
      "period": "3days",
      "filename": "indonesia/news/news_3days_2026-09-14.json",
      "total_items": 5,
      "scraped_at": "2026-09-14T10:00:32Z"
    }
  ]
}
```

## Q: Berapa total files per run?

Total: **48 files** (8 categories × 3 periods × 2 locales) + 1 `index.json`.
