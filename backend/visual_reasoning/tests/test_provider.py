"""Tests for VLM providers and structured outputs."""

import pytest
from visual_reasoning.provider import BaseVLMProvider, MockVLMProvider
from visual_reasoning.schemas import DiagramType, VisualReasoningProposal


def test_1_provider_interface():
    """Requirement 1: provider interface is an abstract contract."""
    assert issubclass(MockVLMProvider, BaseVLMProvider)


def test_2_mock_provider():
    """Requirement 2: mock provider returns deterministic output."""
    provider = MockVLMProvider()
    proposal = provider.generate_visual_proposal("frame.jpg", "Analyze this")
    assert provider.invocation_count == 1
    assert proposal.model_name == "mock-vlm-2b"
    assert proposal.diagram_type == DiagramType.CIRCUIT_DIAGRAM


def test_3_valid_structured_output():
    """Requirement 3: structured output adheres to Pydantic schema."""
    proposal = VisualReasoningProposal(
        model_name="qwen2-vl:2b",
        diagram_type=DiagramType.CIRCUIT_DIAGRAM,
        description="Circuit with series resistor and capacitor.",
        entities_detected=["Resistor", "Capacitor"],
        relations_detected=["Connected in series"],
        visible_equations=["i(t) = C * dv/dt"],
        confidence=0.89,
    )
    dumped = proposal.model_dump()
    assert dumped["diagram_type"] == "circuit_diagram"
    assert len(dumped["entities_detected"]) == 2
    assert dumped["confidence"] == 0.89


def test_4_malformed_output():
    """Requirement 4: malformed output does not crash provider."""
    provider = MockVLMProvider(malformed_json=True)
    proposal = provider.generate_visual_proposal("frame.jpg", "Analyze this")
    assert proposal.confidence == 0.1
    assert "Invalid" in proposal.raw_response


def test_12_no_network_dependency(monkeypatch):
    """Requirement 12: no network access is needed for local mock provider."""
    import socket

    def guarded_connect(*args, **kwargs):
        raise RuntimeError("Network attempted during offline VLM execution!")

    monkeypatch.setattr(socket, "socket", guarded_connect)
    provider = MockVLMProvider()
    res = provider.generate_visual_proposal("frame.jpg", "Analyze")
    assert res.diagram_type == DiagramType.CIRCUIT_DIAGRAM
