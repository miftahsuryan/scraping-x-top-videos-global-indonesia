import logging
import os

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
OUTPUT_DIR = "output"
OUTPUT_FILE_PATTERN_MONTHLY_ID = "top15_indonesia_monthly_{}.json"
OUTPUT_FILE_PATTERN_MONTHLY_GL = "top15_global_monthly_{}.json"
OUTPUT_FILE_PATTERN_3DAYS_ID = "top15_indonesia_3days_{}.json"
OUTPUT_FILE_PATTERN_3DAYS_GL = "top15_global_3days_{}.json"

BROWSER_VIEWPORT_WIDTH = 1280
BROWSER_VIEWPORT_HEIGHT = 800
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)
BROWSER_LOCALE = "en-US"

MAX_SCROLLS = 12
SCRAPE_LIMIT = 15
MIN_ENGAGEMENT_SCORE = 5000

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

ALLOWED_TOPICS: dict[str, frozenset[str]] = {
    "highlight": frozenset([
        "viral", "trending", "breaking", "happening", "just in",
        "shocking", "unbelievable", "insane", "crazy", "epic",
        "legendary", "historic", "record", "first time", "massive",
        "huge", "explosion", "eruption", "disaster", "accident",
        "rescue", "survive", "miracle", "catch", "goal", "slam",
        "knockout", "champion", "final", "win", "score",
        "highlight", "replay", "moment", "reaction",
        "terjadi", "heboh", "mengejutkan", "gila", "keren",
        "legendaris", "bersejarah", "rekor", "pertama kali",
        "ledakan", "bencana", "kecelakaan", "selamat",
        "mukjizat", "gol", "juara", "menang", "skor",
        " momen", "reaksi",
    ]),
    "culture": frozenset([
        "music", "movie", "film", "concert", "festival", "art",
        "dance", "fashion", "food", "cook", "recipe", "restaurant",
        "tradition", "ceremony", "holiday", "celebrate", "k-pop",
        "anime", "manga", "game", "gaming", "esport", "sport",
        "football", "soccer", "basketball", "nba", "nfl", "cricket",
        "tennis", "olympic", "world cup", "premier league", "liga",
        "chef", "cuisine", "baking", "street food", "viral food",
        "celebrity", "actor", "actress", "singer", "rapper",
        "album", "song", "track", "concert", "tour",
        "musik", "konser", "seni", "tari", "makanan", "masak",
        "resep", "restoran", "tradisi", "upacara", "liburan",
        "selebrasi", "game", "gaming", "esport", "olahraga",
        "sepak bola", "basket", "liga", "kuliner", "artis",
        "penyanyi", "rapper", "album", "lagu", "film",
    ]),
    "social": frozenset([
        "protest", "rally", "march", "activist", "movement",
        "human rights", "climate", "environment", "education",
        "health", "mental health", "community", "volunteer",
        "charity", "donation", "rescue", "solidarity",
        "election", "vote", "politics", "policy", "government",
        "parliament", "congress", "president", "minister",
        "society", "culture", "heritage", "identity",
        "immigrant", "refugee", "equality", "justice",
        "security", "conflict", "peace", "humanitarian",
        "protes", "unjuk rasa", "aktivis", "gerakan",
        "hak asasi", "iklim", "lingkungan", "pendidikan",
        "kesehatan", "komunitas", "relawan", "amal", "donasi",
        "pilkada", "pemilu", "politik", "kebijakan",
        "pemerintah", "parlemen", "presiden", "menteri",
        "masyarakat", "budaya", "warisan", "imigran",
        "pengungsi", "kesetaraan", "keadilan", "keamanan",
        "konflik", "perdamaian",
    ]),
    "technology": frozenset([
        "ai", "artificial intelligence", "machine learning", "robot",
        "tech", "gadget", "smartphone", "iphone", "android",
        "software", "hardware", "startup", "app", "coding",
        "programming", "python", "javascript", "blockchain",
        "crypto", "bitcoin", "ethereum", "nft", "metaverse",
        "spacex", "nasa", "rocket", "satellite", "starlink",
        "space", "mars", "launch", "orbit", "renewable",
        "solar", "ev", "electric car", "tesla", "battery",
        "quantum", "biotech", "fintech", "5g", "wifi",
        "hack", "cyber", "data", "cloud", "server",
        "kecerdasan buatan", "teknologi", "perangkat lunak",
        "perangkat keras", "pemrograman", "kripto",
        "luar angkasa", "energi terbarukan", "mobil listrik",
        "baterai", "kuantum", "bioteknologi", "siber",
    ]),
}

QUERY_INDONESIA = "indonesia filter:videos min_faves:5000 -is:reply"
QUERY_GLOBAL = "filter:videos min_faves:10000 -is:reply"
