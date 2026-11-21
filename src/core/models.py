from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class Startup(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "STARTUP"
    source_name: str = ""
    source_url: str = ""
    content_entityName: str = ""
    content_description: Optional[str] = None
    content_data_employeeCount: Optional[int] = None
    content_batch: Optional[str] = None
    content_status: Optional[str] = "Active"
    content_country: Optional[str] = None
    content_yearFounded: Optional[int] = None
    content_tags: List[str] = Field(default_factory=list)
    content_website: str = ""
    content_domain: Optional[str] = None
    content_legalName: Optional[str] = None
    collectedAt: str = ""
    raw_extracted_text: Optional[str] = None


class Product(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "PRODUCT"
    source_name: str = ""
    source_url: str = ""
    content_productName: str = ""
    content_startupName: str = ""
    content_pricingModel: str = "FREE"
    content_description: Optional[str] = None
    content_category: Optional[str] = None
    content_stars_or_likes: Optional[int] = 0
    content_productUrl: str = ""
    content_createdDate: Optional[str] = None
    collectedAt: str = ""
    raw_extracted_text: Optional[str] = None


class Paper(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "RESEARCH_PAPER"
    source_name: str = ""
    source_url: str = ""
    content_title: str = ""
    content_authors: List[str] = Field(default_factory=list)
    content_paper_url: str = ""
    content_github_url: str = ""
    content_github_stars: int = 0
    content_published_date: Optional[str] = None
    content_arxiv_id: Optional[str] = None
    content_abstract: Optional[str] = None
    collectedAt: str = ""
    raw_extracted_text: Optional[str] = None


class Job(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "JOB"
    source_name: str = ""
    source_url: str = ""
    content_title: str = ""
    content_company: str = ""
    content_date: str = ""
    content_is_remote: bool = False
    content_role_family: str = "Engineering"
    content_location: Optional[str] = None
    content_salary_range: Optional[str] = None
    content_jobUrl: str = ""
    date_method: str = ""
    collectedAt: str = ""
    raw_extracted_text: Optional[str] = None


class News(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "NEWS"
    source_name: str = ""
    source_url: str = ""
    content_title: str = ""
    content_articleUrl: str = ""
    content_publishedAt: str = ""
    content_summary: Optional[str] = None
    content_mentionedEntities: List[str] = Field(default_factory=list)
    date_method: str = ""
    collectedAt: str = ""
    raw_extracted_text: Optional[str] = None


class EntityMappingLog(BaseModel):
    raw_name: str
    canonical_name: str
    method: str
    score: float
    source_url: str
