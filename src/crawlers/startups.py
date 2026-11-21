import asyncio
import json
import os
from typing import List, Optional
from src.core.http import http_client
from src.core.models import Startup, EntityMappingLog
from src.resolver.entity_resolver import entity_resolver
from src.storage.db import db_manager
from src.storage.dedup import deduplicator
from src.core.logging import logger

YC_COMPANIES_URL = "https://raw.githubusercontent.com/ArtificiallyLTD/open-business-datasets/main/yc-companies/yc-companies.json"


class StartupsCrawler:
    """Collects startup intelligence from Y Combinator directory and canonical seed entities."""

    def __init__(self, target_count: int = 1000):
        self.target_count = target_count

    async def crawl_seed_entities(self) -> List[Startup]:
        """Loads canonical seed entities first to establish ground truth."""
        collected: List[Startup] = []
        seed_path = "config/seed_entities.json"
        if not os.path.exists(seed_path):
            return collected

        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                seeds = json.load(f)

            for item in seeds:
                website = f"https://{item['domain']}" if not item["domain"].startswith("http") else item["domain"]
                if not deduplicator.mark_seen(website):
                    continue

                canonical_name = item["canonical_name"]
                startup = Startup(
                    canonical_name=canonical_name,
                    legal_name=item["aliases"][0] if item.get("aliases") else canonical_name,
                    domain=item.get("domain"),
                    website=website,
                    source_url="config/seed_entities.json",
                    description=f"{canonical_name} - Frontier Artificial Intelligence Company",
                    batch="Seed",
                    status="Active",
                    country=item.get("country", "USA"),
                    year_founded=item.get("year_founded"),
                    tags=["AI", "Frontier", "Machine Learning"],
                    raw_extracted_text=f"{canonical_name} ({website}) founded in {item.get('year_founded')}",
                )
                collected.append(startup)
                db_manager.save_startup(startup)

                # Log entity mapping
                mapping_log = EntityMappingLog(
                    raw_name=canonical_name,
                    canonical_name=canonical_name,
                    method="seed_ground_truth",
                    score=1.0,
                    source_url="config/seed_entities.json",
                )
                db_manager.save_mapping_log(mapping_log)

        except Exception as e:
            logger.error(f"Failed to crawl seed entities: {e}")

        return collected

    async def crawl_yc_companies(self, target: int) -> List[Startup]:
        """Crawls comprehensive YC company directory dataset."""
        collected: List[Startup] = []
        logger.info(f"Fetching YC companies dataset from {YC_COMPANIES_URL}...")

        try:
            data = await http_client.get_json(YC_COMPANIES_URL)
            if not isinstance(data, list):
                logger.error("YC dataset did not return a JSON array.")
                return collected

            for item in data:
                website = item.get("website")
                name = item.get("name")
                if not website or not name:
                    continue

                if not website.startswith("http"):
                    website = f"https://{website}"

                if not deduplicator.mark_seen(website):
                    continue

                canonical_name, map_log = entity_resolver.resolve(
                    raw_name=name,
                    website_or_url=website,
                    source_url=YC_COMPANIES_URL,
                )

                tags = item.get("tags") or []
                desc = item.get("oneLiner") or item.get("longDescription") or f"{name} technology company"

                startup = Startup(
                    canonical_name=canonical_name,
                    legal_name=name,
                    domain=entity_resolver._extract_domain(website),
                    website=website,
                    source_url=YC_COMPANIES_URL,
                    description=desc,
                    batch=item.get("batch"),
                    status=item.get("status", "Active"),
                    country=item.get("country"),
                    year_founded=item.get("yearFounded"),
                    tags=tags,
                    raw_extracted_text=f"{name} ({website}) - {desc}. Batch: {item.get('batch')}",
                )
                collected.append(startup)
                db_manager.save_startup(startup)
                db_manager.save_mapping_log(map_log)

                if len(collected) >= target:
                    break

        except Exception as e:
            logger.error(f"Error crawling YC companies: {e}")

        return collected

    async def run(self) -> List[Startup]:
        logger.info(f"Starting Startups crawl (Target: >= {self.target_count} unique startups)...")
        results: List[Startup] = []

        # 1. Ground truth seeds
        seeds = await self.crawl_seed_entities()
        results.extend(seeds)
        logger.info(f"Loaded {len(seeds)} seed entities.")

        # 2. YC Companies dataset
        remaining = max(0, self.target_count - len(results))
        yc_items = await self.crawl_yc_companies(target=remaining + 50)
        results.extend(yc_items)

        logger.info(f"Startups crawl complete. Total collected: {len(results)}")
        return results


startups_crawler = StartupsCrawler()
