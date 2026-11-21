import hashlib
import re
from typing import Set, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


class Deduplicator:
    """Canonical URL normalization and in-memory hash deduplication engine."""

    # Parameters to strip during canonicalization
    TRACKING_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "msclkid", "ref", "source", "mc_cid", "mc_eid"
    }

    def __init__(self):
        self._seen_hashes: Set[str] = set()

    def normalize_url(self, url: str) -> str:
        """Normalizes a URL by stripping tracking parameters, trailing slashes, and downcasing netloc."""
        if not url:
            return ""
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # Filter query params
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_query = [(k, v) for k, v in query_pairs if k.lower() not in self.TRACKING_PARAMS]
        filtered_query.sort()
        query_str = urlencode(filtered_query)

        # Reconstruct canonical url
        canonical = urlunparse((
            parsed.scheme.lower() or "https",
            netloc,
            path,
            "",
            query_str,
            ""  # strip fragments
        ))
        return canonical

    def url_hash(self, url: str) -> str:
        """Computes SHA-256 fingerprint for canonical URL."""
        norm = self.normalize_url(url)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def is_seen(self, url: str) -> bool:
        """Checks if URL hash was already processed."""
        h = self.url_hash(url)
        return h in self._seen_hashes

    def mark_seen(self, url: str) -> bool:
        """Marks URL as seen. Returns True if newly added, False if already present."""
        h = self.url_hash(url)
        if h in self._seen_hashes:
            return False
        self._seen_hashes.add(h)
        return True

    def clear(self):
        self._seen_hashes.clear()


deduplicator = Deduplicator()
