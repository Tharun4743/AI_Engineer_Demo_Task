import pytest
import asyncio
from typing import Optional, Dict, Any
from src.llm.orchestrator import LLMOrchestrator
from src.llm.providers import BaseLLMAdapter, LLMError


class MockProvider(BaseLLMAdapter):
    def __init__(self, name: str, behavior: str, response: str = ""):
        self._name = name
        self.behavior = behavior  # '429', '413', 'invalid_json', 'repairable_json', 'success'
        self.response = response
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> str:
        self.call_count += 1
        if self.behavior == "429":
            raise LLMError("Rate limit exceeded", status_code=429)
        elif self.behavior == "413":
            raise LLMError("Payload too large", status_code=413)
        elif self.behavior == "invalid_json":
            return "<<NON_JSON_CORRUPT_OUTPUT>>"
        elif self.behavior == "repairable_json":
            return "```json\n{\"extracted\": true, \"name\": \"Valid Output\"}\n```"
        elif self.behavior == "success":
            return self.response or '{"status": "ok"}'
        raise LLMError("Unknown error", status_code=500)


@pytest.mark.asyncio
async def test_429_backoff_jitter_failover():
    """Proves: 429 status triggers backoff with jitter and fails over to secondary provider."""
    p1 = MockProvider(name="rate_limited_provider", behavior="429")
    p2 = MockProvider(name="healthy_provider", behavior="success", response='{"resolved_by": "provider2"}')

    orchestrator = LLMOrchestrator(providers=[p1, p2])
    result = await orchestrator.execute_extraction("Prompt: {text}", "Source Text Input", max_retries_per_provider=2)

    assert result is not None
    assert result.get("resolved_by") == "provider2"
    assert p1.call_count == 2  # Proves retry with backoff was executed
    assert p2.call_count == 1  # Proves failover succeeded


@pytest.mark.asyncio
async def test_413_payload_halving_failover():
    """Proves: 413 status triggers payload halving and fails over or succeeds."""
    p1 = MockProvider(name="oversized_provider", behavior="413")
    p2 = MockProvider(name="healthy_provider", behavior="success", response='{"recovered": true}')

    orchestrator = LLMOrchestrator(providers=[p1, p2])
    long_text = "This is a long sentence repeated. " * 50
    result = await orchestrator.execute_extraction("Prompt: {text}", long_text, max_retries_per_provider=2)

    assert result is not None
    assert result.get("recovered") is True
    assert p1.call_count == 2
    assert p2.call_count == 1


@pytest.mark.asyncio
async def test_invalid_json_repair_and_failover():
    """Proves: invalid JSON attempts repair, and if unrepairable, fails over."""
    # Test repairable markdown JSON
    p_repair = MockProvider(name="markdown_json_provider", behavior="repairable_json")
    orchestrator1 = LLMOrchestrator(providers=[p_repair])
    res1 = await orchestrator1.execute_extraction("Prompt: {text}", "text")
    assert res1 is not None
    assert res1.get("name") == "Valid Output"

    # Test unrepairable JSON triggers failover
    p_broken = MockProvider(name="broken_json_provider", behavior="invalid_json")
    p_backup = MockProvider(name="backup_provider", behavior="success", response='{"backup": true}')
    orchestrator2 = LLMOrchestrator(providers=[p_broken, p_backup])
    res2 = await orchestrator2.execute_extraction("Prompt: {text}", "text")
    assert res2 is not None
    assert res2.get("backup") is True
    assert p_broken.call_count == 1
    assert p_backup.call_count == 1
