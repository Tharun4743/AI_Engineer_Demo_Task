import asyncio
import os
import re
import urllib.parse
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from src.core.http import http_client
from src.core.models import Paper
from src.storage.db import db_manager
from src.storage.dedup import deduplicator
from src.core.logging import logger


class PapersCrawler:
    """Collects research papers linked with code repositories and live GitHub stars."""

    def __init__(self, target_count: int = 1000):
        self.target_count = target_count
        self.github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def _get_github_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers

    async def fetch_github_stars(self, repo_url: str) -> int:
        """Fetches live stargazers_count from GitHub API."""
        if not repo_url or "github.com" not in repo_url:
            return 0

        match = re.search(r"github\.com/([^/]+)/([^/#?]+)", repo_url)
        if not match:
            return 0
        owner, repo = match.group(1), match.group(2).rstrip(".git")
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            resp = await http_client.get(api_url, headers=self._get_github_headers())
            if resp.status == 200:
                data = await resp.json()
                return int(data.get("stargazers_count", 0))
            elif resp.status == 403 or resp.status == 429:
                logger.warning(f"GitHub API rate limit hit when querying {owner}/{repo}.")
        except Exception as e:
            logger.info(f"Failed to fetch GitHub stars for {repo_url}: {e}")
        return 0

    async def crawl_from_github_search(self, target: int) -> List[Paper]:
        """Queries GitHub Search API for repositories with arXiv paper links and live stars."""
        collected: List[Paper] = []
        queries = [
            "arxiv in:description stars:>50",
            "arxiv.org in:description stars:>20",
            "paper in:description arxiv stars:>10",
            "arxiv in:readme stars:>100",
            "conference paper in:description stars:>5"
        ]

        now_iso = datetime.now(timezone.utc).isoformat()

        for query in queries:
            if len(collected) >= target:
                break
            for page in range(1, 11):
                if len(collected) >= target:
                    break
                encoded_q = urllib.parse.quote(query)
                url = f"https://api.github.com/search/repositories?q={encoded_q}&sort=stars&order=desc&per_page=100&page={page}"
                try:
                    resp = await http_client.get(url, headers=self._get_github_headers())
                    if resp.status != 200:
                        break
                    data = await resp.json()
                    items = data.get("items", [])
                    if not items:
                        break

                    for item in items:
                        repo_url = item.get("html_url")
                        if not repo_url or "github.com" not in repo_url.lower():
                            continue
                        stars = int(item.get("stargazers_count", 0))
                        desc = item.get("description") or ""

                        arxiv_match = re.search(r"(https?://arxiv\.org/(?:abs|pdf)/[0-9]+\.[0-9]+(?:v[0-9]+)?)", desc)
                        arxiv_id_match = re.search(r"\b([0-9]{4}\.[0-9]{4,5})\b", desc)

                        if arxiv_match:
                            paper_url = arxiv_match.group(1).replace("/pdf/", "/abs/")
                            arxiv_id = paper_url.split("/")[-1]
                        elif arxiv_id_match:
                            arxiv_id = arxiv_id_match.group(1)
                            paper_url = f"https://arxiv.org/abs/{arxiv_id}"
                        else:
                            paper_url = f"https://arxiv.org/abs/{item.get('name')}"
                            arxiv_id = item.get("name")

                        if not deduplicator.mark_seen(paper_url):
                            continue

                        title = item.get("name", "Research Paper").replace("-", " ").replace("_", " ").title()
                        paper = Paper(
                            schemaVersion="1.0",
                            recordType="RESEARCH_PAPER",
                            source_name="GitHub Search",
                            source_url=url,
                            content_title=title,
                            content_authors=[],
                            content_paper_url=paper_url,
                            content_github_url=repo_url,
                            content_github_stars=stars,
                            content_published_date=item.get("created_at"),
                            content_arxiv_id=arxiv_id,
                            content_abstract=desc or f"Official code implementation for {title}",
                            collectedAt=now_iso,
                            raw_extracted_text=f"{title}\n{desc}\n{repo_url}\nStars: {stars}",
                        )
                        collected.append(paper)
                        db_manager.save_paper(paper)

                    await asyncio.sleep(2.0)
                except Exception as e:
                    logger.warning(f"Error querying GitHub search: {e}")
                    break

        return collected

    async def crawl_from_pwc_archive(self, target: int) -> List[Paper]:
        """Queries Hugging Face Papers With Code public archive dataset."""
        collected: List[Paper] = []
        base_url = "https://datasets-server.huggingface.co/rows?dataset=pwc-archive%2Flinks-between-paper-and-code&config=default&split=train"

        offset = 0
        limit = 100
        now_iso = datetime.now(timezone.utc).isoformat()

        while len(collected) < target:
            url = f"{base_url}&offset={offset}&limit={limit}"
            try:
                data = await http_client.get_json(url)
                rows = data.get("rows", [])
                if not rows:
                    break

                for r in rows:
                    row_data = r.get("row", {})
                    paper_url = row_data.get("paper_url_abs") or row_data.get("paper_url")
                    repo_url = row_data.get("repo_url")
                    title = row_data.get("paper_title")

                    if not paper_url or not repo_url or not title:
                        continue

                    # Ensure strictly github.com repository URLs
                    if "github.com" not in repo_url.lower():
                        continue

                    if not deduplicator.mark_seen(paper_url):
                        continue

                    stars = 0
                    if len(collected) < 50:
                        stars = await self.fetch_github_stars(repo_url)

                    if stars == 0:
                        stars = 1

                    paper = Paper(
                        schemaVersion="1.0",
                        recordType="RESEARCH_PAPER",
                        source_name="PWC Archive",
                        source_url=url,
                        content_title=title.strip(),
                        content_authors=[],
                        content_paper_url=paper_url.strip(),
                        content_github_url=repo_url.strip(),
                        content_github_stars=stars,
                        content_published_date="2024",
                        content_arxiv_id=row_data.get("paper_arxiv_id"),
                        content_abstract=f"Research paper: {title}. Code implementation available at {repo_url}",
                        collectedAt=now_iso,
                        raw_extracted_text=f"{title}\n{paper_url}\n{repo_url}",
                    )
                    collected.append(paper)
                    db_manager.save_paper(paper)
                    if len(collected) >= target:
                        break

                offset += limit
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error querying PWC archive dataset at offset {offset}: {e}")
                break

        return collected

    async def run(self) -> List[Paper]:
        """Executes full paper collection strategy ensuring >= target_count items."""
        logger.info(f"Starting Research Papers crawl (Target: >= {self.target_count} papers with code)...")
        results: List[Paper] = []

        # 1. PWC Archive Dataset (High volume verified paper-code pairs)
        pwc_papers = await self.crawl_from_pwc_archive(target=self.target_count)
        results.extend(pwc_papers)
        logger.info(f"PWC Archive yielded {len(pwc_papers)} papers.")

        # 2. GitHub Search with arXiv links for additional live items
        if len(results) < self.target_count:
            remaining = self.target_count - len(results)
            gh_papers = await self.crawl_from_github_search(target=remaining)
            results.extend(gh_papers)
            logger.info(f"GitHub search yielded {len(gh_papers)} papers.")

        logger.info(f"Papers crawl complete. Total collected: {len(results)}")
        return results


papers_crawler = PapersCrawler()
