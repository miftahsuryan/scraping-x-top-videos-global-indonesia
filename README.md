# X/Twitter Video Scraper (8 Categories, 3 Periods, 2 Locales)

Proyek ini adalah scraper otomatis untuk mengumpulkan dan memeringkat tweet di X (Twitter) berdasarkan **8 kategori konten**, **3 periode waktu**, dan **2 locale** (Indonesia & Global).

**Total: 48 file output** per sesi scraping (8 × 3 × 2).

---

## Kategori

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

## Periode

| Periode | Deskripsi | Limit | min_faves |
|---|---|---|---|
| `3days` | 3 hari terakhir | 5 | 500 |
| `weekly` | Senin → hari ini | 10 | 1000 |
| `monthly` | Tanggal 1 → hari ini | 10 | 1000 |

## Locale

| Locale | Filter |
|---|---|
| `indonesia` | Keywords Indonesia (default) |
| `global` | Keywords English (default) |

---

## Formula Pemeringkatan

$$\text{Engagement Score} = \text{Likes} + \text{Reposts} + \text{Views}$$

---

## Struktur Output

```
output/
├── index.json
├── indonesia/
│   ├── engagement/
│   │   ├── engagement_3days_2026-09-14.json
│   │   ├── engagement_week_2026-W37.json
│   │   └── engagement_month_2026-09.json
│   ├── news/
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

---

## CLI Usage

### Default (semua period, semua category, semua locale)
```bash
python main.py
```

### Period tertentu
```bash
python main.py --period 3days
python main.py --period weekly
python main.py --period monthly
```

### Category tertentu
```bash
python main.py --category news
python main.py --category news,economic,social
```

### Custom Keywords
```bash
python main.py --category news --keywords-id "berita terkini,update" --keywords-gl "breaking news"
```

### Debugging (browser visible)
```bash
python main.py --no-headless
```

### Kombinasi
```bash
python main.py --period 3days --category news,economic --keywords-id "ekonomi,berita" --keywords-gl "economy,news"
```

---

## Custom Keywords

- Format: comma-separated, support multi-word dengan quote
- Case-insensitive (huruf besar/kecil tidak masalah)
- Match logic: OR (jika salah satu keyword cocok)
- Digabung dengan default keywords

**Contoh:**
```bash
--keywords-id "berita terkini,ekonomi pasar"
--keywords-gl "breaking news,stock market"
```

---

## Default Keywords

### Indonesia
| Kategori | Keywords |
|---|---|
| engagement | heboh, geger, gempar, syok, kaget, ramai dibicarakan, bikin heboh, jadi sorotan, curi perhatian, banjir komentar, disorot netizen, jadi bahan obrolan, netizen heboh, bikin geger, tak disangka, mengejutkan publik, gempar netizen |
| news | berita terkini, kabar terbaru, info terkini, kabar terhangat, berita hari ini, berita mengejutkan, update terbaru, kabar duka, kabar gembira, peristiwa terkini, kejadian terbaru, laporan terbaru, sorotan berita, headline hari ini, isu terkini, insiden terbaru, berita nasional, kronologi kejadian |
| economic | pasar saham, ihsg, rupiah melemah, rupiah menguat, harga naik, harga turun, harga bbm, inflasi, resesi ekonomi, bi rate, suku bunga, investasi saham, bursa efek, kripto indonesia, harga emas, nilai tukar, utang negara, apbn, pajak naik, subsidi bbm, harga sembako, daya beli, pertumbuhan ekonomi |
| social | bansos, kemiskinan, kesejahteraan sosial, unjuk rasa, demo buruh, bantuan sosial, korban bencana, penggalangan dana, aksi solidaritas, anak jalanan, kelaparan, gizi buruk, pengungsi, korban kekerasan, hak asasi manusia, diskriminasi, kesenjangan sosial, gerakan sosial, relawan bencana, donasi bencana |
| technology | teknologi terbaru, aplikasi lokal, startup lokal, inovasi anak bangsa, hp terbaru, gawai terbaru, kecerdasan buatan, robot canggih, aplikasi buatan indonesia, perusahaan rintisan, teknologi ai, inovasi digital, transformasi digital, produk teknologi baru, gadget terbaru, peluncuran aplikasi, startup teknologi, riset teknologi |
| research | penelitian, riset, studi, discovery |
| business | bisnis, perusahaan, ceo perusahaan, direktur utama, merger perusahaan, akuisisi bisnis, ipo saham, pendapatan perusahaan, laba perusahaan, rugi perusahaan, phk massal, kemitraan bisnis, waralaba, umkm naik kelas, wirausaha muda, pengusaha sukses, strategi bisnis, ekspansi usaha, brand lokal, bisnis online, jualan online, bangkrut |
| social_media | media sosial, fitur baru instagram, update tiktok, algoritma twitter, x down, instagram down, kebijakan media sosial, konten kreator, monetisasi konten, centang biru, verifikasi akun, akun diblokir, tren tiktok, live streaming, influencer marketing, platform media sosial, update algoritma, fitur terbaru medsos, meta rilis fitur, youtube shorts |

### Global
| Kategori | Keywords |
|---|---|
| engagement | went viral, blew up, buzzing, sensation, can't stop watching, took the internet by storm, everyone's talking about, internet is obsessed, gone viral, viral moment, broke the internet, stopped scrolling, can't unsee, viral sensation, jaw-dropping, mind-blowing, instant hit |
| news | breaking news, headlines, just in, developing story, top story, news alert, live update, world news, latest news, reports say, according to reports, major incident, this just happened, exclusive report, confirmed reports |
| economic | stock market, wall street, inflation, recession, interest rate, federal reserve, nasdaq, s&p 500, market crash, crypto crash, market rally, economic downturn, gdp growth, trade war, oil prices, gold prices, jobs report, market volatility, bear market, bull market |
| social | welfare, food bank, protest, homelessness, wage strike, human rights, charity, relief fund, refugees, social justice, inequality, activism, grassroots movement, community support, disaster relief, fundraising campaign, volunteers, mutual aid |
| technology | tech news, ai breakthrough, new gadget, startup funding, app launch, tech giant, silicon valley, product launch, software update, tech innovation, ai model, chip technology, venture capital, tech industry, smart device, next-gen tech, robotics breakthrough |
| research | research, study, discovery |
| business | business, CEO resigns, CEO steps down, merger, acquisition, IPO, quarterly earnings, company profits, layoffs, business partnership, franchise, small business, entrepreneur, business strategy, corporate expansion, brand deal, e-commerce, business deal, corporate news, retail, supply chain, bankruptcy |
| social_media | social media, new feature, algorithm change, platform outage, app update, blue checkmark, account verification, content creator, creator economy, monetization update, community guidelines, account banned, live streaming, influencer marketing, platform update, app down, TikTok ban, Meta announcement, YouTube Shorts, X update |

---

## Instalasi

### 1. Prasyarat
- Python 3.10+
- Akun X (Twitter) yang aktif

### 2. Install Dependensi
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Konfigurasi `.env`
```bash
cp .env.example .env
```
Isi cookie X/Twitter (`auth_token`, `ct0`) dari browser Developer Tools.

---

## Web Dashboard (Local Only)

Dashboard browser untuk mengontrol scraper tanpa CLI.

### Menjalankan Dashboard
```bash
python web_ui.py
```

Buka `http://127.0.0.1:8000` di browser.

### Fitur Dashboard
- **Start Scraping**: Pilih period, category, custom keywords, headless mode
- **Status Monitoring**: Polling status job secara real-time
- **Report Browser**: Filter dan lihat hasil scraping
- **Report Detail**: Lihat ranked tweets dengan metrics

### API Endpoints
| Endpoint | Method | Description |
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

## Testing

```bash
pytest tests/
```

---

## Struktur Folder Proyek

```text
scraping/
├── AGENTS.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── conftest.py
├── main.py
├── web_ui.py
├── docs/
├── output/
├── specs/
│   ├── x-video-scraper/
│   └── web-ui/
├── src/
│   ├── __init__.py
│   ├── browser.py
│   ├── config.py
│   ├── extractor.py
│   ├── models.py
│   ├── scraper.py
│   └── web/
│       ├── __init__.py
│       ├── app.py
│       ├── schemas.py
│       ├── jobs.py
│       ├── reports.py
│       ├── templates/
│       │   └── index.html
│       └── static/
│           ├── app.js
│           └── styles.css
├── standards/
└── tests/
    └── test_extractor.py
```
