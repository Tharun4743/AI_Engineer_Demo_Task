import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
import feedparser
from src.core.http import http_client
from src.core.models import Job
from src.extraction.dates import date_extractor
from src.resolver.entity_resolver import entity_resolver
from src.storage.db import db_manager
from src.storage.dedup import deduplicator
from src.core.logging import logger


class JobsCrawler:
    """Collects tech and AI job postings across 5 distinct sources with strict 24h publication checks."""

    def __init__(self, max_age_hours: int = 24):
        self.max_age_hours = max_age_hours

    async def crawl_arbeitnow(self) -> List[Job]:
        """Source 1: Arbeitnow Jobs API."""
        url = "https://www.arbeitnow.com/api/job-board-api"
        source_name = "Arbeitnow"
        collected: List[Job] = []

        try:
            data = await http_client.get_json(url)
            jobs = data.get("data", [])
            for j in jobs:
                job_url = j.get("url")
                title = j.get("title")
                company = j.get("company_name", "Technology Company")
                if not job_url or not title:
                    continue

                if not deduplicator.mark_seen(job_url):
                    continue

                created_at = j.get("created_at")
                if not created_at:
                    continue

                dt = datetime.fromtimestamp(created_at, tz=timezone.utc)
                if not date_extractor.is_within_hours(dt, hours=self.max_age_hours):
                    continue

                canonical_name, _ = entity_resolver.resolve(raw_name=company, source_url=job_url)

                job = Job(
                    title=title.strip(),
                    company_name=company.strip(),
                    canonical_name=canonical_name,
                    job_url=job_url.strip(),
                    source_url=url,
                    location=j.get("location", "Remote"),
                    salary_range="Competitive",
                    published_at=dt,
                    date_method="timestamp",
                    source_name=source_name,
                    raw_extracted_text=f"{title} at {company} ({j.get('location')})",
                )
                collected.append(job)
                db_manager.save_job(job)

        except Exception as e:
            logger.warning(f"Error crawling {source_name}: {e}")

        return collected

    async def crawl_jobspresso(self) -> List[Job]:
        """Source 2: Jobspresso RSS."""
        url = "https://jobspresso.co/feed/?post_type=job_listing"
        source_name = "Jobspresso"
        collected: List[Job] = []

        try:
            content = await http_client.get_text(url)
            parsed = feedparser.parse(content)

            for entry in parsed.entries:
                job_url = entry.get("link")
                title = entry.get("title")
                if not job_url or not title:
                    continue

                if not deduplicator.mark_seen(job_url):
                    continue

                raw_date = entry.get("published")
                dt, method = date_extractor.extract_date(raw_date)

                if not date_extractor.is_within_hours(dt, hours=self.max_age_hours):
                    continue

                # Heuristic company extraction from title if formatted "Title at Company"
                company = "Remote Technology"
                if " at " in title:
                    parts = title.split(" at ")
                    title_clean = parts[0].strip()
                    company = parts[1].strip()
                else:
                    title_clean = title

                canonical_name, _ = entity_resolver.resolve(raw_name=company, source_url=job_url)

                job = Job(
                    title=title_clean,
                    company_name=company,
                    canonical_name=canonical_name,
                    job_url=job_url.strip(),
                    source_url=url,
                    location="Remote",
                    salary_range="Competitive",
                    published_at=dt,
                    date_method=method,
                    source_name=source_name,
                    raw_extracted_text=f"{title} ({job_url})",
                )
                collected.append(job)
                db_manager.save_job(job)

        except Exception as e:
            logger.warning(f"Error crawling {source_name}: {e}")

        return collected

    async def crawl_jobicy(self) -> List[Job]:
        """Source 3: Jobicy Remote Jobs API."""
        url = "https://jobicy.com/api/v2/remote-jobs?count=50"
        source_name = "Jobicy"
        collected: List[Job] = []

        try:
            data = await http_client.get_json(url)
            jobs = data.get("jobs", [])

            for j in jobs:
                job_url = j.get("url")
                title = j.get("jobTitle")
                company = j.get("companyName", "Tech Employer")
                if not job_url or not title:
                    continue

                if not deduplicator.mark_seen(job_url):
                    continue

                raw_date = j.get("pubDate")
                dt, method = date_extractor.extract_date(raw_date)

                if not date_extractor.is_within_hours(dt, hours=self.max_age_hours):
                    continue

                canonical_name, _ = entity_resolver.resolve(raw_name=company, source_url=job_url)

                job = Job(
                    title=title.strip(),
                    company_name=company.strip(),
                    canonical_name=canonical_name,
                    job_url=job_url.strip(),
                    source_url=url,
                    location=j.get("jobGeo", "Remote"),
                    salary_range=f"{j.get('annualSalaryMin', '')}-{j.get('annualSalaryMax', '')}" if j.get('annualSalaryMin') else "Competitive",
                    published_at=dt,
                    date_method=method,
                    source_name=source_name,
                    raw_extracted_text=f"{title} at {company} ({j.get('jobGeo')})",
                )
                collected.append(job)
                db_manager.save_job(job)

        except Exception as e:
            logger.warning(f"Error crawling {source_name}: {e}")

        return collected

    async def crawl_nodesk(self) -> List[Job]:
        """Source 4: NoDesk Remote Jobs Feed."""
        url = "https://nodesk.co/remote-jobs/index.xml"
        source_name = "NoDesk"
        collected: List[Job] = []

        try:
            content = await http_client.get_text(url)
            parsed = feedparser.parse(content)

            for entry in parsed.entries:
                job_url = entry.get("link")
                title = entry.get("title")
                if not job_url or not title:
                    continue

                if not deduplicator.mark_seen(job_url):
                    continue

                raw_date = entry.get("published")
                dt, method = date_extractor.extract_date(raw_date)

                if not date_extractor.is_within_hours(dt, hours=self.max_age_hours):
                    continue

                job = Job(
                    title=title.strip(),
                    company_name="Global Remote",
                    canonical_name="Global Remote",
                    job_url=job_url.strip(),
                    source_url=url,
                    location="Remote",
                    salary_range="Competitive",
                    published_at=dt,
                    date_method=method,
                    source_name=source_name,
                    raw_extracted_text=f"{title} ({job_url})",
                )
                collected.append(job)
                db_manager.save_job(job)

        except Exception as e:
            logger.warning(f"Error crawling {source_name}: {e}")

        return collected

    async def crawl_himalayas(self) -> List[Job]:
        """Source 5: Himalayas Remote Jobs RSS Feed."""
        url = "https://himalayas.app/jobs/rss"
        source_name = "Himalayas"
        collected: List[Job] = []

        try:
            content = await http_client.get_text(url)
            parsed = feedparser.parse(content)

            for entry in parsed.entries:
                job_url = entry.get("link")
                title = entry.get("title")
                if not job_url or not title:
                    continue

                if not deduplicator.mark_seen(job_url):
                    continue

                raw_date = entry.get("published")
                dt, method = date_extractor.extract_date(raw_date)

                if not date_extractor.is_within_hours(dt, hours=self.max_age_hours):
                    continue

                company = "Tech Company"
                if " at " in title:
                    parts = title.split(" at ")
                    title_clean = parts[0].strip()
                    company = parts[1].strip()
                elif " - " in title:
                    parts = title.split(" - ")
                    title_clean = parts[0].strip()
                    company = parts[1].strip()
                else:
                    title_clean = title

                canonical_name, _ = entity_resolver.resolve(raw_name=company, source_url=job_url)

                job = Job(
                    title=title_clean,
                    company_name=company,
                    canonical_name=canonical_name,
                    job_url=job_url.strip(),
                    source_url=url,
                    location="Remote",
                    salary_range="Competitive",
                    published_at=dt,
                    date_method=method,
                    source_name=source_name,
                    raw_extracted_text=f"{title} ({job_url})",
                )
                collected.append(job)
                db_manager.save_job(job)

        except Exception as e:
            logger.warning(f"Error crawling {source_name}: {e}")

        return collected

    async def run(self) -> List[Job]:
        logger.info(f"Starting Jobs crawl across 5 distinct sources (100% <= {self.max_age_hours}h)...")
        results: List[Job] = []

        sources = [
            self.crawl_arbeitnow(),
            self.crawl_jobspresso(),
            self.crawl_jobicy(),
            self.crawl_nodesk(),
            self.crawl_himalayas(),
        ]

        batch_results = await asyncio.gather(*sources, return_exceptions=True)
        active_sources = 0

        for r in batch_results:
            if isinstance(r, list) and r:
                active_sources += 1
                results.extend(r)

        logger.info(f"Jobs crawl complete. Total collected: {len(results)} across {active_sources} active sources.")
        return results


jobs_crawler = JobsCrawler()
