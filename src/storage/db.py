import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from dateutil import parser as dateutil_parser
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from src.core.logging import logger

Base = declarative_base()


class StartupModel(Base):
    __tablename__ = "startups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schemaVersion = Column(String(16), default="1.0")
    recordType = Column(String(32), default="STARTUP")
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=False)
    content_entityName = Column(String(255), nullable=False)
    content_description = Column(Text, nullable=True)
    content_data_employeeCount = Column(Integer, nullable=True)
    content_batch = Column(String(64), nullable=True)
    content_status = Column(String(64), default="Active")
    content_country = Column(String(64), nullable=True)
    content_yearFounded = Column(Integer, nullable=True)
    content_tags = Column(Text, nullable=True)
    content_website = Column(String(512), nullable=False, unique=True)
    content_domain = Column(String(255), nullable=True)
    content_legalName = Column(String(255), nullable=True)
    collectedAt = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("content_website", name="uq_startup_website"),
        Index("idx_startup_entity", "content_entityName"),
    )


class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schemaVersion = Column(String(16), default="1.0")
    recordType = Column(String(32), default="PRODUCT")
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=False)
    content_productName = Column(String(255), nullable=False)
    content_startupName = Column(String(255), nullable=True)
    content_pricingModel = Column(String(32), default="FREE")
    content_description = Column(Text, nullable=True)
    content_category = Column(String(128), nullable=True)
    content_stars_or_likes = Column(Integer, default=0)
    content_productUrl = Column(String(1024), nullable=False, unique=True)
    content_createdDate = Column(String(64), nullable=True)
    collectedAt = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("content_productUrl", name="uq_product_url"),
        Index("idx_product_name", "content_productName"),
    )


class PaperModel(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schemaVersion = Column(String(16), default="1.0")
    recordType = Column(String(32), default="RESEARCH_PAPER")
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=False)
    content_title = Column(String(512), nullable=False)
    content_authors = Column(Text, nullable=True)
    content_paper_url = Column(String(1024), nullable=False, unique=True)
    content_github_url = Column(String(1024), nullable=False)
    content_github_stars = Column(Integer, default=0, nullable=False)
    content_published_date = Column(String(64), nullable=True)
    content_arxiv_id = Column(String(64), nullable=True)
    content_abstract = Column(Text, nullable=True)
    collectedAt = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("content_paper_url", name="uq_paper_url"),
        Index("idx_paper_github", "content_github_url"),
    )


class JobModel(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schemaVersion = Column(String(16), default="1.0")
    recordType = Column(String(32), default="JOB")
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=False)
    content_title = Column(String(512), nullable=False)
    content_company = Column(String(255), nullable=False)
    content_date = Column(String(64), nullable=False)
    content_is_remote = Column(Boolean, default=False)
    content_role_family = Column(String(64), default="Engineering")
    content_location = Column(String(255), nullable=True)
    content_salary_range = Column(String(128), nullable=True)
    content_jobUrl = Column(String(1024), nullable=False, unique=True)
    date_method = Column(String(64), nullable=False)
    collectedAt = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("content_jobUrl", name="uq_job_url"),
        Index("idx_job_date", "content_date"),
    )


class NewsModel(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schemaVersion = Column(String(16), default="1.0")
    recordType = Column(String(32), default="NEWS")
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=False)
    content_title = Column(String(512), nullable=False)
    content_articleUrl = Column(String(1024), nullable=False, unique=True)
    content_publishedAt = Column(String(64), nullable=False)
    content_summary = Column(Text, nullable=True)
    content_mentionedEntities = Column(Text, nullable=True)
    date_method = Column(String(64), nullable=False)
    collectedAt = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("content_articleUrl", name="uq_news_article_url"),
        Index("idx_news_published", "content_publishedAt"),
    )


