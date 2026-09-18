from pydantic import BaseModel, Field


class EngagementMetrics(BaseModel):
    likes: int = Field(default=0, description="Jumlah likes pada tweet")
    views: int = Field(default=0, description="Jumlah tayangan/views pada tweet")
    reposts: int = Field(default=0, description="Jumlah reposts/retweets pada tweet")
    replies: int = Field(default=0, description="Jumlah balasan/replies pada tweet")
    total_score: int = Field(
        default=0, description="Formula kombinasi: likes + reposts + views"
    )


class VideoTweet(BaseModel):
    tweet_url: str = Field(..., description="Link permanen URL dari tweet")
    video_url: str | None = Field(
        default=None, description="Direct URL file video / stream jika terdeteksi"
    )
    caption: str = Field(
        default="", description="Teks atau caption utama dari tweet"
    )
    username: str = Field(default="", description="Display name pemilik tweet")
    handle: str = Field(
        default="", description="Username/handle pembuat tweet (misal: @user)"
    )
    posted_at: str | None = Field(default=None, description="Waktu tweet dibuat")
    engagement: EngagementMetrics = Field(
        ..., description="Rincian dan total skor metrik keterlibatan"
    )
    source: str = Field(
        default="search", description="Source scraping: 'search' atau 'explore'"
    )


class ScrapeReport(BaseModel):
    period: str = Field(..., description="Periode scraping (3days, weekly, monthly)")
    category: str = Field(..., description="Kategori konten (engagement, news, economic, social, technology, research)")
    locale: str = Field(..., description="Lokalitas (indonesia, global)")
    scraped_date: str = Field(..., description="Tanggal target scraping (YYYY-MM-DD)")
    scraped_at: str = Field(..., description="Waktu eksekusi scraping (ISO 8601)")
    formula: str = Field(
        default="likes + reposts + views",
        description="Formula penghitungan ranking keterlibatan",
    )
    mode: str = Field(
        default="search", description="Mode scraping: 'search' atau 'explore'"
    )
    total_items: int = Field(
        default=0, description="Total tweet yang berhasil dikumpulkan"
    )
    tweets: list[VideoTweet] = Field(
        default_factory=list, description="Daftar tweet terurut berdasarkan engagement score"
    )
