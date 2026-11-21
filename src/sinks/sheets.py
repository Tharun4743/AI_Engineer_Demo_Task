import os
import csv
from typing import List, Dict, Any, Optional
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
from src.core.logging import logger

try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

SHEET_TAB_NAMES = [
    "Startups",
    "Products",
    "Research Papers",
    "Jobs",
    "News",
    "Entity Mapping Log",
]


class SheetsExporter:
    """Exports pipeline data to Google Sheets (6 required tabs) and local CSV backup files."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.sa_json_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.sheet_id = os.environ.get("GOOGLE_SHEET_ID")

    def export_csv_backups(self) -> Dict[str, str]:
        """Dumps all 6 database tables to CSV backup files."""
        session: Session = db_manager.Session()
        exported_files: Dict[str, str] = {}

        try:
            # 1. Startups
            startups_path = os.path.join(self.output_dir, "startups.csv")
            startups = session.query(StartupModel).all()
            with open(startups_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["canonical_name", "legal_name", "domain", "website", "source_url", "description", "batch", "status", "country", "year_founded", "tags"])
                for s in startups:
                    writer.writerow([s.canonical_name, s.legal_name, s.domain, s.website, s.source_url, s.description, s.batch, s.status, s.country, s.year_founded, s.tags])
            exported_files["Startups"] = startups_path

            # 2. Products
            products_path = os.path.join(self.output_dir, "products.csv")
            products = session.query(ProductModel).all()
            with open(products_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "canonical_name", "product_url", "source_url", "description", "category", "stars_or_likes", "created_date"])
                for p in products:
                    writer.writerow([p.name, p.canonical_name, p.product_url, p.source_url, p.description, p.category, p.stars_or_likes, p.created_date])
            exported_files["Products"] = products_path

            # 3. Research Papers
            papers_path = os.path.join(self.output_dir, "research_papers.csv")
            papers = session.query(PaperModel).all()
            with open(papers_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["title", "paper_url", "source_url", "arxiv_id", "published_date", "abstract", "github_url", "github_stars"])
                for p in papers:
                    writer.writerow([p.title, p.paper_url, p.source_url, p.arxiv_id, p.published_date, p.abstract, p.github_url, p.github_stars])
            exported_files["Research Papers"] = papers_path

            # 4. Jobs
            jobs_path = os.path.join(self.output_dir, "jobs.csv")
            jobs = session.query(JobModel).all()
            with open(jobs_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["title", "company_name", "canonical_name", "job_url", "source_url", "location", "salary_range", "published_at", "date_method", "source_name"])
                for j in jobs:
                    writer.writerow([j.title, j.company_name, j.canonical_name, j.job_url, j.source_url, j.location, j.salary_range, j.published_at.isoformat() if j.published_at else "", j.date_method, j.source_name])
            exported_files["Jobs"] = jobs_path

            # 5. News
            news_path = os.path.join(self.output_dir, "news.csv")
            news_items = session.query(NewsModel).all()
            with open(news_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["title", "article_url", "source_url", "source_name", "published_at", "date_method", "summary", "mentioned_entities"])
                for n in news_items:
                    writer.writerow([n.title, n.article_url, n.source_url, n.source_name, n.published_at.isoformat() if n.published_at else "", n.date_method, n.summary, n.mentioned_entities])
            exported_files["News"] = news_path

            # 6. Entity Mapping Log
            log_path = os.path.join(self.output_dir, "entity_mapping_log.csv")
            mapping_logs = session.query(EntityMappingLogModel).all()
            with open(log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["raw_name", "canonical_name", "method", "score", "source_url"])
                for m in mapping_logs:
                    writer.writerow([m.raw_name, m.canonical_name, m.method, m.score, m.source_url])
            exported_files["Entity Mapping Log"] = log_path

            logger.info("CSV backup export completed successfully for all 6 tables.")
        finally:
            session.close()

        return exported_files

    def export_to_google_sheets(self) -> Optional[str]:
        """Exports data to Google Sheets with 6 required tabs and sets sharing to public view."""
        if not HAS_GSPREAD:
            logger.warning("gspread library is not installed. Skipping Google Sheets export.")
            return None

        if not self.sa_json_path or not os.path.exists(self.sa_json_path):
            logger.warning(
                "GOOGLE_SERVICE_ACCOUNT_JSON not provided or file not found. "
                "Google Sheets sync skipped; CSV files generated in output/."
            )
            return None

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        try:
            creds = Credentials.from_service_account_file(self.sa_json_path, scopes=scopes)
            client = gspread.authorize(creds)

            # Open existing spreadsheet or create a new public one
            if self.sheet_id:
                spreadsheet = client.open_by_key(self.sheet_id)
                logger.info(f"Opened existing Google Sheet: {spreadsheet.url}")
            else:
                spreadsheet = client.create("AI Competitive Intelligence Dashboard")
                logger.info(f"Created new Google Sheet: {spreadsheet.url}")
                # Make public view
                spreadsheet.share(None, perm_type="anyone", role="reader")
                logger.info("Configured Google Sheet permissions: Anyone with the link can view.")

            session: Session = db_manager.Session()
            try:
                # Setup 6 required tabs in exact order
                for tab_name in SHEET_TAB_NAMES:
                    try:
                        worksheet = spreadsheet.worksheet(tab_name)
                    except gspread.WorksheetNotFound:
                        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1500, cols=20)

                    # Populate tab
                    rows_data = self._get_tab_rows(tab_name, session)
                    if rows_data:
                        worksheet.clear()
                        worksheet.update("A1", rows_data)
                        logger.info(f"Updated tab '{tab_name}' with {len(rows_data)-1} data rows.")

                # Remove default 'Sheet1' if present
                try:
                    default_sheet = spreadsheet.worksheet("Sheet1")
                    if len(spreadsheet.worksheets()) > 1:
                        spreadsheet.del_worksheet(default_sheet)
                except Exception:
                    pass

                return spreadsheet.url

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {e}")
            return None

    def _get_tab_rows(self, tab_name: str, session: Session) -> List[List[Any]]:
        if tab_name == "Startups":
            header = ["canonical_name", "legal_name", "domain", "website", "source_url", "description", "batch", "status", "country", "year_founded", "tags"]
            rows = [header]
            for s in session.query(StartupModel).all():
                rows.append([s.canonical_name, s.legal_name or "", s.domain or "", s.website, s.source_url, s.description or "", s.batch or "", s.status or "", s.country or "", s.year_founded or "", s.tags or ""])
            return rows

        elif tab_name == "Products":
            header = ["name", "canonical_name", "product_url", "source_url", "description", "category", "stars_or_likes", "created_date"]
            rows = [header]
            for p in session.query(ProductModel).all():
                rows.append([p.name, p.canonical_name or "", p.product_url, p.source_url, p.description or "", p.category or "", p.stars_or_likes or 0, p.created_date or ""])
            return rows

        elif tab_name == "Research Papers":
            header = ["title", "paper_url", "source_url", "arxiv_id", "published_date", "abstract", "github_url", "github_stars"]
            rows = [header]
            for p in session.query(PaperModel).all():
                rows.append([p.title, p.paper_url, p.source_url, p.arxiv_id or "", p.published_date or "", p.abstract or "", p.github_url, p.github_stars])
            return rows

        elif tab_name == "Jobs":
            header = ["title", "company_name", "canonical_name", "job_url", "source_url", "location", "salary_range", "published_at", "date_method", "source_name"]
            rows = [header]
            for j in session.query(JobModel).all():
                rows.append([j.title, j.company_name, j.canonical_name or "", j.job_url, j.source_url, j.location or "", j.salary_range or "", j.published_at.isoformat() if j.published_at else "", j.date_method, j.source_name])
            return rows

        elif tab_name == "News":
            header = ["title", "article_url", "source_url", "source_name", "published_at", "date_method", "summary", "mentioned_entities"]
            rows = [header]
            for n in session.query(NewsModel).all():
                rows.append([n.title, n.article_url, n.source_url, n.source_name, n.published_at.isoformat() if n.published_at else "", n.date_method, n.summary or "", n.mentioned_entities or ""])
            return rows

        elif tab_name == "Entity Mapping Log":
            header = ["raw_name", "canonical_name", "method", "score", "source_url"]
            rows = [header]
            for m in session.query(EntityMappingLogModel).all():
                rows.append([m.raw_name, m.canonical_name, m.method, m.score, m.source_url])
            return rows

        return []


sheets_exporter = SheetsExporter()
