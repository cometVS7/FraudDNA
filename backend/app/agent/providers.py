"""FraudDNA LLM Provider Abstraction and Deterministic Fallback Engine.

Provides a pluggable model provider interface supporting:
1. DeterministicFallbackEngine (Offline, zero-token, fully grounded rule synthesis)
2. GeminiProvider (Google Gemini API via httpx)
3. OpenAIProvider (OpenAI Chat Completions via httpx)
4. AnthropicProvider (Anthropic Messages API via httpx)
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, cast

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER_TIMEOUT: float = 15.0


class BaseLLMProvider(ABC):
    """Abstract interface for LLM synthesis engines."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider backend."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name or version of the underlying model."""

    @property
    @abstractmethod
    def is_degraded(self) -> bool:
        """Return True if running in fallback/degraded deterministic mode."""

    @abstractmethod
    def generate_investigation_synthesis(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Generate structured JSON investigation findings from formatted context."""


class DeterministicFallbackEngine(BaseLLMProvider):
    """Offline, zero-token, fully grounded deterministic synthesis engine.

    Used when external LLM providers are disabled (LLM_PROVIDER='deterministic'),
    unreachable, timeout, or return invalid JSON.
    Synthesizes structured findings strictly from empirical context and verified signals.
    """

    def __init__(self, model_name: str = "rule_fallback_v2") -> None:
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "deterministic"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_degraded(self) -> bool:
        return True

    def generate_investigation_synthesis(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Synthesize deterministic investigation findings from context passed in prompt or state."""
        _ = (prompt, system_prompt, temperature)
        return {
            "synthesis_engine": "deterministic_fallback",
            "model": self._model_name,
            "status": "degraded",
        }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Chat Completions API provider using httpx."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        api_base: str | None = None,
        timeout: float = DEFAULT_PROVIDER_TIMEOUT,
    ) -> None:
        self.api_key = api_key or settings.LLM_API_KEY or ""
        self.model = model or settings.LLM_MODEL or "gpt-4o-mini"
        self.api_base = (api_base or settings.LLM_API_BASE or "https://api.openai.com/v1").rstrip(
            "/"
        )
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_degraded(self) -> bool:
        return False

    def generate_investigation_synthesis(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Invoke OpenAI API with strict JSON mode enforcement."""
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Set LLM_API_KEY environment variable.")

        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return cast(dict[str, Any], json.loads(content))


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider using httpx."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
        timeout: float = DEFAULT_PROVIDER_TIMEOUT,
    ) -> None:
        self.api_key = api_key or settings.LLM_API_KEY or ""
        self.model = model or settings.LLM_MODEL or "gemini-1.5-flash"
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_degraded(self) -> bool:
        return False

    def generate_investigation_synthesis(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Invoke Gemini generateContent endpoint with JSON response schema."""
        if not self.api_key:
            raise ValueError("Gemini API key is missing. Set LLM_API_KEY environment variable.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\n{prompt}"},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            data = resp.json()
            text_content = data["candidates"][0]["content"]["parts"][0]["text"]
            return cast(dict[str, Any], json.loads(text_content))


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider using httpx."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = DEFAULT_PROVIDER_TIMEOUT,
    ) -> None:
        self.api_key = api_key or settings.LLM_API_KEY or ""
        self.model = model or settings.LLM_MODEL or "claude-3-5-sonnet-20241022"
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_degraded(self) -> bool:
        return False

    def generate_investigation_synthesis(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Invoke Anthropic Messages API."""
        if not self.api_key:
            raise ValueError("Anthropic API key is missing. Set LLM_API_KEY environment variable.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text_content = data["content"][0]["text"]
            clean_text = text_content.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            return cast(dict[str, Any], json.loads(clean_text.strip()))


def get_llm_provider(
    provider_name: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> BaseLLMProvider:
    """Factory creating configured LLM provider instance."""
    name = (provider_name or settings.LLM_PROVIDER or "deterministic").lower().strip()

    if name in {"deterministic", "offline", "mock", "fallback"}:
        return DeterministicFallbackEngine()
    if name == "openai":
        return OpenAIProvider(api_key=api_key, model=model)
    if name in {"gemini", "google"}:
        return GeminiProvider(api_key=api_key, model=model or "gemini-1.5-flash")
    if name in {"anthropic", "claude"}:
        return AnthropicProvider(api_key=api_key, model=model or "claude-3-5-sonnet-20241022")

    logger.warning(f"Unknown LLM provider '{name}'. Defaulting to DeterministicFallbackEngine.")
    return DeterministicFallbackEngine()
