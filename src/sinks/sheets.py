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
        """Dumps all 6 database tables to CSV backup files after pruning expired temporal records."""
        # Prune expired temporal records (>24h) prior to export
        db_manager.prune_expired_temporal_records(max_age_hours=24)

        session: Session = db_manager.Session()
        exported_files: Dict[str, str] = {}

        try:
            # 1. Startups
            startups_path = os.path.join(self.output_dir, "startups.csv")
            startups = session.query(StartupModel).all()
            with open(startups_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["schemaVersion", "recordType", "source_name", "source_url",
                                 "content_entityName", "content_description", "content_data_employeeCount",
                                 "content_batch", "content_status", "content_country", "content_yearFounded",
                                 "content_tags", "content_website", "content_domain", "content_legalName", "collectedAt"])
                for s in startups:
                    writer.writerow([s.schemaVersion, s.recordType, s.source_name, s.source_url,
                                     s.content_entityName, s.content_description, s.content_data_employeeCount,
                                     s.content_batch, s.content_status, s.content_country, s.content_yearFounded,
                                     s.content_tags, s.content_website, s.content_domain, s.content_legalName, s.collectedAt])
            exported_files["Startups"] = startups_path

            # 2. Products
            products_path = os.path.join(self.output_dir, "products.csv")
            products = session.query(ProductModel).all()
            with open(products_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["schemaVersion", "recordType", "source_name", "source_url",
                                 "content_productName", "content_startupName", "content_pricingModel",
                                 "content_description", "content_category", "content_stars_or_likes",
                                 "content_productUrl", "content_createdDate", "collectedAt"])
                for p in products:
                    writer.writerow([p.schemaVersion, p.recordType, p.source_name, p.source_url,
                                     p.content_productName, p.content_startupName, p.content_pricingModel,
                                     p.content_description, p.content_category, p.content_stars_or_likes,
                                     p.content_productUrl, p.content_createdDate, p.collectedAt])
            exported_files["Products"] = products_path

            # 3. Research Papers
            papers_path = os.path.join(self.output_dir, "research_papers.csv")
            papers = session.query(PaperModel).all()
            with open(papers_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["schemaVersion", "recordType", "source_name", "source_url",
                                 "content_title", "content_authors", "content_paper_url",
                                 "content_github_url", "content_github_stars", "content_published_date",
                                 "content_arxiv_id", "collectedAt"])
                for p in papers:
                    writer.writerow([p.schemaVersion, p.recordType, p.source_name, p.source_url,
                                     p.content_title, p.content_authors, p.content_paper_url,
                                     p.content_github_url, p.content_github_stars, p.content_published_date,
                                     p.content_arxiv_id, p.collectedAt])
            exported_files["Research Papers"] = papers_path

            # 4. Jobs
            jobs_path = os.path.join(self.output_dir, "jobs.csv")
            jobs = session.query(JobModel).all()
            with open(jobs_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["schemaVersion", "recordType", "source_name", "source_url",
                                 "content_title", "content_company", "content_date",
                                 "content_is_remote", "content_role_family", "content_location",
                                 "content_salary_range", "content_jobUrl", "date_method", "collectedAt"])
                for j in jobs:
                    writer.writerow([j.schemaVersion, j.recordType, j.source_name, j.source_url,
                                     j.content_title, j.content_company, j.content_date,
                                     j.content_is_remote, j.content_role_family, j.content_location,
                                     j.content_salary_range, j.content_jobUrl, j.date_method, j.collectedAt])
            exported_files["Jobs"] = jobs_path

            # 5. News
            news_path = os.path.join(self.output_dir, "news.csv")
            news_items = session.query(NewsModel).all()
            with open(news_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["schemaVersion", "recordType", "source_name", "source_url",
                                 "content_title", "content_articleUrl", "content_publishedAt",
                                 "content_summary", "content_mentionedEntities", "date_method", "collectedAt"])
                for n in news_items:
                    writer.writerow([n.schemaVersion, n.recordType, n.source_name, n.source_url,
                                     n.content_title, n.content_articleUrl, n.content_publishedAt,
                                     n.content_summary, n.content_mentionedEntities, n.date_method, n.collectedAt])
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

            if self.sheet_id:
                spreadsheet = client.open_by_key(self.sheet_id)
                logger.info(f"Opened existing Google Sheet: {spreadsheet.url}")
            else:
                spreadsheet = client.create("AI Competitive Intelligence Dashboard")
                logger.info(f"Created new Google Sheet: {spreadsheet.url}")
                spreadsheet.share(None, perm_type="anyone", role="reader")
                logger.info("Configured Google Sheet permissions: Anyone with the link can view.")

            session: Session = db_manager.Session()
            try:
                for tab_name in SHEET_TAB_NAMES:
                    try:
                        worksheet = spreadsheet.worksheet(tab_name)
                    except gspread.WorksheetNotFound:
                        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1500, cols=20)

                    rows_data = self._get_tab_rows(tab_name, session)
                    if rows_data:
                        worksheet.clear()
                        worksheet.update("A1", rows_data)
                        logger.info(f"Updated tab '{tab_name}' with {len(rows_data)-1} data rows.")

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
            header = ["schemaVersion", "recordType", "source_name", "source_url",
                       "content_entityName", "content_description", "content_data_employeeCount",
                       "content_batch", "content_status", "content_country", "content_yearFounded",
                       "content_tags", "content_website", "content_domain", "content_legalName", "collectedAt"]
            rows = [header]
            for s in session.query(StartupModel).all():
                rows.append([s.schemaVersion or "", s.recordType or "", s.source_name or "", s.source_url or "",
                             s.content_entityName or "", s.content_description or "",
                             s.content_data_employeeCount or "", s.content_batch or "",
                             s.content_status or "", s.content_country or "", s.content_yearFounded or "",
                             s.content_tags or "", s.content_website or "", s.content_domain or "",
                             s.content_legalName or "", s.collectedAt or ""])
            return rows

        elif tab_name == "Products":
            header = ["schemaVersion", "recordType", "source_name", "source_url",
                       "content_productName", "content_startupName", "content_pricingModel",
                       "content_description", "content_category", "content_stars_or_likes",
                       "content_productUrl", "content_createdDate", "collectedAt"]
            rows = [header]
            for p in session.query(ProductModel).all():
                rows.append([p.schemaVersion or "", p.recordType or "", p.source_name or "", p.source_url or "",
                             p.content_productName or "", p.content_startupName or "",
                             p.content_pricingModel or "", p.content_description or "",
                             p.content_category or "", p.content_stars_or_likes or 0,
                             p.content_productUrl or "", p.content_createdDate or "", p.collectedAt or ""])
            return rows

        elif tab_name == "Research Papers":
            header = ["schemaVersion", "recordType", "source_name", "source_url",
                       "content_title", "content_authors", "content_paper_url",
                       "content_github_url", "content_github_stars", "content_published_date",
                       "content_arxiv_id", "collectedAt"]
            rows = [header]
            for p in session.query(PaperModel).all():
                rows.append([p.schemaVersion or "", p.recordType or "", p.source_name or "", p.source_url or "",
                             p.content_title or "", p.content_authors or "", p.content_paper_url or "",
                             p.content_github_url or "", p.content_github_stars or 0,
                             p.content_published_date or "", p.content_arxiv_id or "", p.collectedAt or ""])
            return rows

        elif tab_name == "Jobs":
            header = ["schemaVersion", "recordType", "source_name", "source_url",
                       "content_title", "content_company", "content_date",
                       "content_is_remote", "content_role_family", "content_location",
                       "content_salary_range", "content_jobUrl", "date_method", "collectedAt"]
            rows = [header]
            for j in session.query(JobModel).all():
                rows.append([j.schemaVersion or "", j.recordType or "", j.source_name or "", j.source_url or "",
                             j.content_title or "", j.content_company or "", j.content_date or "",
                             str(j.content_is_remote), j.content_role_family or "", j.content_location or "",
                             j.content_salary_range or "", j.content_jobUrl or "", j.date_method or "",
                             j.collectedAt or ""])
            return rows

        elif tab_name == "News":
            header = ["schemaVersion", "recordType", "source_name", "source_url",
                       "content_title", "content_articleUrl", "content_publishedAt",
                       "content_summary", "content_mentionedEntities", "date_method", "collectedAt"]
            rows = [header]
            for n in session.query(NewsModel).all():
                rows.append([n.schemaVersion or "", n.recordType or "", n.source_name or "", n.source_url or "",
                             n.content_title or "", n.content_articleUrl or "", n.content_publishedAt or "",
                             n.content_summary or "", n.content_mentionedEntities or "", n.date_method or "",
                             n.collectedAt or ""])
            return rows

        elif tab_name == "Entity Mapping Log":
            header = ["raw_name", "canonical_name", "method", "score", "source_url"]
            rows = [header]
            for m in session.query(EntityMappingLogModel).all():
                rows.append([m.raw_name, m.canonical_name, m.method, m.score, m.source_url])
            return rows

        return []


sheets_exporter = SheetsExporter()
