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
        default="", description="Teks atau caption utama dari tweet yang memuat video"
    )
    username: str = Field(default="", description="Display name pemilik tweet")
    handle: str = Field(
        default="", description="Username/handle pembuat tweet (misal: @user)"
    )
    posted_at: str | None = Field(default=None, description="Waktu tweet dibuat")
    engagement: EngagementMetrics = Field(
        ..., description="Rincian dan total skor metrik keterlibatan"
    )


class ScrapeReport(BaseModel):
    scraped_date: str = Field(..., description="Tanggal target scraping (YYYY-MM-DD)")
    scraped_at: str = Field(..., description="Waktu eksekusi scraping (ISO 8601)")
    formula: str = Field(
        default="likes + reposts + views",
        description="Formula penghitungan ranking keterlibatan",
    )
    total_items: int = Field(
        default=20, description="Total video tweet yang berhasil dikumpulkan"
    )
    indonesia_explore: list[VideoTweet] = Field(
        default_factory=list, description="Top 15 video tweet dari Explore Indonesia"
    )
    global_explore: list[VideoTweet] = Field(
        default_factory=list, description="Top 15 video tweet dari Explore Global"
    )
