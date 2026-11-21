import re
from typing import Dict, Any, Tuple, Optional, List
from src.core.logging import logger


class GroundingValidator:
    """Anti-hallucination grounding validator.
    
    Verifies that extracted fields are lexically anchored in the raw source text.
    Any ungrounded extracted field is nulled.
    Records missing required fields after validation are dropped.
    """

    def __init__(self):
        self.total_checked_fields: int = 0
        self.total_nulled_fields: int = 0
        self.total_checked_records: int = 0
        self.total_dropped_records: int = 0

    def clean_text_for_search(self, text: str) -> str:
        """Lowercases and cleans punctuation for lexical grounding matching."""
        if not text:
            return ""
        return re.sub(r"[^\w\s]", " ", text.lower())

    def is_grounded(self, field_value: Any, raw_source_text: str) -> bool:
        """Verifies if the field value exists in raw source text."""
        if field_value is None:
            return True  # Already null, no grounding violation
        
        val_str = str(field_value).strip()
        if not val_str or not raw_source_text:
            return False

        # If it's a short string or number, check word boundary
        cleaned_source = self.clean_text_for_search(raw_source_text)
        cleaned_val = self.clean_text_for_search(val_str)

        if not cleaned_val:
            return False

        # Exact substring match in cleaned text
        if cleaned_val in cleaned_source:
            return True

        # Token overlap match: if >70% of non-stopword tokens exist in source
        tokens = [t for t in cleaned_val.split() if len(t) > 2]
        if not tokens:
            return cleaned_val in cleaned_source

        found = sum(1 for t in tokens if t in cleaned_source)
        return (found / len(tokens)) >= 0.7

    def validate_and_ground(
        self,
        extracted_fields: Dict[str, Any],
        raw_source_text: str,
        required_fields: List[str]
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Validates extracted fields against raw source text.
        
        Returns:
            (grounded_record, is_valid)
            - If any required field is ungrounded or missing, returns (None, False).
            - Non-required ungrounded fields are replaced with None.
        """
        self.total_checked_records += 1
        grounded_data = dict(extracted_fields)

        for field, value in list(extracted_fields.items()):
            # Don't check internal or structural URLs if they are already source URLs
            if field in ("source_url", "date_method", "raw_extracted_text"):
                continue

            self.total_checked_fields += 1
            if not self.is_grounded(value, raw_source_text):
                logger.info(f"Ungrounded field '{field}' with value '{value}'. Nulling field.")
                grounded_data[field] = None
                self.total_nulled_fields += 1

        # Check required fields
        for req in required_fields:
            if not grounded_data.get(req):
                logger.warning(f"Record dropped due to missing/ungrounded required field: '{req}'.")
                self.total_dropped_records += 1
                return None, False

        return grounded_data, True

    def get_stats(self) -> Dict[str, Any]:
        nulled_pct = (
            (self.total_nulled_fields / self.total_checked_fields * 100.0)
            if self.total_checked_fields > 0 else 0.0
        )
        dropped_pct = (
            (self.total_dropped_records / self.total_checked_records * 100.0)
            if self.total_checked_records > 0 else 0.0
        )
        return {
            "total_checked_fields": self.total_checked_fields,
            "total_nulled_fields": self.total_nulled_fields,
            "nulled_percentage": round(nulled_pct, 2),
            "total_checked_records": self.total_checked_records,
            "total_dropped_records": self.total_dropped_records,
            "dropped_percentage": round(dropped_pct, 2),
        }


grounding_validator = GroundingValidator()
