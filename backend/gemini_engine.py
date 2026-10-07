"""Gemini Multimodal Intelligence Engine for GyanDrishti.

Features:
1. Thread-safe Multi-Key Pool with automatic round-robin and 429 rate-limit fallback.
2. Step 3: Deep chalkboard vision analysis, handwritten LaTeX OCR, teacher/board detection, and diagram extraction.
3. Step 4: Multimodal temporal alignment fusing speech and visual chalkboard actions.
4. Step 5: Pedagogical notes and exam question synthesis with Mermaid diagrams in cooperation with local Llama.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
]


class GeminiKeyPool:
    """Manages a pool of Gemini API keys with round-robin rotation, thread safety,
    and automatic failover when Free-Tier rate limits (429) or errors are encountered.
    """

    def __init__(
        self,
        keys: Optional[List[str]] = None,
        api_keys: Optional[List[str]] = None,
        pacing_delay_sec: float = 0.5,
        default_cooldown_sec: float = 65.0,
        **kwargs: Any
    ) -> None:
        self._lock = threading.Lock()
        self._keys: List[str] = []
        self._index = 0
        self._exhausted_until: Dict[str, float] = {}  # key -> timestamp when it can be retried
        self.pacing_delay_sec = pacing_delay_sec
        self.default_cooldown_sec = default_cooldown_sec

        init_keys = keys or api_keys
        if init_keys:
            self.set_keys(init_keys)
        else:
            # Check environment variables
            env_keys = os.environ.get("GEMINI_API_KEYS", "") or os.environ.get("GEMINI_API_KEY", "")
            if env_keys:
                self.set_keys([k.strip() for k in re.split(r"[,;\n\s]+", env_keys) if k.strip()])

    @property
    def rate_limited_until(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._exhausted_until)

    def set_keys(self, keys: List[str]) -> None:
        with self._lock:
            cleaned = [k.strip() for k in keys if k and k.strip()]
            self._keys = list(dict.fromkeys(cleaned))  # unique, preserve order
            self._index = 0
            self._exhausted_until.clear()
            logger.info("GeminiKeyPool loaded with %d key(s)", len(self._keys))

    def add_keys(self, new_keys: List[str]) -> None:
        with self._lock:
            existing = set(self._keys)
            for k in new_keys:
                k_clean = k.strip()
                if k_clean and k_clean not in existing:
                    self._keys.append(k_clean)
                    existing.add(k_clean)

    def has_keys(self) -> bool:
        with self._lock:
            return len(self._keys) > 0

    def get_key_count(self) -> int:
        with self._lock:
            return len(self._keys)

    def get_next_key(self) -> Optional[str]:
        """Gets next available non-rate-limited key from pool."""
        with self._lock:
            if not self._keys:
                return None

            now = time.time()
            total = len(self._keys)

            # Try to find a key not in rate-limit cooldown
            for _ in range(total):
                key = self._keys[self._index % total]
                self._index = (self._index + 1) % total
                cooldown = self._exhausted_until.get(key, 0.0)
                if now >= cooldown:
                    return key

            # If all are in cooldown, return the one whose cooldown expires soonest
            soonest_key = min(self._keys, key=lambda k: self._exhausted_until.get(k, 0.0))
            return soonest_key

    def mark_rate_limited(self, key: str, cooldown_seconds: Optional[float] = None) -> None:
        cooldown = cooldown_seconds if cooldown_seconds is not None else self.default_cooldown_sec
        with self._lock:
            self._exhausted_until[key] = time.time() + cooldown
            logger.warning(
                "Gemini key ending in '...%s' marked rate-limited for %ds. Total keys: %d",
                key[-6:] if len(key) >= 6 else key,
                int(cooldown),
                len(self._keys)
            )

    def execute_with_failover(
        self,
        api_callable: Any,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Executes a Gemini API function, automatically rotating keys on 429 / quota failure."""
        with self._lock:
            total_keys = len(self._keys)

        if total_keys == 0:
            raise ValueError("No Gemini API keys configured.")

        attempts = max(1, total_keys * 2)
        last_error = None

        for attempt in range(attempts):
            key = self.get_next_key()
            if not key:
                break

            try:
                # Add slight delay between requests to remain comfortably within 15 RPM Free Tier
                if self.pacing_delay_sec > 0:
                    time.sleep(self.pacing_delay_sec)
                return api_callable(key, *args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = (
                    "429" in err_str or
                    "quota" in err_str or
                    "resource_exhausted" in err_str or
                    "too many requests" in err_str
                )

                if is_rate_limit:
                    self.mark_rate_limited(key, cooldown_seconds=self.default_cooldown_sec)
                    last_error = e
                    logger.info("Attempt %d: rotating to next Gemini API key after 429", attempt + 1)
                    continue
                else:
                    logger.error("Gemini API call failed with non-rate-limit error: %s", e)
                    last_error = e
                    if "invalid_argument" in err_str or "api_key_invalid" in err_str or "permission_denied" in err_str:
                        self.mark_rate_limited(key, cooldown_seconds=86400.0)
                        continue
                    raise

        raise RuntimeError(f"All Gemini API keys in pool were exhausted or failed. Last error: {last_error}")

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            rate_limited = sum(1 for exp in self._exhausted_until.values() if exp > now)
            return {
                "total_keys": len(self._keys),
                "active_keys": max(0, len(self._keys) - rate_limited),
                "rate_limited_keys": rate_limited
            }


def clean_json_markdown(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return cleaned


def extract_mermaid_blocks(text: str) -> List[str]:
    pattern = r"```(?:mermaid)?\s*([\s\S]*?)```"
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    results = []
    for m in matches:
        stripped = m.strip()
        if any(keyword in stripped for keyword in ["graph ", "flowchart ", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram"]):
            results.append(stripped)
    return results


# Global default key pool instance
gemini_pool = GeminiKeyPool()


def _call_gemini_rest_api(
    api_key: str,
    contents: List[Dict[str, Any]],
    system_instruction: Optional[str] = None,
    model: str = "gemini-1.5-flash",
    timeout: float = 45.0,
) -> Dict[str, Any]:
    """Direct REST caller for Gemini 1.5/2.0 API using httpx."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    generation_config: Dict[str, Any] = {
        "temperature": 0.2,
        "maxOutputTokens": 4096,
        "responseMimeType": "application/json"
    }

    body: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": generation_config,
    }

    if system_instruction:
        body["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=body)
        if resp.status_code == 429:
            raise RuntimeError(f"Gemini 429 Rate Limit hit: {resp.text}")
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"No candidates in Gemini response: {data}")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Empty parts in Gemini response candidate")

        text_content = parts[0].get("text", "")
        try:
            return json.loads(text_content)
        except json.JSONDecodeError:
            cleaned = re.sub(r"^```json\s*", "", text_content.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned.strip())
            return json.loads(cleaned)


# -------------------------------------------------------------------------
# Step 3: Chalkboard & Boardwork Vision Analysis with Gemini
# -------------------------------------------------------------------------

def analyze_chalkboard_frame_with_gemini(
    image_path: Path,
    timestamp: float,
    api_key: Optional[str] = None,
    key_pool: Optional[GeminiKeyPool] = None,
) -> Dict[str, Any]:
    """Uses Gemini 1.5 Multimodal Vision to inspect a classroom frame.

    Extracts:
    1. Teacher presence & bounding box
    2. Chalkboard/Whiteboard presence & state
    3. Handwritten chalkboard notes & text
    4. Complex mathematical formulas (transcribed into clean LaTeX)
    5. Diagrams (circuits, geometry, flowcharts, graphs) with Mermaid/ASCII specifications
    """
    image_path = Path(image_path)
    if not image_path.exists():
        return {
            "teacher_present": False,
            "board_present": True,
            "chalkboard_text": [],
            "equations": [],
            "diagrams": []
        }

    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    prompt = (
        "You are an expert computer vision intelligence agent analyzing classroom lecture boardwork keyframes.\n"
        "Examine this frame carefully and extract:\n"
        "1. Teacher Presence: Is the instructor/teacher visible in the frame?\n"
        "2. Chalkboard/Whiteboard Presence: Is the board visible?\n"
        "3. Boardwork Content: Transcribe all handwritten chalkboard or whiteboard text, labels, and notes.\n"
        "4. Mathematical Equations: Extract every mathematical formula or relation as clean LaTeX ($...$).\n"
        "5. Diagrams: Detect any visual diagrams (electrical circuits, geometry, graphs, schematics, free-body diagrams). For each diagram, provide a descriptive summary and clean Mermaid diagram code (or structured ASCII description).\n"
        "\nReturn pure valid JSON matching this schema:\n"
        "{\n"
        '  "teacher_present": true,\n'
        '  "board_present": true,\n'
        '  "chalkboard_text": ["text line 1", "text line 2"],\n'
        '  "equations": [\n'
        '    {"latex": "I = \\\\frac{V}{R}", "explanation": "Ohm\'s law formula"}\n'
        '  ],\n'
        '  "diagrams": [\n'
        '    {\n'
        '      "name": "DC Resistive Circuit",\n'
        '      "description": "Battery connected in series with a resistor R and ground",\n'
        '      "diagram_type": "circuit",\n'
        '      "mermaid_code": "graph LR; V[Voltage Source] --> R[Resistor R] --> GND[Ground]"\n'
        '    }\n'
        '  ],\n'
        '  "summary": "Brief 1-sentence summary of what is shown on the board at this timestamp"\n'
        "}"
    )

    contents = [
        {
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": img_b64
                    }
                }
            ]
        }
    ]

    pool = key_pool or gemini_pool

    def _caller(key: str) -> Dict[str, Any]:
        return _call_gemini_rest_api(
            api_key=key,
            contents=contents,
            system_instruction="You are an expert pedagogical vision analyst. Always return pure JSON.",
            model="gemini-1.5-flash",
            timeout=30.0
        )

    if api_key:
        return _caller(api_key)
    elif pool.has_keys():
        return pool.execute_with_failover(_caller)
    else:
        raise ValueError("No Gemini API key available.")


# -------------------------------------------------------------------------
# Step 4: Multimodal Temporal Alignment with Gemini
# -------------------------------------------------------------------------

def align_multimodal_with_gemini(
    speech_segments: List[Dict[str, Any]],
    visual_events: List[Dict[str, Any]],
    lecture_title: str,
    api_key: Optional[str] = None,
    key_pool: Optional[GeminiKeyPool] = None,
) -> Dict[str, Any]:
    """Uses Gemini to correlate what was spoken with what was visually drawn on the chalkboard at each timestamp."""
    prompt = (
        f"You are analyzing multimodal classroom evidence for the lecture '{lecture_title}'.\n"
        f"Spoken Speech Segments with timestamps:\n{json.dumps(speech_segments, indent=2)}\n\n"
        f"Chalkboard Keyframe Visual Events with timestamps:\n{json.dumps(visual_events, indent=2)}\n\n"
        "Align spoken speech and visual chalkboard actions temporally. Identify:\n"
        "1. Spoken references that explain or point to chalkboard text/equations.\n"
        "2. Visual equations verified by speech.\n"
        "3. Any discrepancies where spoken explanation differed from chalkboard writing.\n"
        "\nReturn pure valid JSON:\n"
        "{\n"
        '  "aligned_timeline": [\n'
        '    {\n'
        '      "timestamp": 0.0,\n'
        '      "event_type": "multimodal_supported",\n'
        '      "speech_snippet": "...",\n'
        '      "visual_snippet": "...",\n'
        '      "correlation_insight": "Teacher explained formula while writing on board"\n'
        '    }\n'
        '  ],\n'
        '  "grounding_confidence": 0.98,\n'
        '  "summary": "Overall multimodal alignment summary"\n'
        "}"
    )

    contents = [{"parts": [{"text": prompt}]}]
    pool = key_pool or gemini_pool

    def _caller(key: str) -> Dict[str, Any]:
        return _call_gemini_rest_api(
            api_key=key,
            contents=contents,
            system_instruction="You are a multimodal temporal reasoning engine. Return pure valid JSON.",
            model="gemini-1.5-flash",
            timeout=30.0
        )

    if api_key:
        return _caller(api_key)
    elif pool.has_keys():
        return pool.execute_with_failover(_caller)
    else:
        raise ValueError("No Gemini API key available.")


# -------------------------------------------------------------------------
# Step 5: Pedagogical Notes & Questions Synthesis with Diagrams
# -------------------------------------------------------------------------

def synthesize_lecture_notes_with_gemini(
    lecture_title: str,
    subject: str,
    duration: float,
    speech_segments: List[Dict[str, Any]],
    visual_events: List[Dict[str, Any]],
    extracted_diagrams: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    key_pool: Optional[GeminiKeyPool] = None,
) -> Dict[str, Any]:
    """Generates structured pedagogical lecture notes with diagrams using Gemini."""
    prompt = (
        f"Create comprehensive, pedagogically structured classroom lecture notes for:\n"
        f"Title: {lecture_title}\n"
        f"Subject Domain: {subject}\n"
        f"Duration: {round(duration, 1)} seconds\n\n"
        f"Spoken Transcript:\n{json.dumps(speech_segments, indent=2)}\n\n"
        f"Chalkboard Visual Elements & Equations:\n{json.dumps(visual_events, indent=2)}\n\n"
        f"Visual Diagrams Detected:\n{json.dumps(extracted_diagrams or [], indent=2)}\n\n"
        "Synthesize high-quality pedagogical notes including:\n"
        "1. Core Concepts (title and detailed explanation with grounding evidence)\n"
        "2. Formal Definitions of key terms\n"
        "3. Mathematical Equations (clean LaTeX and physical explanation)\n"
        "4. Key Takeaways & Exam Points\n"
        "5. Revision Questions with Expected Model Answers\n"
        "6. Pedagogical Diagrams: Include at least one or two clean Mermaid diagrams (e.g. concept flowchart, circuit diagram, or relationship map) and detailed diagram explanations!\n"
        "\nReturn pure valid JSON:\n"
        "{\n"
        '  "topic": "...",\n'
        '  "overview": "Detailed 2-3 paragraph summary of the lecture",\n'
        '  "concepts": [\n'
        '    {"name": "...", "explanation": "...", "timestamp": 0.0}\n'
        '  ],\n'
        '  "definitions": [\n'
        '    {"term": "...", "definition": "...", "timestamp": 0.0}\n'
        '  ],\n'
        '  "equations": [\n'
        '    {"name": "...", "latex": "...", "representation": "...", "explanation": "...", "timestamp": 0.0}\n'
        '  ],\n'
        '  "diagrams": [\n'
        '    {\n'
        '      "title": "Circuit & Mathematical Relationship",\n'
        '      "description": "Visual diagram illustrating the connection between elements",\n'
        '      "mermaid_code": "graph TD; A[Input Voltage] --> B[Current I] --> C[Output Ground]"\n'
        '    }\n'
        '  ],\n'
        '  "important_points": [\n'
        '    {"point": "...", "importance": "high"}\n'
        '  ],\n'
        '  "revision_questions": [\n'
        '    {"question": "...", "expected_answer": "...", "difficulty": "medium"}\n'
        '  ],\n'
        '  "grounding_score": 0.98\n'
        "}"
    )

    contents = [{"parts": [{"text": prompt}]}]
    pool = key_pool or gemini_pool

    def _caller(key: str) -> Dict[str, Any]:
        return _call_gemini_rest_api(
            api_key=key,
            contents=contents,
            system_instruction="You are an elite professor and pedagogical notes creator. Synthesize rigorous, clear notes with equations, definitions, questions, and Mermaid diagrams. Always output pure JSON.",
            model="gemini-1.5-flash",
            timeout=40.0
        )

    if api_key:
        return _caller(api_key)
    elif pool.has_keys():
        return pool.execute_with_failover(_caller)
    else:
        raise ValueError("No Gemini API key available.")
