import asyncio
import time
import random
from typing import Dict, Optional, Any
from urllib.parse import urlparse
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from src.core.logging import logger

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
]


class TokenBucket:
    """Token bucket rate limiter for per-domain traffic control."""

    def __init__(self, rate: float = 5.0, capacity: float = 10.0):
        self.rate = rate  # Tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
                self.last_update = time.monotonic()
            else:
                self.tokens -= 1.0


class AsyncHttpClient:
    """High-performance async HTTP client with domain concurrency & token buckets."""

    def __init__(self, default_rate_limit: float = 5.0, max_domain_concurrency: int = 5):
        self.default_rate_limit = default_rate_limit
        self.max_domain_concurrency = max_domain_concurrency
        self.domain_buckets: Dict[str, TokenBucket] = {}
        self.domain_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._init_lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            async with self._init_lock:
                if self._session is None or self._session.closed:
                    timeout = aiohttp.ClientTimeout(total=20, connect=10)
                    connector = aiohttp.TCPConnector(limit=100, ssl=False)
                    self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc.lower() or "default"

    def _get_bucket(self, domain: str) -> TokenBucket:
        if domain not in self.domain_buckets:
            self.domain_buckets[domain] = TokenBucket(rate=self.default_rate_limit, capacity=self.default_rate_limit * 2)
        return self.domain_buckets[domain]

    def _get_semaphore(self, domain: str) -> asyncio.Semaphore:
        if domain not in self.domain_semaphores:
            self.domain_semaphores[domain] = asyncio.Semaphore(self.max_domain_concurrency)
        return self.domain_semaphores[domain]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1.0, max=8.0),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> aiohttp.ClientResponse:
        domain = self._get_domain(url)
        bucket = self._get_bucket(domain)
        semaphore = self._get_semaphore(domain)

        await bucket.acquire()

        req_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if headers:
            req_headers.update(headers)

        session = await self.get_session()
        async with semaphore:
            response = await session.get(url, headers=req_headers, **kwargs)
            if response.status == 429:
                retry_after = float(response.headers.get("Retry-After", 2.0))
                logger.warning(f"429 Rate limited on {domain}. Sleeping {retry_after}s...")
                await asyncio.sleep(retry_after)
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=429,
                    message="Too Many Requests",
                )
            return response

    async def get_text(self, url: str, **kwargs) -> str:
        resp = await self.get(url, **kwargs)
        async with resp:
            return await resp.text(errors="replace")

    async def get_json(self, url: str, **kwargs) -> Any:
        resp = await self.get(url, **kwargs)
        async with resp:
            return await resp.json(content_type=None)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


http_client = AsyncHttpClient()
