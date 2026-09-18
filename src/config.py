import logging
import os
import re

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)

HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN", "")
X_CT0 = os.getenv("X_CT0", "")
CF_CLEARANCE = os.getenv("CF_CLEARANCE", "")

SCRAPING_DATE_FORMAT = "%Y-%m-%d"
OUTPUT_DIR = "OUTPUT-X"

BROWSER_VIEWPORT_WIDTH = 1280
BROWSER_VIEWPORT_HEIGHT = 800
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)
BROWSER_LOCALE = "en-US"

MAX_SCROLLS = 12

CATEGORIES: list[str] = [
    "engagement", "news", "economic", "social", "technology", "research", "business", "social_media",
]

PERIODS: list[str] = ["1day", "3days", "weekly", "monthly"]

MIN_FAVES: dict[str, int] = {
    "1day": 100,
    "3days": 500,
    "weekly": 1000,
    "monthly": 1000,
}

SCRAPE_LIMIT: dict[str, int] = {
    "1day": 10,
    "3days": 10,
    "weekly": 10,
    "monthly": 10,
}

DEFAULT_KEYWORDS_ID: dict[str, list[str]] = {
    "engagement": [
        "heboh", "geger", "gempar", "syok", "kaget",
        "ramai dibicarakan", "ramai diperbincangkan", "bikin heboh",
        "jadi sorotan", "curi perhatian", "banjir komentar",
        "disorot netizen", "jadi bahan obrolan", "netizen heboh",
        "bikin geger", "tak disangka", "mengejutkan publik", "gempar netizen",
    ],
    "news": [
        "berita terkini", "kabar terbaru", "info terkini", "kabar terhangat",
        "berita hari ini", "berita mengejutkan", "update terbaru",
        "kabar duka", "kabar gembira", "peristiwa terkini", "kejadian terbaru",
        "laporan terbaru", "sorotan berita", "headline hari ini",
        "isu terkini", "insiden terbaru", "berita nasional", "kronologi kejadian",
    ],
    "economic": [
        "pasar saham", "ihsg", "rupiah melemah", "rupiah menguat",
        "harga naik", "harga turun", "harga bbm", "inflasi",
        "resesi ekonomi", "bi rate", "suku bunga", "investasi saham",
        "bursa efek", "kripto indonesia", "harga emas", "nilai tukar",
        "utang negara", "apbn", "pajak naik", "subsidi bbm",
        "harga sembako", "daya beli", "pertumbuhan ekonomi",
    ],
    "social": [
        "bansos", "kemiskinan", "kesejahteraan sosial", "unjuk rasa",
        "demo buruh", "bantuan sosial", "korban bencana", "penggalangan dana",
        "aksi solidaritas", "anak jalanan", "kelaparan", "gizi buruk",
        "pengungsi", "korban kekerasan", "hak asasi manusia", "diskriminasi",
        "kesenjangan sosial", "gerakan sosial", "relawan bencana", "donasi bencana",
    ],
    "technology": [
        "teknologi terbaru", "aplikasi lokal", "startup lokal",
        "inovasi anak bangsa", "hp terbaru", "gawai terbaru",
        "kecerdasan buatan", "robot canggih", "aplikasi buatan indonesia",
        "perusahaan rintisan", "teknologi ai", "inovasi digital",
        "transformasi digital", "produk teknologi baru", "gadget terbaru",
        "peluncuran aplikasi", "startup teknologi", "riset teknologi",
    ],
    "research": ["penelitian", "riset", "studi", "discovery"],
    "business": [
        "bisnis", "perusahaan", "ceo perusahaan", "direktur utama",
        "merger perusahaan", "akuisisi bisnis", "ipo saham",
        "pendapatan perusahaan", "laba perusahaan", "rugi perusahaan",
        "phk massal", "kemitraan bisnis", "waralaba", "umkm naik kelas",
        "wirausaha muda", "pengusaha sukses", "strategi bisnis",
        "ekspansi usaha", "brand lokal", "bisnis online",
        "jualan online", "bangkrut",
    ],
    "social_media": [
        "media sosial", "fitur baru instagram", "update tiktok",
        "algoritma twitter", "x down", "instagram down",
        "kebijakan media sosial", "konten kreator", "monetisasi konten",
        "centang biru", "verifikasi akun", "akun diblokir",
        "tren tiktok", "live streaming", "influencer marketing",
        "platform media sosial", "update algoritma", "fitur terbaru medsos",
        "meta rilis fitur", "youtube shorts",
    ],
}

