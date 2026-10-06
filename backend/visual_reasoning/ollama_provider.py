"""Local Ollama VLM provider for open-weight vision models (e.g. Qwen2-VL, MiniCPM-V)."""

import base64
import json
import os
from typing import Any, Dict, Optional
import httpx

from .provider import BaseVLMProvider
from .schemas import DiagramType, VisualReasoningProposal


class OllamaVLMProvider(BaseVLMProvider):
    """Integrates local vision models running through Ollama."""

    def __init__(
        self,
        model_name: str = "qwen2-vl:2b",
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    def _encode_image_b64(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def generate_visual_proposal(
        self,
        image_path: str,
        prompt: str,
        ocr_context: Optional[str] = None,
    ) -> VisualReasoningProposal:
        """Sends image and analysis prompt to Ollama vision API."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Keyframe image not found at: {image_path}")

        img_b64 = self._encode_image_b64(image_path)

        system_instruction = (
            "You are a local classroom blackboard visual reasoning assistant. "
            "Analyze diagrams, circuits, plots, and layout structure in the image. "
            "Do NOT hallucinate text that is absent. Emit valid JSON matching the schema."
        )

        full_prompt = prompt
        if ocr_context:
            full_prompt += f"\n\nPre-extracted OCR text on board (do not contradict): {ocr_context}"

        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "system": system_instruction,
            "images": [img_b64],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code != 200:
                    raise RuntimeError(f"Ollama vision API error {res.status_code}: {res.text}")
                data = res.json()
                raw_text = data.get("response", "{}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to connect to local Ollama server at {self.base_url}: {str(e)}") from e

        try:
            parsed = json.loads(raw_text)
            dtype_str = parsed.get("diagram_type", "generic_diagram")
            try:
                dtype = DiagramType(dtype_str)
            except ValueError:
                dtype = DiagramType.GENERIC_DIAGRAM

            return VisualReasoningProposal(
                model_name=self.model_name,
                diagram_type=dtype,
                description=parsed.get("description", "Diagram analyzed."),
                entities_detected=parsed.get("entities_detected", []),
                relations_detected=parsed.get("relations_detected", []),
                visible_equations=parsed.get("visible_equations", []),
                confidence=float(parsed.get("confidence", 0.8)),
                raw_response=raw_text,
            )
        except json.JSONDecodeError:
            return VisualReasoningProposal(
                model_name=self.model_name,
                diagram_type=DiagramType.GENERIC_DIAGRAM,
                description=raw_text[:200],
                confidence=0.3,
                raw_response=raw_text,
            )
