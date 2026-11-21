import os
import json
import aiohttp
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.core.logging import logger


class LLMError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class BaseLLMAdapter(ABC):
    """Common interface for LLM inference providers."""

    @abstractmethod
    async def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> str:
        """Generates completion text from prompt."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class GeminiFlashAdapter(BaseLLMAdapter):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    @property
    def name(self) -> str:
        return "gemini_flash"

    async def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> str:
        if not self.api_key:
            raise LLMError("Gemini API key is not configured.", status_code=401)

        url = f"{self.endpoint}?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=20) as resp:
                if resp.status == 429:
                    raise LLMError("Gemini Rate Limit Exceeded", status_code=429)
                if resp.status == 413:
                    raise LLMError("Gemini Payload Too Large", status_code=413)
                if resp.status != 200:
                    text = await resp.text()
                    raise LLMError(f"Gemini API returned status {resp.status}: {text}", status_code=resp.status)

                data = await resp.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    raise LLMError("Gemini response missing expected candidate parts", status_code=502)


class GroqLlamaAdapter(BaseLLMAdapter):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def name(self) -> str:
        return "groq_llama3"

    async def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> str:
        if not self.api_key:
            raise LLMError("Groq API key is not configured.", status_code=401)

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload, timeout=20) as resp:
                if resp.status == 429:
                    raise LLMError("Groq Rate Limit Exceeded", status_code=429)
                if resp.status == 413:
                    raise LLMError("Groq Payload Too Large", status_code=413)
                if resp.status != 200:
                    text = await resp.text()
                    raise LLMError(f"Groq API returned status {resp.status}: {text}", status_code=resp.status)

                data = await resp.json()
                return data["choices"][0]["message"]["content"]


class DeepSeekAdapter(BaseLLMAdapter):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.endpoint = "https://api.deepseek.com/chat/completions"

    @property
    def name(self) -> str:
        return "deepseek_chat"

    async def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> str:
        if not self.api_key:
            raise LLMError("DeepSeek API key is not configured.", status_code=401)

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload, timeout=20) as resp:
                if resp.status == 429:
                    raise LLMError("DeepSeek Rate Limit Exceeded", status_code=429)
                if resp.status == 413:
                    raise LLMError("DeepSeek Payload Too Large", status_code=413)
                if resp.status != 200:
                    text = await resp.text()
                    raise LLMError(f"DeepSeek API returned status {resp.status}: {text}", status_code=resp.status)

                data = await resp.json()
                return data["choices"][0]["message"]["content"]
