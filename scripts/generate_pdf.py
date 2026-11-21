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
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#718096"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "AI Competitive Intelligence Pipeline — System Architecture")
        self.restoreState()


def build_architecture_pdf(output_path="architecture.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6,
    )
    code_style = ParagraphStyle(
        "CodeStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1A202C"),
    )

    story = []

    # ================= PAGE 1 =================
    story.append(Paragraph("Autonomous AI Intelligence Pipeline", title_style))
    story.append(Paragraph("System Architecture Specification & Technical Blueprint", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

    story.append(Paragraph("1. System Topology & Ingestion Pipeline", h1_style))
    story.append(Paragraph(
        "The Autonomous AI Competitive Intelligence Pipeline is a distributed, high-throughput asynchronous engine "
        "designed for ingestion, grounded extraction, deterministic canonicalization, and multi-sink synchronization "
        "across 5 ecosystem domains: Startups, Products, Research Papers, Jobs, and News.",
        body_style
    ))

    # Architecture Topology Flow Diagram Table
    diag_data = [
        [Paragraph("<b>Source Ingestion Layer</b><br/>arXiv API, Hugging Face Spaces & Datasets, Y-Combinator Directory, 5 News RSS Feeds, 5 Tech Job Boards", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Resilient Networking & Anti-Bot Escalation</b><br/>Token Bucket (Per-Domain) • Concurrency Semaphore • Tier 1 (Native) → Tier 2 (curl_cffi TLS) → Tier 3 (Playwright)", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Extraction & Anti-Hallucination Grounding</b><br/>Trafilatura / Readability Text Extraction • Multi-LLM Orchestrator • Lexical Substring & Token Overlap Gate", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Deterministic Entity Resolution</b><br/>Seed Ground Truth (50 Entities) • Legal Suffix Stripping • Exact Domain Match • Entity Mapping Log", code_style)],
        [Paragraph("↓", body_style)],
        [Paragraph("<b>Persistence & Multi-Sink Synchronization</b><br/>SQLAlchemy (SQLite / Postgres) with Unique Constraints • Google Sheets (6 Tabs) • Local CSV Mirroring", code_style)],
    ]
    diag_table = Table(diag_data, colWidths=[500])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
        ('BOX', (0, 0), (0, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 10))

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
    tier_table = Table(tier_data, colWidths=[50, 110, 240, 100])
    tier_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tier_table)

    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("3. Anti-Hallucination Grounding Architecture", h1_style))
    story.append(Paragraph(
        "Generative LLM extraction introduces non-zero risk of phantom entities, hallucinated funding figures, or fabricated URLs. "
        "The pipeline implements a mandatory zero-trust verification gate between LLM inference and database persistence:",
        body_style
    ))

    story.append(Paragraph("Grounding Verification Circuit", h2_style))
    story.append(Paragraph(
        "• <b>Lexical Search & Normalization</b>: Strips punctuation and converts candidate fields and raw source text into canonical token streams.<br/>"
        "• <b>Dual-Stage Grounding Gate</b>: Checks for strict substring containment; falls back to token overlap requiring ≥ 70% match.<br/>"
        "• <b>Nulling Policy</b>: Any extracted field failing grounding is replaced with <i>null</i>.<br/>"
        "• <b>Record Dropping Gate</b>: If any mandatory field (e.g. startup name, website, paper URL) is ungrounded or absent, the record is dropped entirely.<br/>"
        "• <b>Audit Tracking</b>: The acceptance verification suite monitors and reports the exact percentage of nulled fields and dropped records.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4. Fault-Tolerant LLM Orchestrator & Circuit Breakers", h1_style))
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
    llm_table = Table(llm_error_data, colWidths=[100, 90, 210, 100])
    llm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(llm_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("5. Deterministic Entity Resolution", h1_style))
    story.append(Paragraph(
        "Entity resolution establishes graph linkage across noisy crawled references (e.g., 'OpenAI', 'OpenAI, Inc.', 'Open AI' → 'OpenAI').",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Hierarchy</b>: 1) Domain Exact Match (score 1.0) → 2) Alias Dictionary (score 1.0) → 3) Suffix-Stripped Normalized Match (score 1.0) → 4) Token Overlap (score ≥ 0.8) → 5) Clean Fallback.<br/>"
        "• <b>Legal Suffixes Removed</b>: Inc., LLC, Corp, Ltd, Technologies, Systems, Labs, B.V., GmbH, PBC.<br/>"
        "• <b>Auditability</b>: Every resolved entity generates an explicit row in the <i>Entity Mapping Log</i> containing raw name, canonical name, method, score, and source URL.",
        body_style
    ))

    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("6. Relational Data Schema & Storage Architecture", h1_style))
    story.append(Paragraph(
        "All data persists in SQLite (`data/pipeline.db`) or PostgreSQL via SQLAlchemy with strict relational constraints:",
        body_style
    ))

    schema_data = [
        ["Table / Entity", "Primary Key & Unique Constraint", "Core Attributes", "Volume Threshold"],
        ["Startups", "id (PK), website (UNIQUE)", "canonical_name, legal_name, domain, batch, status, country, year", "≥ 1,000 unique"],
        ["Products", "id (PK), product_url (UNIQUE)", "name, canonical_name, description, category, stars_or_likes", "≥ 1,000 unique"],
        ["Research Papers", "id (PK), paper_url (UNIQUE)", "title, arxiv_id, abstract, github_url, github_stars", "≥ 1,000 code+stars"],
        ["Jobs", "id (PK), job_url (UNIQUE)", "title, company_name, canonical_name, location, published_at, date_method", "5 sources, 100% ≤ 24h"],
        ["News", "id (PK), article_url (UNIQUE)", "title, source_name, published_at, date_method, summary", "5 sources, 100% ≤ 24h"],
        ["Entity Mapping Log", "id (PK)", "raw_name, canonical_name, method, score, source_url", "Audit traceability"],
    ]
    schema_table = Table(schema_data, colWidths=[90, 130, 200, 80])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(schema_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("7. Sink Replication: Google Sheets & CSV Backups", h1_style))
    story.append(Paragraph(
        "Replication synchronizes persisted intelligence across cloud and local sinks:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Google Sheets Dashboard</b>: Authorized via Service Account JSON, creating/updating exactly 6 ordered tabs:<br/>"
        "&nbsp;&nbsp;1) `Startups`, 2) `Products`, 3) `Research Papers`, 4) `Jobs`, 5) `News`, 6) `Entity Mapping Log`.<br/>"
        "• <b>Public Sharing</b>: Automatically configures spreadsheet ACL permissions to public read-only.<br/>"
        "• <b>Atomic CSV Backups</b>: Mirrors database tables into `output/*.csv` to guarantee complete offline data preservation.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8. Acceptance Verification Suite (Definition of Done)", h1_style))
    story.append(Paragraph(
        "The automated acceptance script (`scripts/verify_output.py`) executes 4 deterministic verification gates:<br/>"
        "1. <b>Volume Audit</b>: Confirms ≥ 1,000 startups, ≥ 1,000 products, and ≥ 1,000 papers with code and stars.<br/>"
        "2. <b>Freshness Audit</b>: Verifies 100% of Jobs and News records are within 24 hours of collection with recorded date methods.<br/>"
        "3. <b>Grounding Integrity</b>: Reports exact percentage of nulled and dropped items, failing on ungrounded survivors.<br/>"
        "4. <b>Export Completeness</b>: Confirms all 6 CSV backup exports are non-empty and present.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF successfully built at: {output_path}")


if __name__ == "__main__":
    build_architecture_pdf()
