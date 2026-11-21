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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 40, 24, page_text)
        self.drawString(40, 24, "FrontierAtlas AI Competitive Intelligence Pipeline — System Architecture Specification")
        self.restoreState()


def build_architecture_pdf(output_path="architecture.pdf"):
    # Margins: 40pt horizontal, 36pt vertical -> Usable: 532pt x 720pt
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=5,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=5,
        spaceAfter=2.5,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.8,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.4,
        leading=10.2,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=2,
    )
    code_style = ParagraphStyle(
        "CodeStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#1A202C"),
    )

    story = []

    # ================= PAGE 1 =================
    story.append(Paragraph("Autonomous AI Intelligence Pipeline", title_style))
    story.append(Paragraph(
        "Architecture Blueprint, 500k Scale Strategy, Multi-Tier Fault-Tolerance & Production Schema Design<br/>"
        "<b>GitHub</b>: github.com/Tharun4743/frontier-atlas-ai-pipeline • <b>Live Dashboard</b>: 6-Tab Google Sheet Synced",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=5))

    story.append(Paragraph("1. System Topology & Ingestion Pipeline", h1_style))
    story.append(Paragraph(
        "The FrontierAtlas AI Competitive Intelligence Pipeline is a distributed, high-throughput asynchronous engine "
        "engineered for massive bulk ingestion, grounded extraction, deterministic canonicalization, and multi-sink synchronization "
        "across 5 ecosystem verticals: Startups, Products, Research Papers, Jobs, and News.",
        body_style
    ))

    diag_data = [
        [Paragraph("<b>Source Ingestion Layer</b><br/>arXiv API, Hugging Face Spaces & Datasets, YC Company Directory, 5 News Feeds, 5 Tech Job Boards", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Resilient Networking & Anti-Bot Escalation</b><br/>Token Bucket (Per-Domain) • Concurrency Semaphore • Tier 1 (Native Async) → Tier 2 (curl_cffi TLS) → Tier 3 (Playwright)", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Extraction & Anti-Hallucination Grounding Gate</b><br/>Trafilatura / Readability Text Extraction • Multi-LLM Orchestrator • Lexical Substring & 70% Token Overlap Gate", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Deterministic Entity Resolution & Audit</b><br/>Seed Ground Truth (50 Entities) • Legal Suffix Stripping • Exact Domain Match • Entity Mapping Log", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Persistence, 24h Rolling Freshness & Multi-Sink Synchronization</b><br/>SQLAlchemy (SQLite / Postgres) with Unique Constraints • Google Sheets (6 Tabs) • Local CSV Mirroring", code_style)],
    ]
    diag_table = Table(diag_data, colWidths=[532])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
        ('BOX', (0, 0), (0, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 5))

    story.append(Paragraph("2. Tiered Anti-Bot & Network Escalation Protocol", h1_style))
    story.append(Paragraph(
        "To reliably bypass perimeter bot mitigation systems without stalling, the HTTP engine cascades across 4 tiers:",
        body_style
    ))

    tier_data = [
        ["Tier", "Engine", "Capabilities & Protections", "Throughput Limit"],
        ["Tier 1", "aiohttp Native Async", "HTTP/1.1 & HTTP/2, User-Agent rotation, token bucket rate limiter.", "5 req/s, 5 conn/domain"],
        ["Tier 2", "curl_cffi TLS", "Chrome 120 browser JA3/JA4 fingerprint impersonation.", "3 req/s, TLS mimicry"],
        ["Tier 3", "Playwright Headless", "Full DOM evaluation, client-side SPA JavaScript execution.", "1 worker, high cost"],
        ["Tier 4", "Dead-Letter Queue", "Skip record, emit structured JSON warning to pipeline log.", "Terminal boundary"],
    ]
    tier_table = Table(tier_data, colWidths=[52, 115, 255, 110])
    tier_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.2),
        ('FONTSIZE', (0, 1), (-1, -1), 7.2),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(tier_table)

    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("3. Anti-Hallucination Grounding Architecture", h1_style))
    story.append(Paragraph(
        "Generative LLM extraction introduces non-zero risk of phantom entities, hallucinated metrics, or fabricated URLs. "
        "The pipeline implements a mandatory zero-trust verification gate between LLM inference and persistence:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Lexical Search & Normalization</b>: Strips punctuation and converts candidate fields and raw source text into canonical token streams.<br/>"
        "• <b>Dual-Stage Grounding Gate</b>: Checks for strict substring containment; falls back to token overlap requiring ≥ 70% match.<br/>"
        "• <b>Nulling Policy</b>: Any extracted field failing grounding is replaced with <i>null</i>.<br/>"
        "• <b>Record Dropping Gate</b>: If any mandatory field (e.g. startup name, website, paper URL) is ungrounded or absent, the record is dropped entirely.<br/>"
        "• <b>Audit Tracking</b>: The acceptance verification suite monitors and reports the exact percentage of nulled fields and dropped records.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("4. Fault-Tolerant LLM Orchestrator & Circuit Breakers (413 & 429 Handling)", h1_style))
    story.append(Paragraph(
        "The LLM Orchestrator balances workloads across Gemini 1.5 Flash, Groq Llama 3, and DeepSeek with automated self-healing:",
        body_style
    ))

    llm_error_data = [
        ["Failure Condition", "Detection", "Autonomous Mitigation Protocol", "Failover Path"],
        ["429 Rate Limit", "HTTP 429 Status", "Exponential backoff with randomized jitter (2^attempt + U(0.5, 1.5)s)", "Next Provider"],
        ["413 Payload Too Large", "HTTP 413 Status", "Semantic token budgeting halves input text at sentence boundary", "Next Provider"],
        ["Malformed JSON", "json.loads exception", "Three-stage repair: fence stripping, regex boundary isolation", "Next Provider"],
        ["Repeated Service Down", "3 consecutive failures", "Circuit Breaker trips to OPEN; 60-second cooldown period", "Next Provider"],
    ]
    llm_table = Table(llm_error_data, colWidths=[105, 95, 222, 110])
    llm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.2),
        ('FONTSIZE', (0, 1), (-1, -1), 7.2),
        ('GRID', (0, 0), (-1, 0), 0.5, colors.HexColor("#E2E8F0")),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(llm_table)
    story.append(Spacer(1, 3))

    story.append(Paragraph("5. Deterministic Entity Resolution", h1_style))
    story.append(Paragraph(
        "Entity resolution establishes graph linkage across noisy crawled references (e.g., 'OpenAI', 'OpenAI, Inc.', 'Open AI' → 'OpenAI'):",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Resolution Hierarchy</b>: 1) Domain Exact Match (score 1.0) → 2) Alias Dictionary (score 1.0) → 3) Suffix-Stripped Normalized Match (score 1.0) → 4) Token Overlap (score ≥ 0.8) → 5) Clean Fallback.<br/>"
        "• <b>Legal Suffixes Removed</b>: Inc., LLC, Corp, Ltd, Technologies, Systems, Labs, B.V., GmbH, PBC.<br/>"
        "• <b>Auditability</b>: Every resolved entity generates an explicit row in the <i>Entity Mapping Log</i> containing raw name, canonical name, method, score, and source URL.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("6. 500k Scaling Strategy: Distributed Ingestion & LLM Optimization", h1_style))
    story.append(Paragraph(
        "To scale ingestion and extraction from thousands to 500,000+ entities while controlling cloud costs and API limits:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Distributed Celery / Ray Ingestion</b>: Workloads are partitioned across distributed worker pools connected to a Redis message queue. Domain-partitioned token buckets regulate per-host concurrency across hundreds of target domains.<br/>"
        "• <b>Dynamic Proxy Mesh</b>: Automatically cycles residential and datacenter proxies to prevent IP blocks at 500k scale.<br/>"
        "• <b>SLM & Heuristic Pre-Filtering</b>: Fast regex and a quantized Small Language Model (SLM) evaluate candidate pages, bypassing frontier LLM extraction on 80% of routine records to slash token costs.<br/>"
        "• <b>Semantic Embedding Cache</b>: Vector embeddings of incoming text blocks are cached in Qdrant/pgvector; near-duplicate texts (≥ 0.95 cosine similarity) reuse cached structured schemas, cutting LLM API costs by ~75%.",
        bullet_style
    ))

    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("7. Relational Canonical Schema & Storage Architecture", h1_style))
    story.append(Paragraph(
        "All pipeline data persists in PostgreSQL / SQLite via SQLAlchemy with strict relational constraints and canonical field schemas:",
        body_style
    ))

    schema_data = [
        ["Table / Entity", "Primary Key & Unique Constraint", "Canonical Field Schema", "Volume Threshold"],
        ["Startups", "id (PK), content_website (UQ)", "content_entityName, content_data_employeeCount, content_batch", "≥ 1,000 unique"],
        ["Products", "id (PK), content_productUrl (UQ)", "content_productName, content_startupName, content_pricingModel", "≥ 1,000 unique"],
        ["Research Papers", "id (PK), content_paper_url (UQ)", "content_title, content_paper_url, content_github_url, content_github_stars", "≥ 1,000 code+stars"],
        ["Jobs", "id (PK), content_jobUrl (UQ)", "content_company, content_date, content_is_remote, content_role_family", "5 sources, 100% ≤ 24h"],
        ["News", "id (PK), content_articleUrl (UQ)", "content_title, content_articleUrl, content_publishedAt, date_method", "5 sources, 100% ≤ 24h"],
        ["Entity Mapping Log", "id (PK)", "raw_name, canonical_name, method, score, source_url", "Audit traceability"],
    ]
    schema_table = Table(schema_data, colWidths=[90, 140, 212, 90])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.2),
        ('FONTSIZE', (0, 1), (-1, -1), 7.2),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(schema_table)
    story.append(Spacer(1, 3))

    story.append(Paragraph("8. 500k Scaling Strategy: Database Indexing & Cold Lake Tiering", h1_style))
    story.append(Paragraph(
        "Scaling relational persistence to 500,000 records requires enterprise database optimizations and tiered storage architecture:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>PgBouncer Connection Pooling</b>: Transaction-level pooling multiplexes thousands of async Celery/Ray workers over 200 persistent PostgreSQL connections, preventing database connection exhaustion.<br/>"
        "• <b>Composite B-Tree Indexes & Partitioning</b>: B-Tree indexes on <i>(content_entityName, content_domain)</i> and <i>(source_name, collectedAt)</i> deliver sub-10ms queries. Declarative monthly table partitioning accelerates temporal queries.<br/>"
        "• <b>Bulk Batch Ingestion</b>: Replaces single-row inserts with batched <i>COPY</i> / <i>INSERT ... ON CONFLICT DO UPDATE</i> chunks (5,000 rows/batch), reaching sustained write throughput > 10,000 records/second.<br/>"
        "• <b>S3 / GCS Parquet Cold Lake Tiering</b>: Raw crawled payloads and historical versions are archived to S3/GCS in Snappy-compressed Parquet format, queryable serverless via DuckDB/Athena at near-zero idle compute cost.<br/>"
        "• <b>Google Sheets 10M Cell Management</b>: High-volume raw data resides in PostgreSQL and Parquet cold lake; Google Sheets receives executive cohort partitions and curated analytical views to stay strictly within cell limits.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("9. Sink Replication & 24-Hour Freshness Tracking", h1_style))
    story.append(Paragraph(
        "• <b>Google Sheets Dashboard</b>: Automated service account / CLI synchronization creates/updates exactly 6 ordered tabs: <i>Startups</i>, <i>Products</i>, <i>Research Papers</i>, <i>Jobs</i>, <i>News</i>, and <i>Entity Mapping Log</i> with public read-only access.<br/>"
        "• <b>Atomic CSV Backups</b>: Mirrors all database tables to <i>output/*.csv</i> with 100% schema parity for offline analysis.<br/>"
        "• <b>Automated 24h Rolling TTL Freshness</b>: The <i>prune_expired_temporal_records(max_age_hours=24)</i> engine purges stale job and news listings prior to export, guaranteeing 100% freshness compliance across 5 sources each.",
        bullet_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("10. Acceptance Verification Suite (Definition of Done)", h1_style))
    story.append(Paragraph(
        "The automated acceptance script (<i>scripts/verify_output.py</i>) executes 4 deterministic verification gates:<br/>"
        "1. <b>Volume Audit</b>: Confirms ≥ 1,000 startups, ≥ 1,000 products, and ≥ 1,000 papers with code and stars (0 null source URLs).<br/>"
        "2. <b>Freshness Audit</b>: Verifies 100% of Jobs and News records are within 24 hours of collection across 5 sources each with date methods.<br/>"
        "3. <b>Grounding Integrity</b>: Reports exact percentage of nulled and dropped items, failing on ungrounded survivors.<br/>"
        "4. <b>Export Completeness</b>: Confirms all 6 CSV backup exports are non-empty, schema-compliant, and present.",
        bullet_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF successfully built at: {output_path}")


if __name__ == "__main__":
    build_architecture_pdf()
