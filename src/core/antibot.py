import asyncio
from typing import Optional, Tuple
from src.core.http import http_client, USER_AGENTS
from src.core.logging import logger
import random

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class AntiBotFetcher:
    """Tiered fetching engine: Native HTTP -> curl_cffi TLS impersonation -> Playwright -> Skip."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    async def fetch(self, url: str, timeout_seconds: int = 15) -> Tuple[Optional[str], str]:
        """Fetches URL contents through escalating tiers. Returns (content, tier_used)."""
        # Tier 1: Native HTTP Async
        try:
            content = await http_client.get_text(url)
            if len(content) > 200 and not self._is_blocked(content):
                return content, "tier1_native"
            logger.info(f"Tier 1 returned weak/blocked content for {url}. Escalating to Tier 2...")
        except Exception as e:
            logger.info(f"Tier 1 native fetch failed for {url} ({e}). Escalating to Tier 2...")

        # Tier 2: curl_cffi TLS browser fingerprint impersonation
        if HAS_CURL_CFFI:
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: cffi_requests.get(
                        url,
                        impersonate="chrome120",
                        timeout=timeout_seconds,
                        headers={"User-Agent": random.choice(USER_AGENTS)}
                    )
                )
                if response.status_code == 200 and len(response.text) > 200 and not self._is_blocked(response.text):
                    return response.text, "tier2_curl_cffi"
                logger.info(f"Tier 2 curl_cffi blocked/status {response.status_code} on {url}. Escalating...")
            except Exception as e:
                logger.info(f"Tier 2 curl_cffi failed for {url}: {e}")

        # Tier 3: Playwright Headless Browser
        if HAS_PLAYWRIGHT:
            try:
                content = await self._fetch_playwright(url, timeout_seconds)
                if content and len(content) > 200 and not self._is_blocked(content):
                    return content, "tier3_playwright"
            except Exception as e:
                logger.warning(f"Tier 3 playwright failed for {url}: {e}")

        # Tier 4: Skip and Log
        logger.warning(f"All fetch tiers exhausted for {url}. Skipping record.")
        return None, "tier4_failed"

    def _is_blocked(self, content: str) -> bool:
        lower = content.lower()
        blocked_signatures = [
            "access denied",
            "just a moment...",
            "cloudflare",
            "attention required! | cloudflare",
            "recaptcha",
            "ddos-guard",
            "403 forbidden",
            "enable javascript and cookies to continue",
        ]
        return any(sig in lower and len(content) < 5000 for sig in blocked_signatures)

    async def _fetch_playwright(self, url: str, timeout_seconds: int) -> Optional[str]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_seconds * 1000)
                await asyncio.sleep(1.0)
                content = await page.content()
                return content
            finally:
                await browser.close()


antibot_fetcher = AntiBotFetcher()
