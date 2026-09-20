import json
from pathlib import Path

from src.downloader import (
    _load_reports,
    _parse_download_links,
    _should_skip,
    download_path_for,
    extract_quality_score,
    resolve_tweet_id,
    select_best_quality,
)


def test_resolve_tweet_id_standard():
    assert resolve_tweet_id("https://x.com/user/status/1234567890") == "1234567890"


def test_resolve_tweet_id_with_query_params():
    assert resolve_tweet_id("https://x.com/user/status/1234567890?ref=abc") == "1234567890"


def test_resolve_tweet_id_twitter_domain():
    assert resolve_tweet_id("https://twitter.com/user/status/9999999999") == "9999999999"


def test_resolve_tweet_id_invalid():
    assert resolve_tweet_id("https://x.com/user") == ""
    assert resolve_tweet_id("not a url") == ""
    assert resolve_tweet_id("") == ""


def test_extract_quality_score():
    assert extract_quality_score("Download 1080P MP4") == 1080
    assert extract_quality_score("720p video") == 720
    assert extract_quality_score("480 quality") == 480
    assert extract_quality_score("no quality info") == 0
    assert extract_quality_score("2160P 4K") == 2160


def test_select_best_quality_single_link():
    links = ["https://example.com/video.mp4"]
    texts = ["some text"]
    assert select_best_quality(links, texts) == "https://example.com/video.mp4"


def test_select_best_quality_multiple():
    links = [
        "https://example.com/480.mp4",
        "https://example.com/1080.mp4",
        "https://example.com/720.mp4",
    ]
    texts = ["480P quality", "1080P HD", "720P HD"]
    assert select_best_quality(links, texts) == "https://example.com/1080.mp4"


def test_select_best_quality_empty():
    assert select_best_quality([], []) is None


def test_download_path_for():
    path = download_path_for("1234567890", "2026-09-20")
    assert path == Path("OUTPUT-X/downloads/2026-09-20/tweet_1234567890.mp4")


def test_should_skip_existing_download(tmp_path):
    tweet = {"download_path": str(tmp_path / "nonexistent.mp4")}
    assert _should_skip(tweet) is False


def test_should_skip_no_download_path():
    tweet = {"tweet_url": "https://x.com/user/status/123"}
    assert _should_skip(tweet) is False


def test_should_skip_with_existing_file(tmp_path):
    existing_file = tmp_path / "video.mp4"
    existing_file.write_bytes(b"fake video data")
    tweet = {"download_path": str(existing_file)}
    assert _should_skip(tweet) is True


def test_parse_download_links_with_mp4():
    html = '<a href="https://video.twimg.com/ext_tw_video/123/pu/vid/480/abc.mp4">480P</a>'
    urls, _texts = _parse_download_links(html)
    assert len(urls) == 1
    assert "abc.mp4" in urls[0]


def test_parse_download_links_with_quality():
    html = (
        '<a href="https://example.com/v1.mp4">720P</a>'
        '<a href="https://example.com/v2.mp4">1080P</a>'
    )
    urls, _texts = _parse_download_links(html)
    assert len(urls) == 2


def test_parse_download_links_empty():
    urls, texts = _parse_download_links("<div>No links here</div>")
    assert urls == []
    assert texts == []


def test_load_reports_single(tmp_path):
    report = {
        "scraped_date": "2026-09-20",
        "tweets": [{"tweet_url": "https://x.com/user/status/123"}],
    }
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")

    result = _load_reports(tmp_path / "nonexistent_index.json", report_file)
    assert len(result) == 1
    assert result[0]["scraped_date"] == "2026-09-20"


def test_load_reports_from_index(tmp_path):
    index = {
        "results": [{"filename": "explore/report.json", "scraped_date": "2026-09-20"}],
    }
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")

    report = {"scraped_date": "2026-09-20", "tweets": []}
    report_dir = tmp_path / "explore"
    report_dir.mkdir()
    (report_dir / "report.json").write_text(json.dumps(report), encoding="utf-8")

    result = _load_reports(index_path, None)
    assert len(result) == 1
    assert result[0]["scraped_date"] == "2026-09-20"


def test_load_reports_missing_file(tmp_path):
    index = {"results": [{"filename": "missing/report.json"}]}
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = _load_reports(index_path, None)
    assert len(result) == 0


def test_video_tweet_model_backward_compat():
    from src.models import VideoTweet

    tweet = VideoTweet(
        tweet_url="https://x.com/user/status/123",
        engagement={"likes": 0, "views": 0, "reposts": 0, "replies": 0, "total_score": 0},
    )
    assert tweet.download_path is None


def test_video_tweet_model_with_download():
    from src.models import VideoTweet

    tweet = VideoTweet(
        tweet_url="https://x.com/user/status/123",
        engagement={"likes": 0, "views": 0, "reposts": 0, "replies": 0, "total_score": 0},
        download_path="OUTPUT-X/downloads/2026-09-20/tweet_123.mp4",
    )
    assert tweet.download_path == "OUTPUT-X/downloads/2026-09-20/tweet_123.mp4"
