import pytest
from src.resolver.entity_resolver import entity_resolver


def test_openai_resolution_variants():
    """Proves: 'OpenAI', 'OpenAI, Inc.', 'Open AI' -> 'OpenAI'."""
    variants = [
        "OpenAI",
        "OpenAI, Inc.",
        "Open AI",
        "OpenAI Inc",
        "OpenAI LLC",
        "openai"
    ]

    for variant in variants:
        canonical, log_entry = entity_resolver.resolve(variant, source_url="test")
        assert canonical == "OpenAI", f"Failed to resolve '{variant}' to 'OpenAI', got '{canonical}'"
        assert log_entry.canonical_name == "OpenAI"


def test_domain_based_resolution():
    canonical, log = entity_resolver.resolve("Random Entity Name", website_or_url="https://openai.com/blog", source_url="test")
    assert canonical == "OpenAI"
    assert log.method == "domain_exact"
    assert log.score == 1.0


def test_other_canonical_startups():
    canonical, _ = entity_resolver.resolve("Anthropic PBC", source_url="test")
    assert canonical == "Anthropic"

    canonical, _ = entity_resolver.resolve("Cohere AI", source_url="test")
    assert canonical == "Cohere"

    canonical, _ = entity_resolver.resolve("Mistral AI SAS", source_url="test")
    assert canonical == "Mistral AI"
