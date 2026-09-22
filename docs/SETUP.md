# Local Setup Guide

Panduan langkah demi langkah untuk menjalankan project ini di mesin lokal.

---

## Prasyarat

- Python 3.10+
- macOS, Linux, atau Windows
- Akun X (Twitter) yang aktif

---

## Langkah 1 — Clone Repository

```bash
git clone <repository-url>
cd SCRAPING-CONTENT-X
```

---

## Langkah 2 — Buat Virtual Environment

```bash
python3 -m venv .venv
```

Aktifkan virtual environment:

| OS | Perintah |
|---|---|
| macOS / Linux | `source .venv/bin/activate` |
| Windows | `.venv\Scripts\activate` |

---

## Langkah 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Langkah 4 — Install Browser Chromium

```bash
playwright install chromium
```

---

## Langkah 5 — Konfigurasi `.env`

Copy template `.env.example` ke `.env`:

```bash
cp .env.example .env
```

Buka file `.env` dan isi nilainya:

```env
X_AUTH_TOKEN=your_auth_token_here
X_CT0=your_ct0_here
HEADLESS=true
```

---

## Langkah 6 — Mendapatkan Cookie X/Twitter

Cookie diperlukan agar scraper bisa mengakses konten di X.

1. Buka [x.com](https://x.com) di Chrome/Firefox, login ke akun Anda
2. Tekan `F12` atau `Ctrl+Shift+I` untuk buka Developer Tools
3. Pergi ke tab **Application** (Chrome) atau **Storage** (Firefox)
4. Di panel kiri, buka **Cookies** lalu pilih `https://x.com`
5. Cari nilai `auth_token` dan `ct0`
6. Copy masing-masing ke file `.env`

---

## Langkah 7 — Jalankan Scraper

```bash
python main.py
```

Untuk opsi lainnya, lihat [Usage Guide](USAGE.md).

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError` | Pastikan venv aktif, lalu `pip install -r requirements.txt` |
| `playwright install chromium` gagal | Jalankan `playwright install --with-deps chromium` (Linux) |
| Scraper langsung keluar tanpa error | Periksa nilai `X_AUTH_TOKEN` dan `X_CT0` di `.env` |
| Browser tidak muncul | Set `HEADLESS=false` di `.env` untuk debugging |
| Akun kena rate limit | Tunggu beberapa menit, scraper sudah ada exponential backoff |
