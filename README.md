# Autonomous AI Competitive Intelligence Pipeline

Production-ready, distributed, asynchronous intelligence pipeline for automated ingestion, grounding validation, entity resolution, and synchronized multi-sink publishing across the artificial intelligence ecosystem.

- **Live Google Sheet Dashboard (6 Tabs)**: [FrontierAtlas Dashboard](https://docs.google.com/spreadsheets/d/1NBvDUVfU9koTYhPR03eda0DGdKY3Hix9xAFDsDEUAcY/edit)
- **GitHub Repository**: [Tharun4743/frontier-atlas-ai-pipeline](https://github.com/Tharun4743/frontier-atlas-ai-pipeline)

---

## 1. System Architecture

The pipeline processes market intelligence through four decoupled stages:
1. **Tiered Anti-Bot Ingestion Layer**: Cascades from native async HTTP with per-domain token bucket rate limiting to `curl_cffi` TLS browser impersonation (Chrome 120 JA3/JA4 fingerprinting) and headless Playwright.
2. **Extraction & Anti-Hallucination Grounding Gate**: Validates all generative LLM extractions against raw source text using token overlap and lexical substring matching. Ungrounded fields are converted to `null`; records missing mandatory fields are dropped.
3. **Deterministic Entity Resolution**: Resolves noisy variants (e.g., *"OpenAI"*, *"OpenAI, Inc."*, *"Open AI"*) to canonical entities using domain matching, seed aliases, and legal suffix stripping.
4. **Relational Storage, Freshness Pruning & Sink Replication**: Persists deduplicated records in SQLite/PostgreSQL with `UNIQUE` constraints, purges stale temporal listings (>24h), and exports to Google Sheets (6 required tabs) and local CSV files.

```
                              ┌──────────────────────────────────┐
                              │     Data Sources & Ingestion     │
                              │ (arXiv, HF, YC, RSS, Job Boards) │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │   Tiered Anti-Bot HTTP Engine    │
                              │ • Token Bucket Rate Limiter      │
                              │ • Per-Domain Concurrency (Sem)   │
                              │ • Tier 1 (Native) -> Tier 2 (TLS)│
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │  Extraction & Grounding Gate     │
                              │ • Trafilatura / Readability Text │
                              │ • Multi-LLM Orchestrator         │
                              │ • Anti-Hallucination Grounding   │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │ Deterministic Entity Resolution  │
                              │ • Legal Suffix Strip & Domain    │
                              │ • 50 Seed Aliases + Fuzzy Match  │
                              │ • Audit Log Generation           │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │  Persistence & Sink Replication  │
                              │ • SQLAlchemy (SQLite / Postgres) │
                              │ • 24h Automated TTL Freshness    │
                              │ • 6-Tab Google Sheets Export     │
                              │ • Atomic CSV Local Backups       │
                              └──────────────────────────────────┘
```

---

## 2. Directory Layout

```
.
├── README.md
├── architecture.pdf              # 3-page executive architecture blueprint
├── architecture.md               # Detailed markdown system specification
├── pyproject.toml                # Project metadata and package configuration
├── requirements.txt              # Production dependency specifications
├── .env.example                  # Environment configuration template
├── config/
│   ├── sources.yaml              # Ingestion sources, selectors, rate limits, tiering
│   └── seed_entities.json        # 50 canonical AI startups, domains, and aliases
├── src/
│   ├── main.py                   # Async CLI: phase1 | phase2 | all | export
│   ├── core/
│   │   ├── http.py               # Async client, token bucket, domain semaphores, tenacity
│   │   ├── antibot.py            # Tiered fetch: Native -> curl_cffi -> Playwright -> Skip
│   │   ├── logging.py            # Single-line JSON structured logger
│   │   └── models.py             # Pydantic v2 data contracts
│   ├── crawlers/
│   │   ├── papers.py             # Papers With Code archive + arXiv + HF + GitHub stars
│   │   ├── startups.py           # Y-Combinator directory + seed startups
│   │   ├── products.py           # Hugging Face Spaces + AI apps
│   │   ├── news.py               # 5 sources, RSS + 24h freshness filter
│   │   └── jobs.py               # 5 sources, API/RSS + 24h freshness filter
│   ├── extraction/
│   │   ├── dates.py              # ISO, RFC 2822, relative date normalization
│   │   ├── fulltext.py           # Trafilatura & BeautifulSoup content extraction
│   │   └── validator.py          # Anti-hallucination lexical grounding validator
│   ├── llm/
│   │   ├── orchestrator.py       # Fallback chain, backoff, halving, JSON repair, circuit breaker
│   │   ├── providers.py          # Gemini Flash, Groq Llama 3, DeepSeek adapters
│   │   ├── chunker.py            # Token budgeting and semantic paragraph truncation
│   │   └── prompts.py            # Zero-shot extraction prompts with JSON schemas
│   ├── resolver/
│   │   └── entity_resolver.py    # Deterministic canonical entity resolution
│   ├── storage/
│   │   ├── db.py                 # SQLite / PostgreSQL via SQLAlchemy with unique constraints & TTL pruning
│   │   └── dedup.py              # SHA-256 URL hashing and deduplication set
│   └── sinks/
│       └── sheets.py             # Google Sheets (6 tabs) and CSV exporter
├── tests/                        # Pytest suite (dates, chunker, orchestrator, resolver, validator, dedup)
├── scripts/
│   ├── generate_pdf.py           # 3-page architecture PDF compiler
│   └── verify_output.py          # Automated Definition of Done acceptance checks
└── output/                       # CSV export backup directory
```

---

## 3. Installation & Environment Setup

### 3.1 Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Git

### 3.2 Virtual Environment & Dependencies
```bash
# 1. Clone or navigate to the repository
cd "AI ENGINEER DEMO"

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# On Windows (PowerShell / Command Prompt):
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 4. Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install Playwright browser binaries (for Tier 3 dynamic crawling)
playwright install chromium
```

### 3.3 Environment Variables Configuration (`.env`)
Create a local `.env` file from `.env.example`:
```bash
cp .env.example .env
```

Key configuration options:
```bash
# Database Configuration
DATABASE_URL=sqlite:///data/pipeline.db

# LLM Providers (Optional - automated heuristic fallback active if omitted)
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# GitHub Token (Optional - increases GitHub API rate limit from 60 to 5,000 req/hr)
GITHUB_TOKEN=your_github_personal_access_token

# Google Sheets Service Account (Optional - for live cloud synchronization)
GOOGLE_SERVICE_ACCOUNT_JSON=config/service_account.json
GOOGLE_SHEET_ID=                                  # Optional: leave empty to create a new sheet
```

---

## 4. Execution Guide (CLI)

The command-line interface provides modular phase execution:

```bash
# Phase 1: Foundational Intelligence (Startups, Products, Research Papers)
python src/main.py phase1

# Phase 2: Real-Time Temporal Ingestion (News, Jobs <= 24h)
python src/main.py phase2

# Full Pipeline Execution (Phase 1 + Phase 2 + Export)
python src/main.py all

# Export Only: Prune Expired Records, Synchronize Google Sheets and Re-export CSVs
python src/main.py export
```

---

## 5. Google Sheets 6-Tab Dataset & Import Guide

The pipeline exports a canonical 6-tab competitive intelligence dataset to `output/*.csv` with 100% schema parity to Google Sheets.

### 5.1 Tab & Schema Mapping Specifications

| Tab Name | Source File | Row Count | Columns | Key Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **Startups** | `output/startups.csv` | $\ge 1,000$ (1,050) | 16 | 100% unique websites, 0 null source URLs, 25 YC cohorts + 50 seeds |
| **Products** | `output/products.csv` | $\ge 1,000$ (1,000) | 13 | 100% unique product URLs, 0 null source URLs, FREE pricing model |
| **Research Papers** | `output/research_papers.csv` | $\ge 1,000$ (1,000) | 12 | 100% unique paper URLs, 100% with GitHub code repository & stars $\ge 1$ |
| **Jobs** | `output/jobs.csv` | Variable (384+) | 14 | 5 sources (Arbeitnow, Jobicy, Jobspresso, Himalayas, NoDesk), $100\% \le 24$h |
| **News** | `output/news.csv` | Variable (56+) | 11 | 5 sources (TechCrunch AI, Hacker News AI, CNBC, NYT, Wired), $100\% \le 24$h |
| **Entity Mapping Log** | `output/entity_mapping_log.csv` | 1,050 | 5 | Deterministic provenance, confidence scores (0.7 to 1.0), audit log |

#### Detailed Column Schemas:
1. **Startups (16 cols)**: `schemaVersion`, `recordType`, `source_name`, `source_url`, `content_entityName`, `content_description`, `content_data_employeeCount`, `content_batch`, `content_status`, `content_country`, `content_yearFounded`, `content_tags`, `content_website`, `content_domain`, `content_legalName`, `collectedAt`.
2. **Products (13 cols)**: `schemaVersion`, `recordType`, `source_name`, `source_url`, `content_productName`, `content_startupName`, `content_pricingModel`, `content_description`, `content_category`, `content_stars_or_likes`, `content_productUrl`, `content_createdDate`, `collectedAt`.
3. **Research Papers (12 cols)**: `schemaVersion`, `recordType`, `source_name`, `source_url`, `content_title`, `content_authors`, `content_paper_url`, `content_github_url`, `content_github_stars`, `content_published_date`, `content_arxiv_id`, `collectedAt`.
4. **Jobs (14 cols)**: `schemaVersion`, `recordType`, `source_name`, `source_url`, `content_title`, `content_company`, `content_date`, `content_is_remote`, `content_role_family`, `content_location`, `content_salary_range`, `content_jobUrl`, `date_method`, `collectedAt`.
5. **News (11 cols)**: `schemaVersion`, `recordType`, `source_name`, `source_url`, `content_title`, `content_articleUrl`, `content_publishedAt`, `content_summary`, `content_mentionedEntities`, `date_method`, `collectedAt`.
6. **Entity Mapping Log (5 cols)**: `raw_name`, `canonical_name`, `method`, `score`, `source_url`.

### 5.2 Step-by-Step Google Sheets Import Instructions

#### Option A: Manual Web UI Import (Zero Credentials Required)
1. **Create Spreadsheet**: Navigate to [Google Sheets](https://sheets.new) and title the document `AI Competitive Intelligence Dashboard`.
2. **Rename Initial Sheet**: Right-click the bottom `Sheet1` tab, select **Rename**, and set it to `Startups`.
3. **Import Tab 1 (Startups)**:
   - Click `File` $\to$ `Import` $\to$ `Upload` tab.
   - Upload `output/startups.csv`.
   - Set **Import location** to `Replace current sheet`.
   - Set **Separator type** to `Detect automatically` (or `Comma`).
   - Check **Convert text to numbers, dates, and formulas**: Select `No` (preserves ISO 8601 formatting).
   - Click **Import data**.
4. **Import Tabs 2 through 6**:
   - For each remaining file (`output/products.csv`, `output/research_papers.csv`, `output/jobs.csv`, `output/news.csv`, `output/entity_mapping_log.csv`):
     - Click `File` $\to$ `Import` $\to$ `Upload`.
     - Select file.
     - Set **Import location** to `Insert new sheet(s)`.
     - Click **Import data**.
     - Rename the created tab to the exact required title:
       - `Products`
       - `Research Papers`
       - `Jobs`
       - `News`
       - `Entity Mapping Log`
5. **Freeze & Format Headers**:
   - On each tab, click Row 1.
   - Go to `View` $\to$ `Freeze` $\to$ `1 row`.
   - Apply Bold formatting (`Ctrl+B`) and fill with dark background `#1E293B` (Slate) with white text.
6. **Set Public Sharing Permissions**:
   - Click **Share** (top-right).
   - Under **General access**, change from `Restricted` to **Anyone with the link**.
   - Ensure the permission dropdown is set to **Viewer**.
   - Click **Copy link** and **Done**.

#### Option B: Automated Service Account Push
1. Download your Google Cloud Service Account key to `config/service_account.json`.
2. Configure `GOOGLE_SERVICE_ACCOUNT_JSON=config/service_account.json` in `.env`.
3. Run `python src/main.py export`. The exporter provisions the spreadsheet, sets public read permissions, updates all 6 tabs, and prints the live URL.

---

## 6. 500k Record Scaling Architecture

Scaling the pipeline from thousands to 500,000+ records requires addressing network throughput, database concurrency, and inference economics:

1. **Distributed Ingestion Engine (Celery / Ray)**:
   - Workloads are sharded across Celery/Ray worker pools backed by a Redis message queue.
   - Domain-partitioned token buckets regulate per-host rate limits across hundreds of distinct domains.
   - Dynamic residential/datacenter proxy pool automatically rotates IPs upon 403/429 signals.

2. **High-Performance PostgreSQL & Relational Indexing**:
   - **PgBouncer Connection Pooling**: Transaction-level pooling multiplexes thousands of concurrent async workers over 200 persistent connections.
   - **Composite B-Tree Indexes**: B-Tree indexes on `(content_entityName, content_domain)` and `(source_name, collectedAt)` enable sub-10ms lookups.
   - **Timestamp Partitioning**: Declarative table partitioning by ingestion month isolates temporal pruning and speeds up range queries.
   - **Bulk Batch Ingestion**: Replaces single-row inserts with batched `COPY` / `INSERT ... ON CONFLICT DO UPDATE` chunks (5,000 rows/batch), reaching sustained write throughput $> 10,000$ writes/sec.

3. **LLM Cost & Throughput Optimization (SLM Pre-Filtering & Semantic Cache)**:
   - **SLM & Heuristic Pre-Filtering**: Fast regex heuristics and a quantized Small Language Model (SLM) evaluate candidate pages, bypassing frontier LLM extraction on 80% of routine records.
   - **Semantic Embedding Cache**: Vector embeddings cached in Qdrant/pgvector allow near-duplicate pages ($\ge 0.95$ cosine similarity) to reuse cached schemas, slashing token costs by $\approx 75\%$.
   - **Semantic Token Budgeting**: Halves payload at sentence boundaries during 413 events to maximize provider token utilization.

4. **Multi-Tier Cold Lake Storage Tiering**:
   - **S3 / GCS Parquet Lake**: Raw crawled documents and historical versions stream directly to object storage in Snappy-compressed Parquet format, queryable serverless via DuckDB or Athena.
   - **Google Sheets 10M Cell Management**: High-volume records reside in PostgreSQL and the Parquet lake; Google Sheets receives executive cohort partitions and curated analytical views to stay strictly within cell limits.

---

## 7. Architecture PDF Generator

The executive technical blueprint (`architecture.pdf`) is compiled from source using ReportLab:

```bash
# Compile architecture.pdf
python scripts/generate_pdf.py
```

### Verification:
```bash
python -c "
import pypdf
reader = pypdf.PdfReader('architecture.pdf')
print(f'Total Pages: {len(reader.pages)}')
assert len(reader.pages) <= 3, 'PDF exceeds 3 pages!'
print('PDF strictly satisfies the <= 3 page requirement.')
"
```

The resulting document strictly satisfies the 3-page constraint and covers:
- System Topology & Ingestion Pipeline
- Tiered Anti-Bot & Network Escalation Protocol
- Anti-Hallucination Grounding Gate
- Fault-Tolerant LLM Orchestrator (413 Payload Halving & 429 Rate Limiting)
- Deterministic Entity Resolution Engine
- 500k Scaling Strategy (Celery/Ray, PostgreSQL/PgBouncer, SLM pre-filter, Parquet cold lake)
- Relational Schema & Storage Architecture
- Sink Replication & 24h Freshness Tracking
- Acceptance Verification Suite (Definition of Done)

---

## 8. Definition of Done (DoD) & Acceptance Verification

Run the automated acceptance verification suite:
```bash
python scripts/verify_output.py
```

Enforced verification criteria:
- **CHECK 1: Volume & Uniqueness**:
  - Startups: $\ge 1,000$ unique startups (1,050 present, 0 null URLs)
  - Products: $\ge 1,000$ unique products (1,000 present, 0 null URLs)
  - Research Papers: $\ge 1,000$ unique papers with code and stars (1,000 present, 0 null URLs)
- **CHECK 2: Jobs & News 24h Freshness & Source Diversity**:
  - Jobs: 5 distinct sources (Arbeitnow, Jobicy, Jobspresso, Himalayas, NoDesk), 100% published within 24h window
  - News: 5 distinct sources (TechCrunch AI, Hacker News AI, CNBC Tech, NY Times Tech, Wired AI), 100% published within 24h window
  - Date extraction method and source URL recorded for every temporal record
- **CHECK 3: Anti-Hallucination Grounding Audit**:
  - Reports nulled and dropped percentages from lexical grounding checks
- **CHECK 4: Export Artifacts Audit**:
  - All 6 CSV files in `output/` verified present, non-empty, and schema-compliant

---

## 9. Test Suite Execution

Execute the automated test suite covering all core pipeline modules:

```bash
python -m pytest tests/ -v
```

> **Note on Windows**: Execute tests via `python -m pytest tests/ -v` to ensure compatibility with Windows Application Control policies.

### Test Coverage (18 tests):
- `tests/test_chunker.py` (3 tests): Token counting with `tiktoken`, semantic paragraph truncation, payload halving.
- `tests/test_dates.py` (4 tests): ISO 8601 parsing, RFC 2822 RSS pubDate parsing, relative time strings (*"3 hours ago"*, *"yesterday"*), and 24h freshness boundary checks.
- `tests/test_dedup.py` (2 tests): Query tracking parameter stripping (`utm_source`, `utm_campaign`), URL normalization, and SHA-256 state tracking.
- `tests/test_orchestrator.py` (3 tests): HTTP 429 exponential backoff with jitter and secondary provider failover, HTTP 413 payload halving, and malformed JSON fence repair.
- `tests/test_resolver.py` (3 tests): OpenAI variant resolution (`"OpenAI"`, `"OpenAI, Inc."`, `"Open AI"` $\to$ `"OpenAI"`), domain-based matching, and legal suffix stripping.
- `tests/test_validator.py` (3 tests): Anti-hallucination grounding validation, ungrounded field nulling, and missing required field record dropping.
