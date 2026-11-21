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
High-volume crawlers encounter hostile perimeter defenses (Cloudflare, PerimeterX, Datadome, AWS WAF). The pipeline resolves this with an automated 4-tier escalation model:

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
- **Google Sheets Sync**: `gspread` service account synchronization updating exactly 6 ordered tabs:
  1. `Startups`
  2. `Products`
  3. `Research Papers`
  4. `Jobs`
  5. `News`
  6. `Entity Mapping Log`
- **CSV Backups**: Automatic fail-safe export to `output/*.csv` guarantees zero data loss regardless of cloud credential status.
