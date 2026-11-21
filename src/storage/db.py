import os
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from src.core.models import Startup, Product, Paper, Job, News, EntityMappingLog

Base = declarative_base()


class StartupModel(Base):
    __tablename__ = "startups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    website = Column(String(512), nullable=False, unique=True)
    source_url = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    batch = Column(String(64), nullable=True)
    status = Column(String(64), default="Active")
    country = Column(String(64), nullable=True)
    year_founded = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)  # Comma-separated or JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("website", name="uq_startup_website"),
        Index("idx_startup_canonical", "canonical_name"),
    )


class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=True)
    product_url = Column(String(1024), nullable=False, unique=True)
    source_url = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(128), nullable=True)
    stars_or_likes = Column(Integer, default=0)
    created_date = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("product_url", name="uq_product_url"),
        Index("idx_product_name", "name"),
    )


class PaperModel(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)
    paper_url = Column(String(1024), nullable=False, unique=True)
    source_url = Column(String(1024), nullable=False)
    arxiv_id = Column(String(64), nullable=True)
    published_date = Column(String(64), nullable=True)
    abstract = Column(Text, nullable=True)
    github_url = Column(String(1024), nullable=False)
    github_stars = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("paper_url", name="uq_paper_url"),
        Index("idx_paper_github", "github_url"),
    )


class JobModel(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)
    company_name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=True)
    job_url = Column(String(1024), nullable=False, unique=True)
    source_url = Column(String(1024), nullable=False)
    location = Column(String(255), nullable=True)
    salary_range = Column(String(128), nullable=True)
    published_at = Column(DateTime, nullable=False)
    date_method = Column(String(64), nullable=False)
    source_name = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("job_url", name="uq_job_url"),
        Index("idx_job_published", "published_at"),
    )


class NewsModel(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)
    article_url = Column(String(1024), nullable=False, unique=True)
    source_url = Column(String(1024), nullable=False)
    source_name = Column(String(128), nullable=False)
    published_at = Column(DateTime, nullable=False)
    date_method = Column(String(64), nullable=False)
    summary = Column(Text, nullable=True)
    mentioned_entities = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("article_url", name="uq_news_article_url"),
        Index("idx_news_published", "published_at"),
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

    def save_startup(self, startup: Startup) -> bool:
        session = self.Session()
        try:
            tags_str = ",".join(startup.tags) if startup.tags else ""
            model = StartupModel(
                canonical_name=startup.canonical_name,
                legal_name=startup.legal_name,
                domain=startup.domain,
                website=str(startup.website),
                source_url=str(startup.source_url),
                description=startup.description,
                batch=startup.batch,
                status=startup.status,
                country=startup.country,
                year_founded=startup.year_founded,
                tags=tags_str,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_product(self, product: Product) -> bool:
        session = self.Session()
        try:
            model = ProductModel(
                name=product.name,
                canonical_name=product.canonical_name,
                product_url=str(product.product_url),
                source_url=str(product.source_url),
                description=product.description,
                category=product.category,
                stars_or_likes=product.stars_or_likes,
                created_date=product.created_date,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_paper(self, paper: Paper) -> bool:
        session = self.Session()
        try:
            model = PaperModel(
                title=paper.title,
                paper_url=str(paper.paper_url),
                source_url=str(paper.source_url),
                arxiv_id=paper.arxiv_id,
                published_date=paper.published_date,
                abstract=paper.abstract,
                github_url=str(paper.github_url),
                github_stars=paper.github_stars,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_job(self, job: Job) -> bool:
        session = self.Session()
        try:
            model = JobModel(
                title=job.title,
                company_name=job.company_name,
                canonical_name=job.canonical_name,
                job_url=str(job.job_url),
                source_url=str(job.source_url),
                location=job.location,
                salary_range=job.salary_range,
                published_at=job.published_at,
                date_method=job.date_method,
                source_name=job.source_name,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_news(self, news: News) -> bool:
        session = self.Session()
        try:
            entities_str = ",".join(news.mentioned_entities) if news.mentioned_entities else ""
            model = NewsModel(
                title=news.title,
                article_url=str(news.article_url),
                source_url=str(news.source_url),
                source_name=news.source_name,
                published_at=news.published_at,
                date_method=news.date_method,
                summary=news.summary,
                mentioned_entities=entities_str,
            )
            session.add(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_mapping_log(self, log_entry: EntityMappingLog) -> bool:
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


db_manager = DatabaseManager()
