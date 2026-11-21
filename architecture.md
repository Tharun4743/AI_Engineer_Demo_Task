# AI Competitive Intelligence Pipeline: System Architecture Specification

## 1. Executive Summary & Topology
The Autonomous AI Competitive Intelligence Pipeline is a distributed, resilient, asynchronous ingestion and extraction system designed to track startups, products, academic research, technical employment, and market events across the global AI ecosystem.

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
                              │ • LLM Multi-Provider Orchestrator│
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

## 2. Tiered Networking & Anti-Bot Escalation Protocol
High-volume crawlers encounter perimeter defenses (Cloudflare, PerimeterX, Datadome, AWS WAF). The pipeline resolves this with an automated 4-tier escalation model:

| Tier | Engine | Protocol / Technique | Concurrency & Protection |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `aiohttp` Native Async | HTTP/1.1 & HTTP/2 with User-Agent rotation and RFC-compliant token bucket rate limiting. | Semaphore: 5 per domain; Rate: 5 req/sec. |
| **Tier 2** | `curl_cffi` | Native TLS Client Hello JA3/JA4 fingerprint impersonation (`impersonate="chrome120"`). | Bypasses header checks and TCP/IP stack fingerprints. |
| **Tier 3** | `playwright` | Headless Chromium execution executing dynamic client-side SPA scripts and shadow DOMs. | Single-tab worker with randomized human interaction jitter. |
| **Tier 4** | Dead Letter Queue | Hard failure boundary; structured JSON error logged and record skipped without corruption. | Prevents pipeline stalling. |

---

## 3. Anti-Hallucination Grounding & Extraction
Generative extraction introduces severe risk of hallucinated funding rounds, fictitious URLs, or phantom founders. The pipeline enforces strict lexical anchoring:

1. **Extraction Prompts**: Zero-shot, schema-constrained prompts forcing exact JSON outputs.
2. **Grounding Validator**:
   - For every extracted field, the system normalizes both the candidate text and the raw crawled HTML/document text.
   - Exact substring and high-confidence token overlap ($\ge 70\%$) are tested.
   - If an ungrounded field is detected, it is immediately converted to `null`.
   - If any required schema field (`name`, `website`, `paper_url`, `title`) is ungrounded or missing, the entire record is dropped.
   - Comprehensive audit metrics report the exact percentage of nulled fields and dropped records.

---

## 4. Fault-Tolerant LLM Orchestrator
The LLM inference layer utilizes an abstraction layer supporting Gemini 1.5 Flash, Groq Llama 3, and DeepSeek Chat with resilient error mitigation:

- **429 Rate Limiting**: Exponential backoff with jitter ($t = 2^{\text{attempt}} + \text{rand}(0.5, 1.5)$) followed by automatic failover to the subsequent provider.
- **413 Payload Too Large**: Dynamic semantic chunking halves the input text token budget (`semantic_chunker.halve_payload`) while preserving sentence integrity, then retries before failover.
- **Malformed JSON**: Automated repair engine removes markdown fences, isolates outermost curly braces, and verifies JSON syntax before escalating.
- **Circuit Breaker**: Isolates unhealthy provider APIs after 3 consecutive failures for a 60-second cooldown period.

---

## 5. Deterministic Entity Resolution Engine
Entity names appear under multiple noisy variants (e.g. "OpenAI", "Open AI", "OpenAI, Inc.", "OpenAI LLC"). The resolution engine applies deterministic canonicalization:

$$\text{Canonical}(\text{Raw}) = \begin{cases} 
\text{DomainIndex}(\text{domain}) & \text{if domain matches seed} \\
\text{AliasIndex}(\text{lower}(\text{raw})) & \text{if exact alias match} \\
\text{NormalizedIndex}(\text{clean}(\text{raw})) & \text{if suffix/punct stripped} \\
\text{SimilarityMatch}(\text{raw}) & \text{if token overlap} \ge 0.80 \\
\text{CleanFallback}(\text{raw}) & \text{otherwise}
\end{cases}$$

Every resolution produces an audit entry in the `Entity Mapping Log` recording `raw_name`, `canonical_name`, `method`, `score`, and `source_url`.

---

