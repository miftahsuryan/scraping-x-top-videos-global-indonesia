import re

from src.models import EngagementMetrics


def parse_metric_value(raw: str | None) -> int:
    """Mengonversi teks metrik (contoh: '1.2K', '3.4M', '450', '1,200') menjadi integer."""
    if not raw:
        return 0
    text = raw.strip().upper().replace(",", "").replace(" ", "")
    match = re.search(r"([\d.]+)\s*([KM]?)", text)
    if not match:
        return 0
    num_str, unit = match.groups()
    try:
        val = float(num_str)
        if unit == "K":
            return int(val * 1_000)
        elif unit == "M":
            return int(val * 1_000_000)
        return int(val)
    except ValueError:
        return 0


def calculate_engagement(
    likes: int, reposts: int, views: int, replies: int = 0
) -> EngagementMetrics:
    """Menghitung skor kombinasi: Likes + Reposts + Views."""
    total = int(likes + reposts + views)
    return EngagementMetrics(
        likes=likes,
        views=views,
        reposts=reposts,
        replies=replies,
        total_score=total,
    )
