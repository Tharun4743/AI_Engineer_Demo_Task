import json
import re
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from src.core.models import EntityMappingLog
from src.core.logging import logger

LEGAL_SUFFIXES = [
    r"\binc\.?\b",
    r"\bincorporated\b",
    r"\bllc\.?\b",
    r"\bcorp\.?\b",
    r"\bcorporation\b",
    r"\bltd\.?\b",
    r"\blimited\b",
    r"\bpbc\.?\b",
    r"\bsas\.?\b",
    r"\bb\.?v\.?\b",
    r"\bgmbh\b",
    r"\bk\.?k\.?\b",
    r"\btechnologies\b",
    r"\btechnology\b",
    r"\blabs\b",
    r"\bsystems\b",
    r"\bresearch\b",
]


class EntityResolver:
    """Deterministic entity resolver for AI startups and enterprises."""

    def __init__(self, seed_file: str = "config/seed_entities.json"):
        self.seed_file = seed_file
        self.canonical_entities: Dict[str, Dict] = {}
        self.domain_to_canonical: Dict[str, str] = {}
        self.alias_to_canonical: Dict[str, str] = {}
        self.normalized_to_canonical: Dict[str, str] = {}
        self._load_seed_entities()

    def _normalize_name(self, name: str) -> str:
        """Strips legal entity suffixes, special punctuation, and whitespace."""
        if not name:
            return ""
        # Lowercase
        cleaned = name.lower().strip()

        # Strip common legal suffixes
        for suffix_pat in LEGAL_SUFFIXES:
            cleaned = re.sub(suffix_pat, "", cleaned, flags=re.IGNORECASE).strip()

        # Remove punctuation except alphanumeric and space
        cleaned = re.sub(r"[^\w\s]", "", cleaned)

        # Remove internal spaces to resolve "Open AI" -> "openai"
        no_spaces = re.sub(r"\s+", "", cleaned)
        return no_spaces

    def _extract_domain(self, url_or_domain: Optional[str]) -> str:
        if not url_or_domain:
            return ""
        raw = url_or_domain.strip().lower()
        if "://" in raw:
            parsed = urlparse(raw)
            domain = parsed.netloc
        else:
            domain = raw.split("/")[0]

        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    def _load_seed_entities(self):
        if not os.path.exists(self.seed_file):
            return

        try:
            with open(self.seed_file, "r", encoding="utf-8") as f:
                seeds = json.load(f)

            for entity in seeds:
                c_name = entity["canonical_name"]
                self.canonical_entities[c_name] = entity

                # Index domain
                domain = self._extract_domain(entity.get("domain"))
                if domain:
                    self.domain_to_canonical[domain] = c_name

                # Index normalized canonical name
                norm_c = self._normalize_name(c_name)
                self.normalized_to_canonical[norm_c] = c_name

                # Index aliases
                for alias in entity.get("aliases", []):
                    # Direct lowercase alias
                    self.alias_to_canonical[alias.lower().strip()] = c_name
                    # Normalized alias
                    norm_a = self._normalize_name(alias)
                    self.normalized_to_canonical[norm_a] = c_name

        except Exception as e:
            logger.error(f"Failed to load seed entities from {self.seed_file}: {e}")

    def resolve(
        self,
        raw_name: str,
        website_or_url: Optional[str] = None,
        source_url: str = ""
    ) -> Tuple[str, EntityMappingLog]:
        """Resolves raw entity name and website to canonical entity name with mapping log."""
        if not raw_name:
            raw_name = "Unknown"

        raw_clean = raw_name.strip()

        # 1. Exact Domain Match (Highest Precision)
        if website_or_url:
            domain = self._extract_domain(website_or_url)
            if domain and domain in self.domain_to_canonical:
                canonical = self.domain_to_canonical[domain]
                log_entry = EntityMappingLog(
                    raw_name=raw_name,
                    canonical_name=canonical,
                    method="domain_exact",
                    score=1.0,
                    source_url=source_url,
                )
                return canonical, log_entry

        # 2. Exact Alias Match
        raw_lower = raw_clean.lower()
        if raw_lower in self.alias_to_canonical:
            canonical = self.alias_to_canonical[raw_lower]
            log_entry = EntityMappingLog(
                raw_name=raw_name,
                canonical_name=canonical,
                method="alias_exact",
                score=1.0,
                source_url=source_url,
            )
            return canonical, log_entry

        # 3. Normalized Name Match ("Open AI", "OpenAI, Inc." -> "OpenAI")
        norm = self._normalize_name(raw_name)
        if norm and norm in self.normalized_to_canonical:
            canonical = self.normalized_to_canonical[norm]
            log_entry = EntityMappingLog(
                raw_name=raw_name,
                canonical_name=canonical,
                method="normalized_exact",
                score=1.0,
                source_url=source_url,
            )
            return canonical, log_entry

        # 4. Partial / Token containment match for high confidence
        for norm_cand, canonical in self.normalized_to_canonical.items():
            if len(norm) > 4 and len(norm_cand) > 4:
                if norm == norm_cand or norm in norm_cand or norm_cand in norm:
                    # Token similarity ratio
                    score = min(len(norm), len(norm_cand)) / max(len(norm), len(norm_cand))
                    if score >= 0.8:
                        log_entry = EntityMappingLog(
                            raw_name=raw_name,
                            canonical_name=canonical,
                            method="token_similarity",
                            score=round(score, 2),
                            source_url=source_url,
                        )
                        return canonical, log_entry

        # 5. Clean Fallback: Cleaned name without legal suffixes
        cleaned_fallback = re.sub(r"[^\w\s-]", "", raw_clean).strip()
        for suffix_pat in LEGAL_SUFFIXES:
            cleaned_fallback = re.sub(suffix_pat, "", cleaned_fallback, flags=re.IGNORECASE).strip()
        cleaned_fallback = re.sub(r"\s+", " ", cleaned_fallback).strip() or raw_clean

        log_entry = EntityMappingLog(
            raw_name=raw_name,
            canonical_name=cleaned_fallback,
            method="clean_fallback",
            score=0.7,
            source_url=source_url,
        )
        return cleaned_fallback, log_entry


entity_resolver = EntityResolver()
