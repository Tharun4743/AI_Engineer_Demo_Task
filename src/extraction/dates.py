import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
import email.utils

RELATIVE_PATTERN = re.compile(
    r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago",
    re.IGNORECASE
)


class DateExtractor:
    """Robust date extractor supporting ISO formats, RFC 2822 (RSS), relative dates, and regex heuristics."""

    def extract_date(self, text_or_date: Optional[str]) -> Tuple[Optional[datetime], str]:
        """Parses a date and returns (parsed_datetime_utc, date_method)."""
        if not text_or_date:
            return None, "none"

        raw = text_or_date.strip()

        # 1. ISO 8601 parsing
        try:
            # Handle trailing Z
            iso_str = raw.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt, "iso_format"
        except (ValueError, TypeError):
            pass

        # 2. RFC 2822 (Standard RSS pubDate)
        try:
            parsed_tuple = email.utils.parsedate_to_datetime(raw)
            if parsed_tuple:
                if parsed_tuple.tzinfo is None:
                    parsed_tuple = parsed_tuple.replace(tzinfo=timezone.utc)
                else:
                    parsed_tuple = parsed_tuple.astimezone(timezone.utc)
                return parsed_tuple, "rss_pubdate"
        except Exception:
            pass

        # 3. Relative date patterns (e.g., "3 hours ago", "2 days ago")
        match = RELATIVE_PATTERN.search(raw)
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()
            now = datetime.now(timezone.utc)

            delta = timedelta()
            if unit == "second":
                delta = timedelta(seconds=value)
            elif unit == "minute":
                delta = timedelta(minutes=value)
            elif unit == "hour":
                delta = timedelta(hours=value)
            elif unit == "day":
                delta = timedelta(days=value)
            elif unit == "week":
                delta = timedelta(weeks=value)
            elif unit == "month":
                delta = timedelta(days=value * 30)
            elif unit == "year":
                delta = timedelta(days=value * 365)

            return now - delta, "relative_parser"

        if "yesterday" in raw.lower():
            now = datetime.now(timezone.utc)
            return now - timedelta(days=1), "relative_parser"

        # 4. Standard Date Regex Heuristic: YYYY-MM-DD or DD Month YYYY
        date_match = re.search(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", raw)
        if date_match:
            try:
                y, m, d = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                return datetime(y, m, d, tzinfo=timezone.utc), "regex_heuristic"
            except ValueError:
                pass

        return None, "unresolved"

    def is_within_hours(self, dt: Optional[datetime], hours: int = 24) -> bool:
        """Verifies if the given UTC datetime is within the past N hours."""
        if not dt:
            return False
        now = datetime.now(timezone.utc)
        diff = (now - dt).total_seconds()
        return 0 <= diff <= (hours * 3600)


date_extractor = DateExtractor()
