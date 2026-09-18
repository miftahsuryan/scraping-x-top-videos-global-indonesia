# FAQ

## Q: Apa itu Explore Mode?

Explore Mode adalah mode default yang mengambil konten viral dari halaman **Explore For You** di X/Twitter. Tidak memerlukan kategori atau keyword.

```bash
# Explore mode (default)
python main.py

# Dengan periode tertentu
python main.py --period 1day
```

## Q: Bagaimana cara menggunakan Search Mode?

Search Mode memungkinkan pencarian berdasarkan kategori dan keyword:

```bash
python main.py --mode search --category news
python main.py --mode search --category news,economic --keywords-id "berita"
```

## Q: Periode apa saja yang tersedia?

| Periode | Deskripsi |
|---|---|
| `1day` | 24 jam terakhir |
| `3days` | 3 hari terakhir |
| `weekly` | Senin -> hari ini |
| `monthly` | Tanggal 1 -> hari ini |

```bash
python main.py --period 1day
python main.py --period 3days
python main.py --period weekly
python main.py --period monthly
```

## Q: Bagaimana cara custom keywords?

```bash
python main.py --mode search --category news --keywords-id "berita terkini,update" --keywords-gl "breaking news"
```

Custom keywords digabung dengan default keywords. Match logic: OR (jika salah satu keyword cocok).

## Q: Bagaimana cara scrape multiple categories?

```bash
python main.py --mode search --category news,economic,social
```

Gunakan comma-separated untuk multiple categories.

## Q: Bagaimana cara cek output files?

```bash
# Lihat semua files
ls -R OUTPUT-X/

# Lihat index.json
cat OUTPUT-X/index.json | python -m json.tool

# Lihat file tertentu
cat OUTPUT-X/explore/explore_3days_2026-09-18.json | python -m json.tool
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

## Q: Bagaimana cara scrape hanya 1 periode?

```bash
python main.py --period 1day
python main.py --period 3days
python main.py --period weekly
python main.py --period monthly
```

## Q: Apa itu index.json?

`index.json` adalah master index yang berisi list semua hasil scraping per run. File ini di-overwrite setiap run.

Format (Explore Mode):
```json
{
  "run_date": "2026-09-18T10:00:00Z",
  "mode": "explore",
  "results": [
    {
      "locale": "mixed",
      "category": "explore",
      "period": "3days",
      "mode": "explore",
      "filename": "explore/explore_3days_2026-09-18.json",
      "total_items": 10,
      "scraped_at": "2026-09-18T10:00:32Z"
    }
  ]
}
```

## Q: Berapa total item per run?

- **Explore Mode**: 4 file x 10 item = **40 tweets** (1 per periode)
- **Search Mode**: Tergantung jumlah kategori x periode x locale x 10 item

## Q: Bagaimana cara menjalankan Web Dashboard?

```bash
python web_ui.py
```

Buka `http://127.0.0.1:8000` di browser. Dashboard mendukung pemilihan mode (Explore/Search), periode, dan monitoring status secara real-time.

## Q: Bagaimana cara mendapatkan cookie X/Twitter?

1. Buka [x.com](https://x.com) di Chrome/Firefox, login ke akun Anda
2. Tekan `F12` atau `Ctrl+Shift+I` untuk buka Developer Tools
3. Pergi ke tab **Application** (Chrome) atau **Storage** (Firefox)
4. Di panel kiri, buka **Cookies** lalu pilih `https://x.com`
5. Cari nilai `auth_token` dan `ct0`, copy ke file `.env`

## Q: Bagaimana cara debugging jika scraping gagal?

```bash
# Jalankan dengan browser terlihat
python main.py --no-headless

# Jalankan dengan 1 periode saja
python main.py --period 1day --no-headless
```
