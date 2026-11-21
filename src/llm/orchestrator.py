import asyncio
import json
import re
import random
import time
from typing import List, Optional, Dict, Any
from src.llm.providers import BaseLLMAdapter, GeminiFlashAdapter, GroqLlamaAdapter, DeepSeekAdapter, LLMError
from src.llm.chunker import semantic_chunker
from src.core.logging import logger


class CircuitBreaker:
    """Circuit breaker for failing LLM inference endpoints."""

    def __init__(self, failure_threshold: int = 3, reset_timeout_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_seconds
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit Breaker tripped to OPEN ({self.failure_count} consecutive failures).")

    def is_available(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.monotonic() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF-OPEN"
                logger.info("Circuit Breaker transitioned to HALF-OPEN. Testing endpoint...")
                return True
            return False
        return True  # HALF-OPEN


class LLMOrchestrator:
    """LLM Orchestrator managing fallback chains, backoff + jitter, 413 halving, JSON repair, and circuit breakers."""

    def __init__(self, providers: Optional[List[BaseLLMAdapter]] = None):
        if providers:
            self.providers = providers
        else:
            self.providers = [
                GeminiFlashAdapter(),
                GroqLlamaAdapter(),
                DeepSeekAdapter(),
            ]
        self.breakers: Dict[str, CircuitBreaker] = {
            p.name: CircuitBreaker() for p in self.providers
        }

    def repair_json(self, raw_response: str) -> Optional[Dict[str, Any]]:
        """Cleans and repairs malformed LLM JSON strings."""
        if not raw_response:
            return None

        # 1. Direct parse attempt
        try:
            return json.loads(raw_response.strip())
        except Exception:
            pass

        # 2. Strip markdown code fences (```json ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_response.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        try:
            return json.loads(cleaned.strip())
        except Exception:
            pass

        # 3. Regex find first outermost JSON object
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except Exception:
                pass

        return None

    async def execute_extraction(
        self,
        prompt_template: str,
        source_text: str,
        max_retries_per_provider: int = 2
    ) -> Optional[Dict[str, Any]]:
        """Executes extraction through the provider chain with full fault-tolerance:
        - 429: Exponential backoff + jitter -> failover
        - 413: Payload halving -> failover
        - Invalid JSON: Repair -> failover
        """
        current_text = source_text

        for provider in self.providers:
            p_name = provider.name
            breaker = self.breakers.get(p_name)
            if breaker and not breaker.is_available():
                logger.info(f"Provider '{p_name}' circuit breaker is OPEN. Skipping to next provider.")
                continue

            for attempt in range(max_retries_per_provider):
                try:
                    prompt = prompt_template.format(text=current_text)
                    raw_result = await provider.generate(prompt)

                    # JSON parsing & repair
                    parsed = self.repair_json(raw_result)
                    if parsed is not None:
                        if breaker:
                            breaker.record_success()
                        return parsed

                    # Invalid JSON that could not be repaired
                    logger.warning(f"Provider '{p_name}' returned unrepairable JSON: {raw_result[:100]}... Failing over.")
                    if breaker:
                        breaker.record_failure()
                    break  # Failover to next provider

                except LLMError as err:
                    if err.status_code == 429:
                        # 429 -> backoff + jitter -> failover
                        backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                        logger.warning(f"429 Rate limited on '{p_name}'. Backing off {backoff:.2f}s...")
                        await asyncio.sleep(backoff)
                        if attempt == max_retries_per_provider - 1:
                            if breaker:
                                breaker.record_failure()
                            break  # Failover
                        continue

                    elif err.status_code == 413:
                        # 413 -> payload halving -> failover
                        logger.warning(f"413 Payload Too Large on '{p_name}'. Halving payload and retrying...")
                        current_text = semantic_chunker.halve_payload(current_text)
                        if attempt == max_retries_per_provider - 1:
                            if breaker:
                                breaker.record_failure()
                            break  # Failover
                        continue

                    else:
                        logger.error(f"Provider '{p_name}' failed with status {err.status_code}: {err}")
                        if breaker:
                            breaker.record_failure()
                        break  # Failover to next provider

                except Exception as e:
                    logger.error(f"Unexpected error with provider '{p_name}': {e}")
                    if breaker:
                        breaker.record_failure()
                    break  # Failover to next provider

        logger.warning("All LLM providers exhausted without successful extraction.")
        return None


llm_orchestrator = LLMOrchestrator()
