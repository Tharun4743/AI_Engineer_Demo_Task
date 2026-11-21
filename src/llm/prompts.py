EXTRACTION_SYSTEM_PROMPT = """You are a strictly grounded, deterministic data extraction engine.
CRITICAL RULES:
1. Extract ONLY facts explicitly present in the provided source text.
2. If any field or detail is not explicitly mentioned in the source text, set it strictly to null.
3. NEVER assume, extrapolate, or hallucinate entities, URLs, founders, or metrics.
4. Output must strictly be a valid JSON object matching the requested schema. No markdown formatting, no explanations.
"""

STARTUP_EXTRACTION_PROMPT = """Extract the startup details from the source text below.
JSON Schema:
{{
  "canonical_name": "string (Required)",
  "website": "string (Required URL)",
  "description": "string or null",
  "batch": "string or null",
  "status": "string or null",
  "country": "string or null",
  "year_founded": "integer or null",
  "tags": ["string"]
}}

Source Text:
---
{text}
---
"""

PRODUCT_EXTRACTION_PROMPT = """Extract AI product/app details from the source text below.
JSON Schema:
{{
  "name": "string (Required)",
  "product_url": "string (Required URL)",
  "description": "string or null",
  "category": "string or null",
  "stars_or_likes": "integer or null"
}}

Source Text:
---
{text}
---
"""

PAPER_EXTRACTION_PROMPT = """Extract the research paper and associated code repository from the source text below.
JSON Schema:
{{
  "title": "string (Required)",
  "paper_url": "string (Required URL)",
  "arxiv_id": "string or null",
  "published_date": "string or null",
  "abstract": "string or null",
  "github_url": "string or null (Required if code link mentioned)",
  "github_stars": "integer or null"
}}

Source Text:
---
{text}
---
"""