class EntityMappingLogModel(Base):
    __tablename__ = "entity_mapping_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    method = Column(String(64), nullable=False)
    score = Column(Float, default=1.0)
    source_url = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DatabaseManager:
    """Manages database connection and persistence operations."""

    def __init__(self, db_url: Optional[str] = None):
        if not db_url:
            db_url = os.environ.get("DATABASE_URL", "sqlite:///data/pipeline.db")
        if db_url.startswith("sqlite:///"):
            os.makedirs("data", exist_ok=True)
        self.engine = create_engine(db_url, echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        Base.metadata.create_all(self.engine)

    def save_startup(self, startup) -> bool:
        session = self.Session()
        try:
            tags_str = ",".join(startup.content_tags) if startup.content_tags else ""
            model = StartupModel(
                schemaVersion=startup.schemaVersion,
                recordType=startup.recordType,
                source_name=startup.source_name,
                source_url=startup.source_url,
                content_entityName=startup.content_entityName,
                content_description=startup.content_description,
                content_data_employeeCount=startup.content_data_employeeCount,
                content_batch=startup.content_batch,
                content_status=startup.content_status,
                content_country=startup.content_country,
                content_yearFounded=startup.content_yearFounded,
                content_tags=tags_str,
                content_website=startup.content_website,
                content_domain=startup.content_domain,
                content_legalName=startup.content_legalName,
                collectedAt=startup.collectedAt,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_product(self, product) -> bool:
        session = self.Session()
        try:
            model = ProductModel(
                schemaVersion=product.schemaVersion,
                recordType=product.recordType,
                source_name=product.source_name,
                source_url=product.source_url,
                content_productName=product.content_productName,
                content_startupName=product.content_startupName,
                content_pricingModel=product.content_pricingModel,
                content_description=product.content_description,
                content_category=product.content_category,
                content_stars_or_likes=product.content_stars_or_likes,
                content_productUrl=product.content_productUrl,
                content_createdDate=product.content_createdDate,
                collectedAt=product.collectedAt,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_paper(self, paper) -> bool:
        session = self.Session()
        try:
            authors_str = ",".join(paper.content_authors) if paper.content_authors else ""
            model = PaperModel(
                schemaVersion=paper.schemaVersion,
                recordType=paper.recordType,
                source_name=paper.source_name,
                source_url=paper.source_url,
                content_title=paper.content_title,
                content_authors=authors_str,
                content_paper_url=paper.content_paper_url,
                content_github_url=paper.content_github_url,
                content_github_stars=paper.content_github_stars,
                content_published_date=paper.content_published_date,
                content_arxiv_id=paper.content_arxiv_id,
                content_abstract=paper.content_abstract,
                collectedAt=paper.collectedAt,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_job(self, job) -> bool:
        session = self.Session()
        try:
            model = JobModel(
                schemaVersion=job.schemaVersion,
                recordType=job.recordType,
                source_name=job.source_name,
                source_url=job.source_url,
                content_title=job.content_title,
                content_company=job.content_company,
                content_date=job.content_date,
                content_is_remote=job.content_is_remote,
                content_role_family=job.content_role_family,
                content_location=job.content_location,
                content_salary_range=job.content_salary_range,
                content_jobUrl=job.content_jobUrl,
                date_method=job.date_method,
                collectedAt=job.collectedAt,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_news(self, news) -> bool:
        session = self.Session()
        try:
            entities_str = ",".join(news.content_mentionedEntities) if news.content_mentionedEntities else ""
            model = NewsModel(
                schemaVersion=news.schemaVersion,
                recordType=news.recordType,
                source_name=news.source_name,
                source_url=news.source_url,
                content_title=news.content_title,
                content_articleUrl=news.content_articleUrl,
                content_publishedAt=news.content_publishedAt,
                content_summary=news.content_summary,
                content_mentionedEntities=entities_str,
                date_method=news.date_method,
                collectedAt=news.collectedAt,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_mapping_log(self, log_entry) -> bool:
        session = self.Session()
        try:
            model = EntityMappingLogModel(
                raw_name=log_entry.raw_name,
                canonical_name=log_entry.canonical_name,
                method=log_entry.method,
                score=log_entry.score,
                source_url=str(log_entry.source_url),
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def get_counts(self) -> dict:
        session = self.Session()
        try:
            return {
                "startups": session.query(StartupModel).count(),
                "products": session.query(ProductModel).count(),
                "papers": session.query(PaperModel).count(),
                "jobs": session.query(JobModel).count(),
                "news": session.query(NewsModel).count(),
                "entity_mapping_log": session.query(EntityMappingLogModel).count(),
            }
        finally:
            session.close()

    def prune_expired_temporal_records(self, max_age_hours: int = 24) -> dict:
        """Purges jobs and news records published older than max_age_hours or outside temporal window."""
        session = self.Session()
        try:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=max_age_hours)
            future_cutoff = now + timedelta(minutes=10)

            # Prune jobs
            jobs = session.query(JobModel).all()
            pruned_jobs = 0
            for j in jobs:
                try:
                    dt = dateutil_parser.isoparse(j.content_date)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                except Exception:
                    continue
                if dt < cutoff or dt > future_cutoff:
                    session.delete(j)
                    pruned_jobs += 1

            # Prune news
            news = session.query(NewsModel).all()
            pruned_news = 0
            for n in news:
                try:
                    dt = dateutil_parser.isoparse(n.content_publishedAt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                except Exception:
                    continue
                if dt < cutoff or dt > future_cutoff:
                    session.delete(n)
                    pruned_news += 1

            session.commit()
            logger.info(
                f"Pruned expired temporal records: {pruned_jobs} jobs, {pruned_news} news (cutoff={cutoff.isoformat()})"
            )
            return {"pruned_jobs": pruned_jobs, "pruned_news": pruned_news}
        except Exception as e:
            session.rollback()
            logger.error(f"Error pruning temporal records: {e}")
            raise
        finally:
            session.close()


db_manager = DatabaseManager()
