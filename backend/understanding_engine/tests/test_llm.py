"""Unit tests for LLM provider abstraction."""

import pytest
from understanding_engine.llm import (
    LLMTimeoutError,
    LLMUnavailableError,
    MockLLMProvider,
    OllamaProvider,
)


def test_mock_llm_provider_success() -> None:
    provider = MockLLMProvider()
    assert provider.is_available() is True
    assert provider.get_model_name() == "mock-llm"
    res = provider.generate("Analyze this block")
    assert "Electromagnetic Induction" in res


def test_mock_llm_provider_offline() -> None:
    provider = MockLLMProvider(is_online=False)
    assert provider.is_available() is False
    with pytest.raises(LLMUnavailableError, match="offline"):
        provider.generate("Analyze this block")


def test_mock_llm_provider_timeout() -> None:
    provider = MockLLMProvider(simulate_timeout=True)
    with pytest.raises(LLMTimeoutError, match="timeout"):
        provider.generate("Analyze this block")


def test_ollama_provider_configuration() -> None:
    # Verify Ollama provider interface without requiring live daemon
    provider = OllamaProvider(model="llama3.2", base_url="http://localhost:11434")
    assert provider.get_model_name() == "ollama/llama3.2"
    assert provider.base_url == "http://localhost:11434"
