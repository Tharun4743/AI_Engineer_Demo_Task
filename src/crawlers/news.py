import asyncio
from typing import List, Dict
import feedparser
from src.core.http import http_client
from src.core.models import News
from src.extraction.dates import date_extractor
from src.storage.db import db_manager
from src.storage.dedup import deduplicator
from src.core.logging import logger

NEWS_SOURCES = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "Hacker News AI",
        "url": "https://hnrss.org/newest?q=AI",
    },
    {
        "name": "CNBC Tech",
        "url": "https://www.cnbc.com/id/19854910/device/rss/rss.html",
    },
    {
        "name": "NY Times Tech",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    },
    {
        "name": "Wired AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
    },
]


class NewsCrawler:
    """Collects fresh news articles from 5 distinct sources with strict 24h publication checks."""

    def __init__(self, max_age_hours: int = 24):
        self.max_age_hours = max_age_hours

    async def crawl_feed(self, source_info: Dict[str, str]) -> List[News]:
        source_name = source_info["name"]
        feed_url = source_info["url"]
        collected: List[News] = []

        try:
            content = await http_client.get_text(feed_url)
            parsed = feedparser.parse(content)

            for entry in parsed.entries:
                article_url = entry.get("link")
                title = entry.get("title")
                if not article_url or not title:
                    continue

                if not deduplicator.mark_seen(article_url):
                    continue

                # Extract and validate date
                raw_date = entry.get("published") or entry.get("updated")
                dt, method = date_extractor.extract_date(raw_date)

                # Strict 24h freshness constraint
                if not date_extractor.is_within_hours(dt, hours=self.max_age_hours):
                    continue

                summary = entry.get("summary") or entry.get("description") or title

                news_item = News(
                    title=title.strip(),
                    article_url=article_url.strip(),
                    source_url=feed_url,
                    source_name=source_name,
                    published_at=dt,
                    date_method=method,
                    summary=summary.strip(),
                    mentioned_entities=["Artificial Intelligence"],
                    raw_extracted_text=f"{title}\n{summary}\nPublished: {raw_date}",
                )
                collected.append(news_item)
                db_manager.save_news(news_item)

        except Exception as e:
            logger.warning(f"Error crawling news source '{source_name}': {e}")

        return collected

    async def run(self) -> List[News]:
        logger.info(f"Starting News crawl across {len(NEWS_SOURCES)} distinct sources (100% <= {self.max_age_hours}h)...")
        results: List[News] = []
        sources_used = 0

        for source in NEWS_SOURCES:
            items = await self.crawl_feed(source)
            if items:
                sources_used += 1
                results.extend(items)
                logger.info(f"Source '{source['name']}': Collected {len(items)} items within 24h.")
            else:
                logger.warning(f"Source '{source['name']}': 0 items within 24h.")

        logger.info(f"News crawl complete. Total collected: {len(results)} across {sources_used} sources.")
        return results


news_crawler = NewsCrawler()
