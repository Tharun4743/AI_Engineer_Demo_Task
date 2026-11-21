import asyncio
import json
import os
from datetime import datetime, timezone
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

            now_iso = datetime.now(timezone.utc).isoformat()

            for item in seeds:
                website = f"https://{item['domain']}" if not item["domain"].startswith("http") else item["domain"]
                if not deduplicator.mark_seen(website):
                    continue

                canonical_name = item["canonical_name"]
                startup = Startup(
                    schemaVersion="1.0",
                    recordType="STARTUP",
                    source_name="Seed Entities",
                    source_url="config/seed_entities.json",
                    content_entityName=canonical_name,
                    content_description=f"{canonical_name} - Frontier Artificial Intelligence Company",
                    content_data_employeeCount=item.get("employee_count"),
                    content_batch="Seed",
                    content_status="Active",
                    content_country=item.get("country", "USA"),
                    content_yearFounded=item.get("year_founded"),
                    content_tags=["AI", "Frontier", "Machine Learning"],
                    content_website=website,
                    content_domain=item.get("domain"),
                    content_legalName=item["aliases"][0] if item.get("aliases") else canonical_name,
                    collectedAt=now_iso,
                    raw_extracted_text=f"{canonical_name} ({website}) founded in {item.get('year_founded')}",
                )
                collected.append(startup)
                db_manager.save_startup(startup)

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

            now_iso = datetime.now(timezone.utc).isoformat()

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

                team_size = item.get("teamSize")
                employee_count = None
                if team_size is not None:
                    try:
                        employee_count = int(team_size)
                    except (ValueError, TypeError):
                        employee_count = None

                startup = Startup(
                    schemaVersion="1.0",
                    recordType="STARTUP",
                    source_name="YC Directory",
                    source_url=YC_COMPANIES_URL,
                    content_entityName=canonical_name,
                    content_description=desc,
                    content_data_employeeCount=employee_count,
                    content_batch=item.get("batch"),
                    content_status=item.get("status", "Active"),
                    content_country=item.get("country"),
                    content_yearFounded=item.get("yearFounded"),
                    content_tags=tags,
                    content_website=website,
                    content_domain=entity_resolver._extract_domain(website),
                    content_legalName=name,
                    collectedAt=now_iso,
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
