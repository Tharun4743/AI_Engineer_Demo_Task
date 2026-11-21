from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class Startup(BaseModel):
    canonical_name: str
    legal_name: Optional[str] = None
    domain: Optional[str] = None
    website: str
    source_url: str
    description: Optional[str] = None
    batch: Optional[str] = None
    status: Optional[str] = "Active"
    country: Optional[str] = None
    year_founded: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    raw_extracted_text: Optional[str] = None


class Product(BaseModel):
    name: str
    canonical_name: Optional[str] = None
    product_url: str
    source_url: str
    description: Optional[str] = None
    category: Optional[str] = None
    stars_or_likes: Optional[int] = 0
    created_date: Optional[str] = None
    raw_extracted_text: Optional[str] = None


class Paper(BaseModel):
    title: str
    paper_url: str
    source_url: str
    arxiv_id: Optional[str] = None
    published_date: Optional[str] = None
    abstract: Optional[str] = None
    github_url: str
    github_stars: int = 0
    raw_extracted_text: Optional[str] = None


class Job(BaseModel):
    title: str
    company_name: str
    canonical_name: Optional[str] = None
    job_url: str
    source_url: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    published_at: datetime
    date_method: str
    source_name: str
    raw_extracted_text: Optional[str] = None


class News(BaseModel):
    title: str
    article_url: str
    source_url: str
    source_name: str
    published_at: datetime
    date_method: str
    summary: Optional[str] = None
    mentioned_entities: List[str] = Field(default_factory=list)
    raw_extracted_text: Optional[str] = None


class EntityMappingLog(BaseModel):
    raw_name: str
    canonical_name: str
    method: str
    score: float
    source_url: str