DEFAULT_KEYWORDS_GL: dict[str, list[str]] = {
    "engagement": [
        "went viral", "blew up", "buzzing", "sensation",
        "can't stop watching", "took the internet by storm",
        "everyone's talking about", "internet is obsessed", "gone viral",
        "viral moment", "broke the internet", "stopped scrolling",
        "can't unsee", "viral sensation", "jaw-dropping", "mind-blowing",
        "instant hit",
    ],
    "news": [
        "breaking news", "headlines", "just in", "developing story",
        "top story", "news alert", "live update", "world news",
        "latest news", "reports say", "according to reports",
        "major incident", "this just happened", "exclusive report",
        "confirmed reports",
    ],
    "economic": [
        "stock market", "wall street", "inflation", "recession",
        "interest rate", "federal reserve", "nasdaq", "s&p 500",
        "market crash", "crypto crash", "market rally", "economic downturn",
        "gdp growth", "trade war", "oil prices", "gold prices",
        "jobs report", "market volatility", "bear market", "bull market",
    ],
    "social": [
        "welfare", "food bank", "protest", "homelessness",
        "wage strike", "human rights", "charity", "relief fund",
        "refugees", "social justice", "inequality", "activism",
        "grassroots movement", "community support", "disaster relief",
        "fundraising campaign", "volunteers", "mutual aid",
    ],
    "technology": [
        "tech news", "ai breakthrough", "new gadget", "startup funding",
        "app launch", "tech giant", "silicon valley", "product launch",
        "software update", "tech innovation", "ai model", "chip technology",
        "venture capital", "tech industry", "smart device",
        "next-gen tech", "robotics breakthrough",
    ],
    "research": ["research", "study", "discovery"],
    "business": [
        "business", "CEO resigns", "CEO steps down", "merger",
        "acquisition", "IPO", "quarterly earnings", "company profits",
        "layoffs", "business partnership", "franchise", "small business",
        "entrepreneur", "business strategy", "corporate expansion",
        "brand deal", "e-commerce", "business deal", "corporate news",
        "retail", "supply chain", "bankruptcy",
    ],
    "social_media": [
        "social media", "new feature", "algorithm change", "platform outage",
        "app update", "blue checkmark", "account verification", "content creator",
        "creator economy", "monetization update", "community guidelines",
        "account banned", "live streaming", "influencer marketing",
        "platform update", "app down", "TikTok ban", "Meta announcement",
        "YouTube Shorts", "X update",
    ],
}

NSFW_KEYWORDS = frozenset([
    "porn", "xxx", "nude", "naked", "nsfw",
    "erotic", "onlyfans", "boobs", "tits",
    "fap", "masturbat", "orgasm", "slut", "whore",
    "hentai", "ecchi", "lewd", "explicit", "18+",
    "oiled armpits", "near slipped out", "bondage",
    "big butt", "slipped out", "jrkkk", "jerkk",
    "send vids", "front or back", "settle it below",
    "tummytummy", "waggin mi tail", "bouncy",
    "taking my top off", "help please", "pantsu",
    "pussy", "dick", "cock", "asshole", "dildo",
    "handjob", "blowjob", "threesome", "gangbang",
    "creampie", "anal", "swallow", "deepthroat",
    "footjob", "titjob", "cum", "squirting", "bdsm",
    "latex", "stockings", "stripper", "camgirl",
    "vagina", "penis", "kontol", "memek", "ngentot",
    "coli", "bokep", "bugil", "telanjang", "setengah telanjang",
    "saru", "vulgar", "cabul", "pornografi",
])

NSFW_HANDLE_PATTERNS = frozenset([
    "uncaged", "waifu", "cosplay", "underbust",
    "onlyfans", "lewd", "ecchi", "hentai",
    "melons", "wifey",
    "nsfw", "xxx", "naked", "nude", "porn",
    "erotic", "camgirl", "stripper",
    "bugil", "telanjang", "bokep", "saru",
])

ALLOWED_VIDEO_DOMAINS = frozenset([
    "video.twimg.com",
])


def parse_keywords(raw: str | None) -> list[str]:
    """Parse comma-separated keywords, support multi-word dengan quote.

    Contoh:
        'berita,ekonomi' → ['berita', 'ekonomi']
        '"breaking news",update' → ['breaking news', 'update']
    """
    if not raw:
        return []
    pattern = r'"([^"]*)"|(\S+)'
    matches = re.findall(pattern, raw)
    return [m[0] or m[1] for m in matches]
