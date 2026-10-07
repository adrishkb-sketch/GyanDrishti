"""LLM Provider abstraction for GyanDrishti Understanding Engine.

Enables seamless switching between local open-weight runtimes (Ollama, local llama.cpp server,
or mock providers) with zero reliance on paid external APIs or proprietary keys.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMUnavailableError(LLMError):
    """Raised when the local LLM runtime is offline or unreachable."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when the local LLM runtime exceeds its response timeout."""
    pass


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        """Generates raw text completion from the model.

        Args:
            prompt: User / input prompt text.
            system_prompt: Optional system instruction prompt.
            temperature: Sampling temperature (low default 0.1 for deterministic JSON).

        Returns:
            Raw response text from the model.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the local runtime is running and responsive."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the identifier of the configured model."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Local open-weight LLM provider using Ollama HTTP API (http://localhost:11434)."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _resolve_model(self) -> str:
        """Resolves model tag against available local models in Ollama."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    if self.model in models:
                        return self.model
                    for m in models:
                        if m.startswith(self.model) or self.model.startswith(m.split(":")[0]):
                            return m
        except Exception:
            pass
        return self.model

    def get_model_name(self) -> str:
        return f"ollama/{self.model}"

    def is_available(self) -> bool:
        """Checks if Ollama daemon is running locally and has models available."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = res.json().get("models", [])
                    return len(models) > 0
                return False
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        active_model = self._resolve_model()
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": active_model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 1024,
                "num_ctx": 4096,
            },
            "format": "json",  # Instruct Ollama to output valid JSON
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                if response.status_code != 200:
                    raise LLMError(f"Ollama returned HTTP {response.status_code}: {response.text}")
                data = response.json()
                return data.get("response", "")
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Ollama request timed out after {self.timeout}s: {e}") from e
        except httpx.ConnectError as e:
            raise LLMUnavailableError(f"Could not connect to Ollama at {self.base_url}: {e}") from e
        except Exception as e:
            raise LLMError(f"Ollama generation failed: {e}") from e


class LocalHTTPProvider(BaseLLMProvider):
    """Provider for OpenAI-compatible local runtimes (llama.cpp server, vLLM, LM Studio)."""

    def __init__(
        self,
        model: str = "local-model",
        base_url: str = "http://localhost:8000/v1",
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_model_name(self) -> str:
        return f"local-http/{self.model}"

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                if response.status_code != 200:
                    raise LLMError(f"Local HTTP provider returned {response.status_code}: {response.text}")
                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise LLMError("No completion choices returned by local runtime")
                return choices[0]["message"]["content"]
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Request timed out after {self.timeout}s: {e}") from e
        except httpx.ConnectError as e:
            raise LLMUnavailableError(f"Could not connect to local server at {self.base_url}: {e}") from e
        except Exception as e:
            raise LLMError(f"Local HTTP generation failed: {e}") from e


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for unit testing and offline development."""

    def __init__(
        self,
        model_name: str = "mock-llm",
        response_generator: Optional[Callable[[str], str]] = None,
        is_online: bool = True,
        simulate_timeout: bool = False,
    ) -> None:
        self.model_name = model_name
        self.response_generator = response_generator
        self.is_online = is_online
        self.simulate_timeout = simulate_timeout

    def get_model_name(self) -> str:
        return self.model_name

    def is_available(self) -> bool:
        return self.is_online

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        if not self.is_online:
            raise LLMUnavailableError("Mock LLM is offline")
        if self.simulate_timeout:
            raise LLMTimeoutError("Mock LLM simulated timeout")

        if self.response_generator:
            return self.response_generator(prompt)

        # Default minimal valid structured JSON response
        return """{
            "topic": "Electromagnetic Induction and Current Dynamics",
            "concepts": [
                {
                    "name": "Inverse Current-Resistance Relationship",
                    "explanation": "Current increases when resistance decreases under constant voltage.",
                    "timestamp_start": 10.0,
                    "timestamp_end": 14.0
                }
            ],
            "definitions": [
                {
                    "term": "Current",
                    "definition": "The rate of flow of electric charge through a conductor.",
                    "timestamp": 10.2
                }
            ],
            "equations": [
                {
                    "latex_or_text": "I = V / R",
                    "description": "Ohm's Law relating current, voltage, and resistance",
                    "timestamp": 12.5,
                    "explicitly_spoken": true
                }
            ],
            "important_points": [
                {
                    "point": "Current increases as resistance decreases under constant voltage.",
                    "timestamp_start": 10.0,
                    "timestamp_end": 14.0,
                    "importance": "high"
                }
            ],
            "visual_references": [
                {
                    "timestamp": 11.3,
                    "source": "camera",
                    "event_type": "keyframe",
                    "frame_path": "output_frames/f1.jpg",
                    "relevance": "Instructor pointed to circuit diagram on board while discussing current increase."
                }
            ],
            "question_candidates": [
                {
                    "question": "What happens to the current in a circuit when resistance is reduced?",
                    "expected_answer": "The current increases assuming voltage is held constant.",
                    "difficulty": "easy",
                    "relevant_timestamp": 11.0
                }
            ],
            "confidence": 0.95
        }"""
