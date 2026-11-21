# Autonomous AI Competitive Intelligence Pipeline

Production-ready, distributed, asynchronous intelligence pipeline for automated ingestion, grounding validation, entity resolution, and synchronized multi-sink publishing across the artificial intelligence ecosystem.

---

## 1. System Architecture

The pipeline processes market intelligence through four decoupled stages:
1. **Tiered Anti-Bot Ingestion Layer**: Cascades from native async HTTP with per-domain token bucket rate limiting to `curl_cffi` TLS browser impersonation (Chrome 120 JA3/JA4 fingerprinting) and headless Playwright.
2. **Extraction & Anti-Hallucination Grounding Gate**: Validates all generative LLM extractions against raw source text using token overlap and lexical substring matching. Ungrounded fields are converted to `null`; records missing mandatory fields are dropped.
3. **Deterministic Entity Resolution**: Resolves noisy variants (e.g., *"OpenAI"*, *"OpenAI, Inc."*, *"Open AI"*) to canonical entities using domain matching, seed aliases, and legal suffix stripping.
4. **Relational Storage & Sink Replication**: Persists deduplicated records in SQLite/PostgreSQL with `UNIQUE` constraints and exports to Google Sheets (6 required tabs) and local CSV files.

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
│   │   ├── db.py                 # SQLite / PostgreSQL via SQLAlchemy with unique constraints
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

## 3. Environment Configuration (`.env`)

Create a local `.env` file using `.env.example`:

```bash
# Database Configuration
DATABASE_URL=sqlite:///data/pipeline.db

# LLM Providers (Optional - automated heuristic fallback active if omitted)
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# GitHub Token (Optional - increases GitHub API rate limit from 60 to 5,000 req/hr)
GITHUB_TOKEN=your_github_personal_access_token

# Google Sheets Service Account
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

# Export Only: Synchronize Database to Google Sheets and CSV Backups
python src/main.py export
```

---

## 5. Definition of Done (DoD) Criteria

The acceptance verification script (`scripts/verify_output.py`) strictly enforces:

| Acceptance Metric | Target Requirement | Verification Method |
| :--- | :--- | :--- |
| **Startups** | $\ge 1,000$ unique startups | Unique website constraint, non-null source URL |
| **Products** | $\ge 1,000$ unique products | Unique product URL constraint, non-null source URL |
| **Research Papers** | $\ge 1,000$ unique papers with code & stars | Non-null `paper_url`, `github_url`, and live `github_stars` |
| **Jobs** | 5 distinct sources, $100\%$ published $\le 24$h | Timestamp validation, `date_method` recorded |
| **News** | 5 distinct sources, $100\%$ published $\le 24$h | RFC 2822 / ISO validation, `date_method` recorded |
| **Canonical Duplicates** | 0 duplicate URLs per tab | SHA-256 URL hash and SQL `UNIQUE` indices |
| **Missing Source URLs** | 0 records without fetched source URL | Foreign provenance audit |
| **Grounding Gate** | Ungrounded fields nulled; invalid dropped | Lexical overlap check against crawled source text |
| **Google Sheet Tabs** | Exactly 6 tabs in specified order | `Startups`, `Products`, `Research Papers`, `Jobs`, `News`, `Entity Mapping Log` |
| **Offline Backup** | 6 complete CSV files | Generated in `output/*.csv` |

Run acceptance verification:
```bash
python scripts/verify_output.py
```

---

## 6. Test Suite Coverage

Execute all automated unit and integration tests:
```bash
python -m pytest tests/ -v
```

Verified assertions:
- **`test_resolver.py`**: Proves `"OpenAI"`, `"OpenAI, Inc."`, `"Open AI"` resolve deterministically to `"OpenAI"`.
- **`test_orchestrator.py`**:
  - $429 \to$ Exponential backoff with jitter $\to$ Failover to secondary provider.
  - $413 \to$ Payload halving at sentence boundary $\to$ Failover.
  - Malformed JSON $\to$ Automated repair $\to$ Failover.
- **`test_dates.py`**: ISO 8601, RFC 2822 pubDate, relative dates (*"3 hours ago"*, *"yesterday"*), and 24-hour freshness boundaries.
- **`test_chunker.py`**: Token budgeting, semantic paragraph truncation, payload halving.
- **`test_validator.py`**: Anti-hallucination grounding, field nulling, missing required field record dropping.
- **`test_dedup.py`**: Query tracking parameter stripping, URL normalization, SHA-256 collision avoidance.