## 6. Storage & Sink Synchronization
- **Relational Storage**: Managed through SQLAlchemy with SQLite (`data/pipeline.db`) or PostgreSQL. Enforces `UNIQUE` constraints on all canonical URLs to guarantee zero duplicate rows per entity.
- **24-Hour Temporal Freshness**: Strict TTL tracking for jobs and news. The automated `prune_expired_temporal_records(max_age_hours=24)` routine guarantees that all records exported to CSV and Google Sheets fall strictly within the rolling 24-hour window.
- **Google Sheets Sync**: `gspread` service account synchronization updating exactly 6 ordered tabs:
  1. `Startups` (16 columns, $\ge 1,000$ unique startups)
  2. `Products` (13 columns, $\ge 1,000$ unique products)
  3. `Research Papers` (12 columns, $\ge 1,000$ papers with code repository and stars)
  4. `Jobs` (14 columns, 5 distinct sources, $100\% \le 24$h fresh)
  5. `News` (11 columns, 5 distinct sources, $100\% \le 24$h fresh)
  6. `Entity Mapping Log` (5 columns, full resolution audit trail)
- **CSV Backups**: Automatic fail-safe export to `output/*.csv` guarantees complete data preservation.

---

## 7. 500,000 Record Scaling Architecture (500k Scale Strategy)
To scale ingestion and extraction from thousands to 500,000+ records while controlling cloud costs, latency, and database contention, the architecture incorporates four core scaling pillars:

### 7.1 Distributed Ingestion Engine (Celery / Ray)
- **Sharded Asynchronous Workers**: Decouples URL crawling across Celery/Ray worker pools orchestrated via Redis/RabbitMQ message queues.
- **Domain-Partitioned Token Buckets**: Redis-backed distributed rate-limiting prevents 429 penalties across 500k pages from hundreds of distinct target hosts.
- **Dynamic Proxy Mesh**: Automatically routes requests across a distributed pool of residential and datacenter proxies with automatic IP rotation upon 403/429 signals.

### 7.2 High-Performance PostgreSQL & Relational Indexing
- **PgBouncer Connection Pooling**: Transaction-level pooling sustains thousands of concurrent worker writes without saturating PostgreSQL connection limits.
- **Composite B-Tree Indexes**: B-Tree indexes on `(content_entityName, content_domain)` and `(source_name, collectedAt)` enable sub-10ms point queries and rapid deduplication checks.
- **Timestamp Partitioning**: Declarative table partitioning by ingestion month/week isolates temporal pruning operations and accelerates queries.
- **Bulk Batch Ingestion**: Replaces single-record insertions with bulk `COPY` or `INSERT ... ON CONFLICT DO UPDATE` batch chunks of 5,000 records, achieving throughput $> 10,000$ writes/sec.

### 7.3 LLM Cost & Throughput Optimization (SLM Pre-Filtering & Semantic Cache)
- **Heuristic & SLM Pre-Filtering**: A compact Small Language Model (SLM / quantized ONNX) and fast regex heuristics pre-filter 80% of routine records (e.g. standard job postings, structured metadata), bypassing expensive frontier LLM calls.
- **Semantic Embedding Cache**: Extracted text vectors are cached in Qdrant/pgvector. Identical or near-duplicate documents ($\ge 0.95$ cosine similarity) reuse previous extraction results, reducing API token costs by $\approx 75\%$.
- **Aggressive Batching & Semantic Token Budgeting**: Batching multiple payloads into single prompts maximizes prompt cache utilization and eliminates redundant context tokens.

### 7.4 Multi-Tier Cold Lake Storage Tiering
- **Parquet Cold Data Lake**: Raw HTML crawls, intermediate extraction payloads, and historical versions stream directly to object storage (Amazon S3 / Google Cloud Storage) serialized as partitioned Snappy-compressed Parquet files.
- **Serverless Querying**: Downstream analytics and training sets query the Parquet cold lake via DuckDB, Trino, or BigQuery External Tables at near-zero idle compute cost.
- **Google Sheets Partitioning & Aggregation**: Respects Google Sheets' 10,000,000 cell hard ceiling by writing full raw datasets to PostgreSQL and the Parquet lake, while publishing aggregated executive views and top-priority cohorts to Google Sheets.
