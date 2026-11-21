from datetime import datetime, timezone, timedelta
from src.extraction.dates import date_extractor


def test_iso_parsing():
    dt_str = "2026-11-20T14:30:00Z"
    dt, method = date_extractor.extract_date(dt_str)
    assert dt is not None
    assert method == "iso_format"
    assert dt.year == 2026
    assert dt.month == 11
    assert dt.day == 20


def test_rss_rfc2822_parsing():
    rfc_str = "Fri, 20 Nov 2026 18:00:00 +0000"
    dt, method = date_extractor.extract_date(rfc_str)
    assert dt is not None
    assert method == "rss_pubdate"
    assert dt.hour == 18


def test_relative_date_parsing():
    dt, method = date_extractor.extract_date("3 hours ago")
    assert dt is not None
    assert method == "relative_parser"
    now = datetime.now(timezone.utc)
    assert abs((now - dt).total_seconds() - 3 * 3600) < 10

    dt_y, method_y = date_extractor.extract_date("yesterday")
    assert dt_y is not None
    assert method_y == "relative_parser"


def test_24h_freshness_check():
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=6)
    old = now - timedelta(hours=30)

    assert date_extractor.is_within_hours(recent, hours=24) is True
    assert date_extractor.is_within_hours(old, hours=24) is False
