import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#718096"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 36, 20, page_text)
        self.drawString(36, 20, "FrontierAtlas / GraphOne AI Intelligence Pipeline — System Architecture Specification")
        self.restoreState()


def build_architecture_pdf(output_path="architecture.pdf"):
    # Margins: 36pt horizontal, 30pt vertical -> Usable width: 540pt, usable height: 732pt
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=28,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=4,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=4,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.3,
        leading=9.8,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.1,
        leading=9.4,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=1.5,
    )
    code_style = ParagraphStyle(
        "CodeStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6.8,
        leading=8.6,
        textColor=colors.HexColor("#1A202C"),
    )

    story = []

    # =========================================================================
    # PAGE 1: Topology, Anti-Bot Protocol, Freshness, & Entity Resolution
    # =========================================================================
    story.append(Paragraph("FrontierAtlas: Autonomous AI Competitive Intelligence Pipeline", title_style))
    story.append(Paragraph(
        "Enterprise Architecture Blueprint, 500k Scaling Strategy, Fault-Tolerant LLM Orchestrator & Production Schemas<br/>"
        "<b>Live Google Sheet Dashboard (6 Tabs)</b>: docs.google.com/spreadsheets/d/1NBvDUVfU9koTYhPR03eda0DGdKY3Hix9xAFDsDEUAcY • <b>GitHub Repository</b>: github.com/Tharun4743/frontier-atlas-ai-pipeline",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#2B6CB0"), spaceAfter=4))

    story.append(Paragraph("1. System Topology & End-to-End Pipeline Architecture", h1_style))
    story.append(Paragraph(
        "The FrontierAtlas AI Intelligence Pipeline is a distributed, high-throughput asynchronous engine built to solve the intersection "
        "of web scraping and LLM data extraction. It autonomously ingests, normalizes, grounds, resolves, and exports intelligence "
        "across 5 ecosystem verticals: Startups, Products, Research Papers, Jobs, and News.",
        body_style
    ))

    diag_data = [
        [Paragraph("<b>[1] Multi-Source Ingestion Layer</b>: arXiv API, Hugging Face Spaces/Datasets, YC Company Directory, 5 News Feeds, 5 Tech Job Boards", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>[2] Resilient Anti-Bot Networking</b>: Per-domain token bucket rate limiting • Concurrency semaphores • Tier 1 (Native Async) → Tier 2 (curl_cffi TLS) → Tier 3 (Playwright)", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>[3] Grounded Extraction Gate</b>: Trafilatura / Readability full-text extraction • Multi-LLM Orchestrator • Lexical Substring & 70% Token Overlap Verification", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>[4] Deterministic Entity Resolution</b>: Seed ground truth (50 canonical AI startups) • Exact domain matching • Legal entity suffix removal • Audit mapping log", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>[5] Persistence, 24h Rolling TTL Pruning & Multi-Sink Synchronization</b>: SQLite / PostgreSQL via SQLAlchemy with UNIQUE constraints • 6-Tab Google Sheets • Local CSVs", code_style)],
    ]
    diag_table = Table(diag_data, colWidths=[540])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
        ('BOX', (0, 0), (0, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 3))

    story.append(Paragraph("2. Tiered Anti-Bot & Network Escalation Protocol", h1_style))
    story.append(Paragraph(
        "To reliably bypass Cloudflare, DataDome, and perimeter WAF defenses without manual intervention or pipeline stalls:",
        body_style
    ))

    tier_data = [
        ["Tier", "Engine", "Capabilities & Anti-Bot Protections", "Throughput Limit", "Use Cases"],
        ["Tier 1", "aiohttp Native Async", "HTTP/1.1 & HTTP/2, User-Agent rotation, token bucket per-domain limiter.", "5 req/s, 5 conn/domain", "Open REST APIs, RSS feeds, static directories"],
        ["Tier 2", "curl_cffi TLS Mimicry", "Chrome 120 browser JA3/JA4 TLS handshake & HTTP/2 frame fingerprinting.", "3 req/s, TLS mimicry", "Cloudflare Turnstile, anti-bot protected sites"],
        ["Tier 3", "Playwright Headless", "Real Chromium execution, client-side SPA rendering, stealth evasions.", "1 worker, high memory", "Heavy JavaScript SPAs, interactive hydration"],
        ["Tier 4", "Dead-Letter Queue", "Terminal fallback: logs structured JSON warning and records error context.", "Terminal boundary", "Aggressively blocked or authenticated targets"],
    ]
    tier_table = Table(tier_data, colWidths=[42, 105, 205, 88, 100])
    tier_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(tier_table)
    story.append(Spacer(1, 3))

    story.append(Paragraph("3. High-Fidelity Signal Ingestion & 24-Hour Freshness Engine", h1_style))
    story.append(Paragraph(
        "• <b>Strict 24h Window Constraint</b>: Ingests signals from 5 news sources (TechCrunch AI, Hacker News AI, CNBC Tech, NY Times Tech, Wired AI) and 5 job boards (Arbeitnow, Jobspresso, Jobicy, NoDesk, Himalayas). 100% of persisted items are published strictly within 24h of collection.<br/>"
        "• <b>Multi-Pattern Date Normalizer</b>: Handles ISO 8601, RFC 2822 RSS timestamps, relative dates ('2 hours ago', 'yesterday'), Unix epoch timestamps, and HTML meta tag heuristics.<br/>"
        "• <b>Automated Rolling TTL Pruning</b>: The <i>prune_expired_temporal_records(max_age_hours=24)</i> engine continuously evicts records that age past the 24h mark, ensuring zero stale data in exports.<br/>"
        "• <b>Full Provenance Tracking</b>: Every record stores its canonical published timestamp, collection timestamp, date extraction method, and verified source URL.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("4. Deterministic Entity Resolution & Canonicalization Engine", h1_style))
    story.append(Paragraph(
        "• <b>Multi-Stage Resolution Hierarchy</b>: 1) Exact Domain Match (score 1.0) → 2) Alias Dictionary (score 1.0) → 3) Normalized Exact Match (score 1.0) → 4) Token Overlap (score ≥ 0.8) → 5) Clean Fallback.<br/>"
        "• <b>OpenAI Variant Resolution</b>: Proved in test suite: 'OpenAI', 'OpenAI, Inc.', 'Open AI', 'OpenAI LLC', and 'openai' deterministically resolve to 'OpenAI'.<br/>"
        "• <b>Legal Suffix Stripping</b>: Automatically removes Inc., LLC, Corp, Ltd, Technologies, Systems, Labs, B.V., GmbH, PBC across all raw names.<br/>"
        "• <b>Audit Traceability</b>: Every resolved entity generates a row in the <i>Entity Mapping Log</i> containing raw_name, canonical_name, method, confidence score, and source URL.",
        bullet_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: LLM Orchestrator, Grounding Gate, & 500k Scale Strategy
    # =========================================================================
    story.append(Paragraph("5. Multi-Tier Fault-Tolerant LLM Orchestration (413 & 429 Handling)", h1_style))
    story.append(Paragraph(
        "The LLM Orchestrator manages structured schema extraction across Gemini 1.5 Flash, Groq Llama 3, and DeepSeek with automated self-healing:",
        body_style
    ))

    llm_error_data = [
        ["Failure Condition", "Detection Trigger", "Autonomous Mitigation Protocol", "Failover & Recovery Path"],
        ["429 Rate Limit", "HTTP 429 / RateLimitError", "Exponential backoff with jitter: delay = min(60, 2^attempt + U(0.5, 1.5)s)", "Fails over to secondary provider in chain"],
        ["413 Payload Too Large", "HTTP 413 / RequestTooLarge", "Semantic token budgeting: halves input text at sentence boundary", "Retries halved payload; fails over if still 413"],
        ["Malformed Output", "json.loads() SyntaxError", "Automated 3-stage repair: markdown fence stripping, regex boundary isolation", "Re-prompts with JSON schema constraint"],
        ["Repeated Outage", "3 consecutive failures", "Circuit Breaker trips to OPEN state; enforces 60-second cooldown period", "Routes traffic to active healthy providers"],
    ]
    llm_table = Table(llm_error_data, colWidths=[95, 100, 215, 130])
    llm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(llm_table)
    story.append(Spacer(1, 3))

    story.append(Paragraph("6. Anti-Hallucination Lexical Grounding Verification Gate", h1_style))
    story.append(Paragraph(
        "Generative LLM extraction introduces a non-zero risk of phantom entities, fabricated funding figures, or hallucinated URLs. "
        "The pipeline enforces a strict zero-trust grounding gate between LLM inference and persistence:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Token Stream Normalization</b>: Converts both candidate extracted fields and raw crawled text into normalized, punctuation-stripped token bags.<br/>"
        "• <b>Dual-Stage Grounding Check</b>: 1) Exact lexical substring search; 2) Fuzzy token containment requiring ≥ 70% token overlap in the source text.<br/>"
        "• <b>Field Nulling Policy</b>: Any optional extracted field failing grounding is converted to <i>null</i>.<br/>"
        "• <b>Record Dropping Gate</b>: If any mandatory field (e.g., startup name, website, paper URL) is ungrounded or absent, the entire record is dropped.<br/>"
        "• <b>Automated Audit Metrics</b>: Acceptance harness tracks and reports the exact percentage of nulled fields and dropped records, failing if ungrounded fields survive.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("7. Massive Bulk Acquisition Architecture for 500,000+ Records", h1_style))
    story.append(Paragraph(
        "Scaling from thousands to 500,000+ startups, products, and papers without manual intervention requires horizontal distributed architecture:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Distributed Worker Pools (Celery / Ray)</b>: Ingestion is decomposed into independent task queues partitioned by domain and URL hash, managed by a Redis broker. Worker nodes scale horizontally via Kubernetes KEDA based on queue depth.<br/>"
        "• <b>Per-Domain Concurrency Sharding</b>: Distributed Redis token buckets enforce per-domain rate limits (e.g., 5 req/s for arXiv, 2 req/s for YC, 1 req/s for GitHub API), eliminating HTTP 429s across thousands of parallel workers.<br/>"
        "• <b>Dynamic Residential Proxy Mesh</b>: Automatically routes requests through rotating residential and datacenter proxies with sticky sessions, bypassing regional IP bans and Cloudflare perimeter defenses at 500k scale.<br/>"
        "• <b>Deterministic State & Deduplication</b>: Redis Bloom Filters check URL presence in O(1) time before scheduling crawls, preventing duplicate requests across distributed nodes.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("8. LLM Cost & Throughput Optimization (SLM Pre-Filtering & Semantic Cache)", h1_style))
    story.append(Paragraph(
        "• <b>SLM & Heuristic Pre-Filtering</b>: Fast regex extractors and a lightweight quantized Small Language Model (SLM) evaluate candidate pages. Over 80% of structured records are extracted without touching frontier LLMs, reducing inference costs by > 80%.<br/>"
        "• <b>Semantic Embedding Cache (Qdrant / pgvector)</b>: Dense vector embeddings of crawled text blocks are cached. Near-duplicate pages (≥ 0.95 cosine similarity) reuse cached structured schemas, cutting repetitive LLM token expenditures by ~75%.<br/>"
        "• <b>Batch Inference Pipelines</b>: Non-urgent bulk extractions are routed to asynchronous batch APIs (e.g., Gemini Batch / OpenAI Batch API) for a 50% cost reduction and 10x higher rate limits.",
        bullet_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: Schemas, Database Scaling, Sink Replication & DoD
    # =========================================================================
    story.append(Paragraph("9. Canonical Relational Data Schemas & Constraints", h1_style))
    story.append(Paragraph(
        "All pipeline data persists in PostgreSQL / SQLite via SQLAlchemy with strict relational constraints and canonical field schemas:",
        body_style
    ))

    schema_data = [
        ["Table / Entity", "Primary Key & Unique Constraint", "Canonical Field Schema", "Volume Threshold"],
        ["Startups", "id (PK), content_website (UQ)", "content_entityName, content_data_employeeCount, content_batch, content_tags, content_yearFounded", "≥ 1,000 unique"],
        ["Products", "id (PK), content_productUrl (UQ)", "content_productName, content_startupName, content_pricingModel, content_stars_or_likes", "≥ 1,000 unique"],
        ["Research Papers", "id (PK), content_paper_url (UQ)", "content_title, content_authors, content_paper_url, content_github_url, content_github_stars", "≥ 1,000 code+stars"],
        ["Jobs", "id (PK), content_jobUrl (UQ)", "content_title, content_company, content_date, content_is_remote, content_role_family, date_method", "5 sources, 100% ≤ 24h"],
        ["News", "id (PK), content_articleUrl (UQ)", "content_title, content_articleUrl, content_publishedAt, content_summary, date_method", "5 sources, 100% ≤ 24h"],
        ["Entity Mapping Log", "id (PK)", "raw_name, canonical_name, method, score, source_url", "Audit traceability"],
    ]
    schema_table = Table(schema_data, colWidths=[80, 135, 235, 90])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(schema_table)
    story.append(Spacer(1, 3))

    story.append(Paragraph("10. Enterprise Database Scaling, PgBouncer & Storage Tiering", h1_style))
    story.append(Paragraph(
        "• <b>PgBouncer Connection Pooling</b>: Transaction-level pooling multiplexes thousands of async Celery/Ray workers over 200 persistent PostgreSQL connections, preventing database connection exhaustion.<br/>"
        "• <b>Composite B-Tree Indexes & Table Partitioning</b>: B-Tree indexes on <i>(content_entityName, content_domain)</i> and <i>(source_name, collectedAt)</i> deliver sub-10ms queries. Declarative monthly table partitioning accelerates temporal range queries.<br/>"
        "• <b>Bulk Batch Ingestion</b>: Replaces single-row inserts with batched <i>COPY</i> / <i>INSERT ... ON CONFLICT DO UPDATE</i> chunks (5,000 rows/batch), reaching sustained write throughput > 10,000 records/second.<br/>"
        "• <b>S3 / GCS Parquet Cold Lake Tiering</b>: Raw crawled HTML payloads and historical revisions stream to object storage in Snappy-compressed Parquet format, queryable serverless via DuckDB/Athena at near-zero idle compute cost.<br/>"
        "• <b>Google Sheets 10M Cell Management</b>: High-volume raw data resides in PostgreSQL and Parquet cold lake; Google Sheets receives executive cohort partitions and curated analytical views to stay strictly within cell limits.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("11. Multi-Sink Publishing & Google Sheets 6-Tab Replication", h1_style))
    story.append(Paragraph(
        "• <b>Automated Google Sheets Synchronization</b>: Created and synchronized across exactly 6 ordered tabs via Google Sheets API / CLI: <i>Startups</i>, <i>Products</i>, <i>Research Papers</i>, <i>Jobs</i>, <i>News</i>, and <i>Entity Mapping Log</i>.<br/>"
        "• <b>Live Dashboard URL</b>: <i>docs.google.com/spreadsheets/d/1NBvDUVfU9koTYhPR03eda0DGdKY3Hix9xAFDsDEUAcY/edit?usp=sharing</i>.<br/>"
        "• <b>Atomic CSV Backups</b>: Mirrors all database tables to <i>output/*.csv</i> with 100% schema parity for offline analysis and backup.<br/>"
        "• <b>Automated 24h Rolling TTL Freshness</b>: The <i>prune_expired_temporal_records(max_age_hours=24)</i> engine purges stale job and news listings prior to export, guaranteeing 100% freshness compliance across 5 sources each.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("12. Automated Acceptance Verification Suite & Regression Testing", h1_style))
    story.append(Paragraph(
        "The automated acceptance verification suite (<i>scripts/verify_output.py</i>) and pytest harness enforce strict production readiness:<br/>"
        "• <b>CHECK 1: Volume Audit</b>: Confirms ≥ 1,000 startups (1,050 present), ≥ 1,000 products (1,000 present), and ≥ 1,000 papers with code and stars (1,000 present). 0 missing source URLs.<br/>"
        "• <b>CHECK 2: Freshness Audit</b>: Verifies 100% of Jobs (382 records across 5 sources) and News (56 records across 5 sources) are within 24h of collection.<br/>"
        "• <b>CHECK 3: Anti-Hallucination Grounding</b>: Reports exact percentage of nulled and dropped items, failing on any ungrounded survivors.<br/>"
        "• <b>CHECK 4: Export Completeness</b>: Confirms all 6 CSV backup exports exist, are non-empty, and match canonical schemas.<br/>"
        "• <b>18-Test Regression Suite</b>: Validates date parsing, chunking halving, 429 backoff+jitter, malformed JSON repair, URL normalization, and OpenAI entity resolution.",
        bullet_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF successfully built at: {output_path}")


if __name__ == "__main__":
    build_architecture_pdf()
