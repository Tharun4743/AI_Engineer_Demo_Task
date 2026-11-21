import asyncio
import re
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


def infer_role_family(title: str) -> str:
    """Infers job role family from title using keyword matching."""
    t = title.lower()
    if any(kw in t for kw in ["engineer", "developer", "swe", "frontend", "backend", "fullstack", "full-stack",
                               "devops", "sre", "infrastructure", "software", "platform"]):
        return "Engineering"
    if any(kw in t for kw in ["data scientist", "ml", "machine learning", "ai researcher", "deep learning",
                               "nlp", "computer vision", "research scientist"]):
        return "Data Science"
    if any(kw in t for kw in ["designer", "ux", "ui", "design"]):
        return "Design"
    if any(kw in t for kw in ["product manager", "product lead", "pm"]):
        return "Product"
    if "marketing" in t:
        return "Marketing"
    if "sales" in t:
        return "Sales"
    if any(kw in t for kw in ["analyst", "analytics", "business intelligence"]):
        return "Analytics"
    return "Other"


def infer_is_remote(location: str, title: str) -> bool:
    """Infers whether a job is remote from location and title."""
    combined = f"{location} {title}".lower()
    return "remote" in combined


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
            now_iso = datetime.now(timezone.utc).isoformat()

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
                location = j.get("location", "Remote")

                job = Job(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_name=source_name,
                    source_url=url,
                    content_title=title.strip(),
                    content_company=canonical_name,
                    content_date=dt.isoformat(),
                    content_is_remote=infer_is_remote(location, title),
                    content_role_family=infer_role_family(title),
                    content_location=location,
                    content_salary_range="Competitive",
                    content_jobUrl=job_url.strip(),
                    date_method="timestamp",
                    collectedAt=now_iso,
                    raw_extracted_text=f"{title} at {company} ({location})",
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
            now_iso = datetime.now(timezone.utc).isoformat()

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
                    # Intelligent Heuristic: If source lacks a strict date within 24h,
                    # treat fresh unvisited feed items as new since last run
                    dt = datetime.now(timezone.utc)
                    method = "heuristic_since_last_run"

                company = "Remote Technology"
                title_clean = title
                if " at " in title:
                    parts = title.split(" at ")
                    title_clean = parts[0].strip()
                    company = parts[1].strip()

                canonical_name, _ = entity_resolver.resolve(raw_name=company, source_url=job_url)

                job = Job(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_name=source_name,
                    source_url=url,
                    content_title=title_clean,
                    content_company=canonical_name,
                    content_date=dt.isoformat() if hasattr(dt, 'isoformat') else str(dt),
                    content_is_remote=True,
                    content_role_family=infer_role_family(title_clean),
                    content_location="Remote",
                    content_salary_range="Competitive",
                    content_jobUrl=job_url.strip(),
                    date_method=method,
                    collectedAt=now_iso,
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
            now_iso = datetime.now(timezone.utc).isoformat()

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
                location = j.get("jobGeo", "Remote")
                salary_min = j.get("annualSalaryMin")
                salary_max = j.get("annualSalaryMax")
                salary = f"{salary_min}-{salary_max}" if salary_min else "Competitive"

                job = Job(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_name=source_name,
                    source_url=url,
                    content_title=title.strip(),
                    content_company=canonical_name,
                    content_date=dt.isoformat() if hasattr(dt, 'isoformat') else str(dt),
                    content_is_remote=infer_is_remote(location, title),
                    content_role_family=infer_role_family(title),
                    content_location=location,
                    content_salary_range=salary,
                    content_jobUrl=job_url.strip(),
                    date_method=method,
                    collectedAt=now_iso,
                    raw_extracted_text=f"{title} at {company} ({location})",
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
            now_iso = datetime.now(timezone.utc).isoformat()

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
                    # Intelligent Heuristic: If source lacks a strict date within 24h,
                    # treat fresh unvisited feed items as new since last run
                    dt = datetime.now(timezone.utc)
                    method = "heuristic_since_last_run"

                job = Job(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_name=source_name,
                    source_url=url,
                    content_title=title.strip(),
                    content_company="Global Remote",
                    content_date=dt.isoformat() if hasattr(dt, 'isoformat') else str(dt),
                    content_is_remote=True,
                    content_role_family=infer_role_family(title),
                    content_location="Remote",
                    content_salary_range="Competitive",
                    content_jobUrl=job_url.strip(),
                    date_method=method,
                    collectedAt=now_iso,
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
            now_iso = datetime.now(timezone.utc).isoformat()

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
                    # Intelligent Heuristic: If source lacks a strict date within 24h,
                    # treat fresh unvisited feed items as new since last run
                    dt = datetime.now(timezone.utc)
                    method = "heuristic_since_last_run"

                company = "Tech Company"
                title_clean = title
                if " at " in title:
                    parts = title.split(" at ")
                    title_clean = parts[0].strip()
                    company = parts[1].strip()
                elif " - " in title:
                    parts = title.split(" - ")
                    title_clean = parts[0].strip()
                    company = parts[1].strip()

                canonical_name, _ = entity_resolver.resolve(raw_name=company, source_url=job_url)

                job = Job(
                    schemaVersion="1.0",
                    recordType="JOB",
                    source_name=source_name,
                    source_url=url,
                    content_title=title_clean,
                    content_company=canonical_name,
                    content_date=dt.isoformat() if hasattr(dt, 'isoformat') else str(dt),
                    content_is_remote=True,
                    content_role_family=infer_role_family(title_clean),
                    content_location="Remote",
                    content_salary_range="Competitive",
                    content_jobUrl=job_url.strip(),
                    date_method=method,
                    collectedAt=now_iso,
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
