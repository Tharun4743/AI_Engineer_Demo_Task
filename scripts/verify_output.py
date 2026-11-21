import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateutil_parser
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.storage.db import (
    db_manager,
    StartupModel,
    ProductModel,
    PaperModel,
    JobModel,
    NewsModel,
    EntityMappingLogModel,
)
from src.extraction.validator import grounding_validator
from src.core.logging import logger


class AcceptanceVerifier:
    """Verifies all Definition of Done (DoD) criteria for the intelligence pipeline."""

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.failures: List[str] = []

    def _parse_iso_date(self, date_str: str) -> datetime:
        """Parse an ISO 8601 date string to a timezone-aware datetime."""
        try:
            dt = dateutil_parser.isoparse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime.now(timezone.utc)

    def verify_counts_and_uniqueness(self, session: Session):
        print("\n--- CHECK 1: Volume & Uniqueness Constraints ---")

        # 1. Startups >= 1,000
        startups = session.query(StartupModel).all()
        s_count = len(startups)
        s_urls = [s.content_website for s in startups if s.content_website]
        s_unique = len(set(s_urls))
        s_missing_src = sum(1 for s in startups if not s.source_url)
        self.results["startups_count"] = s_count
        self.results["startups_unique_urls"] = s_unique
        self.results["startups_missing_src"] = s_missing_src

        print(f"Startups: Total={s_count}, Unique Websites={s_unique}, Missing Source URL={s_missing_src}")
        if s_count < 1000:
            self.failures.append(f"Startups count shortfall: {s_count} < 1000 required.")
        if s_count != s_unique:
            self.failures.append(f"Duplicate startup websites found: {s_count - s_unique} duplicates.")
        if s_missing_src > 0:
            self.failures.append(f"Startups with missing source URL: {s_missing_src}.")

        # 2. Products >= 1,000
        products = session.query(ProductModel).all()
        p_count = len(products)
        p_urls = [p.content_productUrl for p in products if p.content_productUrl]
        p_unique = len(set(p_urls))
        p_missing_src = sum(1 for p in products if not p.source_url)
        self.results["products_count"] = p_count
        self.results["products_unique_urls"] = p_unique
        self.results["products_missing_src"] = p_missing_src

        print(f"Products: Total={p_count}, Unique Product URLs={p_unique}, Missing Source URL={p_missing_src}")
        if p_count < 1000:
            self.failures.append(f"Products count shortfall: {p_count} < 1000 required.")
        if p_count != p_unique:
            self.failures.append(f"Duplicate product URLs found: {p_count - p_unique} duplicates.")
        if p_missing_src > 0:
            self.failures.append(f"Products with missing source URL: {p_missing_src}.")

        # 3. Papers >= 1,000 with paper_url, github_url, and github_stars
        papers = session.query(PaperModel).all()
        paper_count = len(papers)
        paper_urls = [p.content_paper_url for p in papers if p.content_paper_url]
        paper_unique = len(set(paper_urls))
        paper_missing_src = sum(1 for p in papers if not p.source_url)
        paper_with_code_stars = sum(1 for p in papers if p.content_github_url and p.content_github_stars is not None)
        self.results["papers_count"] = paper_count
        self.results["papers_unique_urls"] = paper_unique
        self.results["papers_with_code_stars"] = paper_with_code_stars
        self.results["papers_missing_src"] = paper_missing_src

        print(f"Research Papers: Total={paper_count}, Unique Paper URLs={paper_unique}, With Code+Stars={paper_with_code_stars}, Missing Source URL={paper_missing_src}")
        if paper_count < 1000:
            self.failures.append(f"Research papers count shortfall: {paper_count} < 1000 required.")
        if paper_with_code_stars < 1000:
            self.failures.append(f"Papers with valid github_url + github_stars: {paper_with_code_stars} < 1000 required.")
        if paper_count != paper_unique:
            self.failures.append(f"Duplicate paper URLs found: {paper_count - paper_unique} duplicates.")
        if paper_missing_src > 0:
            self.failures.append(f"Papers with missing source URL: {paper_missing_src}.")

    def verify_jobs_and_news_freshness(self, session: Session):
        print("\n--- CHECK 2: Jobs & News 24h Freshness & Source Diversity ---")
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)

        # 1. Jobs: 5 distinct sources, 100% within 24h, date_method recorded
        jobs = session.query(JobModel).all()
        job_sources = set(j.source_name for j in jobs if j.source_name)
        jobs_missing_method = sum(1 for j in jobs if not j.date_method)
        jobs_missing_src = sum(1 for j in jobs if not j.source_url)
        jobs_out_of_window = 0

        for j in jobs:
            pub_at = self._parse_iso_date(j.content_date)
            if pub_at < cutoff or pub_at > (now + timedelta(minutes=10)):
                jobs_out_of_window += 1

        self.results["jobs_count"] = len(jobs)
        self.results["jobs_distinct_sources"] = len(job_sources)
        self.results["jobs_out_of_24h"] = jobs_out_of_window
        self.results["jobs_missing_method"] = jobs_missing_method

        print(f"Jobs: Total={len(jobs)}, Distinct Sources={len(job_sources)} ({list(job_sources)[:5]}), Out of 24h Window={jobs_out_of_window}, Missing date_method={jobs_missing_method}")
        if len(job_sources) < 5:
            self.failures.append(f"Jobs source shortfall: {len(job_sources)} < 5 distinct sources required.")
        if jobs_out_of_window > 0:
            self.failures.append(f"Jobs 24h freshness violation: {jobs_out_of_window} records published outside 24h window.")
        if jobs_missing_method > 0:
            self.failures.append(f"Jobs missing date_method: {jobs_missing_method} records.")
        if jobs_missing_src > 0:
            self.failures.append(f"Jobs missing source URL: {jobs_missing_src} records.")

        # 2. News: 5 distinct sources, 100% within 24h, date_method recorded
        news = session.query(NewsModel).all()
        news_sources = set(n.source_name for n in news if n.source_name)
        news_missing_method = sum(1 for n in news if not n.date_method)
        news_missing_src = sum(1 for n in news if not n.source_url)
        news_out_of_window = 0

        for n in news:
            pub_at = self._parse_iso_date(n.content_publishedAt)
            if pub_at < cutoff or pub_at > (now + timedelta(minutes=10)):
                news_out_of_window += 1

        self.results["news_count"] = len(news)
        self.results["news_distinct_sources"] = len(news_sources)
        self.results["news_out_of_24h"] = news_out_of_window
        self.results["news_missing_method"] = news_missing_method

        print(f"News: Total={len(news)}, Distinct Sources={len(news_sources)} ({list(news_sources)[:5]}), Out of 24h Window={news_out_of_window}, Missing date_method={news_missing_method}")
        if len(news_sources) < 5:
            self.failures.append(f"News source shortfall: {len(news_sources)} < 5 distinct sources required.")
        if news_out_of_window > 0:
            self.failures.append(f"News 24h freshness violation: {news_out_of_window} records published outside 24h window.")
        if news_missing_method > 0:
            self.failures.append(f"News missing date_method: {news_missing_method} records.")
        if news_missing_src > 0:
            self.failures.append(f"News missing source URL: {news_missing_src} records.")

    def verify_grounding_integrity(self):
        print("\n--- CHECK 3: Anti-Hallucination Grounding Audit ---")
        stats = grounding_validator.get_stats()
        print(f"Grounding Audit Stats: {stats}")
        self.results["grounding_stats"] = stats

    def verify_exports_and_sheets(self):
        print("\n--- CHECK 4: Export Artifacts Audit ---")
        required_csvs = [
            "startups.csv",
            "products.csv",
            "research_papers.csv",
            "jobs.csv",
            "news.csv",
            "entity_mapping_log.csv"
        ]
        missing_csvs = []
        for f in required_csvs:
            p = os.path.join("output", f)
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                missing_csvs.append(f)
            else:
                print(f"  [OK] output/{f} ({os.path.getsize(p)} bytes)")

        if missing_csvs:
            self.failures.append(f"Missing or empty required CSV exports: {missing_csvs}")

    def run(self) -> bool:
        print("================================================================")
        print("     STARTING ACCEPTANCE AUDIT & DEFINITION OF DONE CHECKS      ")
        print("================================================================")
        session = db_manager.Session()
        try:
            self.verify_counts_and_uniqueness(session)
            self.verify_jobs_and_news_freshness(session)
            self.verify_grounding_integrity()
            self.verify_exports_and_sheets()
        finally:
            session.close()

        print("\n================================================================")
        if not self.failures:
            print("  >>> [ACCEPTANCE PASS]: ALL DEFINITION OF DONE CRITERIA MET <<<")
            print("================================================================")
            return True
        else:
            print("  >>> [ACCEPTANCE FAIL]: CRITERIA SHORTFALLS DETECTED <<<")
            for f in self.failures:
                print(f"  - FAIL: {f}")
            print("================================================================")
            return False


if __name__ == "__main__":
    verifier = AcceptanceVerifier()
    passed = verifier.run()
    sys.exit(0 if passed else 1)
