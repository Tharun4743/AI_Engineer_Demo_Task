from src.extraction.validator import GroundingValidator


def test_grounding_validation_success():
    validator = GroundingValidator()
    source_text = "Acme AI was founded in 2023 in San Francisco by Jane Doe. Website is acme.ai."
    extracted = {
        "name": "Acme AI",
        "website": "acme.ai",
        "year": "2023",
        "description": "Acme AI in San Francisco"
    }

    grounded, is_valid = validator.validate_and_ground(extracted, source_text, required_fields=["name", "website"])
    assert is_valid is True
    assert grounded["name"] == "Acme AI"
    assert grounded["year"] == "2023"


def test_ungrounded_field_is_nulled():
    validator = GroundingValidator()
    source_text = "Acme AI is an artificial intelligence startup in San Francisco."
    extracted = {
        "name": "Acme AI",
        "website": "acme.ai",  # Not in source text
        "funding": "$50 million Series B",  # Complete hallucination
    }

    grounded, is_valid = validator.validate_and_ground(extracted, source_text, required_fields=["name"])
    assert is_valid is True
    assert grounded["name"] == "Acme AI"
    assert grounded["funding"] is None  # Hallucinated field was nulled!


def test_missing_required_field_drops_record():
    validator = GroundingValidator()
    source_text = "An unnamed company launched an AI model today."
    extracted = {
        "name": "Imaginary Startup Corp",  # Ungrounded required field
        "model": "AI Model"
    }

    grounded, is_valid = validator.validate_and_ground(extracted, source_text, required_fields=["name"])
    assert is_valid is False
    assert grounded is None
