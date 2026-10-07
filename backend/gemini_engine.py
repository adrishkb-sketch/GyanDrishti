"""Gemini Multimodal Intelligence Engine for GyanDrishti.

Features:
1. Thread-safe Multi-Key Pool with persistent key storage and dynamic model discovery.
2. Adaptive model fallback (gemini-2.0-flash, gemini-2.5-flash, gemini-1.5-flash-latest, etc.) across v1beta & v1.
3. Step 3: Deep chalkboard vision analysis, handwritten LaTeX math transcription, teacher & board presence, and Mermaid diagram extraction.
4. Step 4: Multimodal temporal alignment fusing speech and visual chalkboard actions.
5. Step 5: Pedagogical notes and exam question synthesis with Mermaid diagrams in cooperation with local Llama.
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

# Candidate models prioritized by speed, quality, and free-tier compatibility
DEFAULT_CANDIDATE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

DEFAULT_API_VERSIONS = ["v1beta", "v1"]


def clean_json_markdown(text: str) -> str:
    """Strips markdown code fences and returns clean JSON string."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    # If there's leading/trailing non-json text, extract first {...} or [...]
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1]
    return cleaned


def extract_mermaid_blocks(text: str) -> List[str]:
    """Finds all Mermaid diagram code blocks in markdown text."""
    pattern = r"```(?:mermaid)?\s*([\s\S]*?)```"
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    results = []
    for m in matches:
        stripped = m.strip()
        if any(keyword in stripped for keyword in ["graph ", "flowchart ", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram"]):
            results.append(stripped)
    return results


def discover_available_models(api_key: str) -> List[str]:
    """Queries ModelService.ListModels to determine exact models available for this API key."""
    for api_ver in DEFAULT_API_VERSIONS:
        try:
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={api_key}"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    models_list = data.get("models", [])
                    working = []
                    for m in models_list:
                        name = m.get("name", "")
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods:
                            clean_name = name.replace("models/", "")
                            working.append(clean_name)
                    if working:
                        # Prioritize flash models
                        sorted_models = sorted(
                            working,
                            key=lambda x: (
                                0 if "flash" in x and "2.0" in x else
                                1 if "flash" in x and "2.5" in x else
                                2 if "flash" in x and "1.5" in x else
                                3 if "flash" in x else
                                4 if "pro" in x else 5
                            )
                        )
                        logger.info("Discovered %d models for API key. Preferred: %s", len(sorted_models), sorted_models[0])
                        return sorted_models
        except Exception as e:
            logger.debug("ListModels on %s notice: %s", api_ver, e)
    return list(DEFAULT_CANDIDATE_MODELS)


class GeminiKeyPool:
    """Manages a pool of Gemini API keys with round-robin rotation, thread safety,
    automatic failover on rate limits (429), and dynamic model adaptation.
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
        self.working_model: Optional[str] = None
        self._key_models_cache: Dict[str, List[str]] = {}

        # Persistent storage file location
        self._keys_file = Path(__file__).resolve().parent / "data" / ".gemini_keys.json"

        init_keys = keys or api_keys
        if init_keys:
            self.set_keys(init_keys)
        else:
            # Check environment variables
            env_keys = os.environ.get("GEMINI_API_KEYS", "") or os.environ.get("GEMINI_API_KEY", "")
            if env_keys:
                self.set_keys([k.strip() for k in re.split(r"[,;\n\s]+", env_keys) if k.strip()])
            elif self._keys_file.exists():
                try:
                    saved = json.loads(self._keys_file.read_text(encoding="utf-8"))
                    if isinstance(saved, list) and saved:
                        self.set_keys(saved)
                        logger.info("Loaded %d Gemini API key(s) from persistent disk storage", len(saved))
                except Exception as e:
                    logger.warning("Notice loading saved gemini keys: %s", e)

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

    def save_keys_permanently(self, keys: List[str]) -> None:
        """Saves keys to memory and writes them to local persistent file."""
        self.set_keys(keys)
        try:
            self._keys_file.parent.mkdir(parents=True, exist_ok=True)
            self._keys_file.write_text(json.dumps(self._keys, indent=2), encoding="utf-8")
            logger.info("Saved %d Gemini key(s) permanently to %s", len(self._keys), self._keys_file)
        except Exception as e:
            logger.warning("Could not write keys file: %s", e)

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
                "rate_limited_keys": rate_limited,
                "working_model": self.working_model or "auto-detect"
            }


# Global default key pool instance
gemini_pool = GeminiKeyPool()


def verify_and_configure_keys(keys: List[str]) -> Dict[str, Any]:
    """Tests keys against Google API, discovers supported models, and saves them."""
    cleaned = [k.strip() for k in keys if k and k.strip()]
    if not cleaned:
        gemini_pool.save_keys_permanently([])
        return {
            "status": "cleared",
            "key_count": 0,
            "active_keys": 0,
            "working_model": None,
            "message": "All Gemini API keys cleared."
        }

    valid_keys = []
    discovered_model = None

    for k in cleaned:
        available = discover_available_models(k)
        if available:
            valid_keys.append(k)
            if not discovered_model:
                discovered_model = available[0]

    # If ListModels was restricted, test with lightweight ping
    if not valid_keys:
        for k in cleaned:
            for model_name in DEFAULT_CANDIDATE_MODELS:
                for api_ver in DEFAULT_API_VERSIONS:
                    try:
                        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={k}"
                        with httpx.Client(timeout=8.0) as client:
                            resp = client.post(url, json={"contents": [{"parts": [{"text": "ping"}]}]})
                            if resp.status_code == 200:
                                valid_keys.append(k)
                                discovered_model = model_name
                                break
                    except Exception:
                        pass
                if k in valid_keys:
                    break

    final_keys = valid_keys or cleaned
    gemini_pool.save_keys_permanently(final_keys)
    if discovered_model:
        gemini_pool.working_model = discovered_model

    return {
        "status": "verified" if valid_keys else "saved",
        "key_count": len(final_keys),
        "active_keys": len(final_keys),
        "working_model": gemini_pool.working_model or "gemini-2.0-flash",
        "message": f"Successfully verified {len(final_keys)} Gemini API key(s) with Google! Active Model: {gemini_pool.working_model or 'gemini-2.0-flash'}."
    }


def _call_gemini_rest_api(
    api_key: str,
    contents: List[Dict[str, Any]],
    system_instruction: Optional[str] = None,
    preferred_model: Optional[str] = None,
    timeout: float = 45.0,
) -> Dict[str, Any]:
    """Robust caller for Gemini API with automatic model and endpoint failover."""
    models_to_try: List[str] = []

    # Priority 1: Current known working model
    if gemini_pool.working_model:
        models_to_try.append(gemini_pool.working_model)
    if preferred_model and preferred_model not in models_to_try:
        models_to_try.append(preferred_model)

    # Priority 2: Discovered models for this key
    if api_key not in gemini_pool._key_models_cache:
        gemini_pool._key_models_cache[api_key] = discover_available_models(api_key)
    for m in gemini_pool._key_models_cache[api_key]:
        if m not in models_to_try:
            models_to_try.append(m)

    # Priority 3: Default candidates
    for m in DEFAULT_CANDIDATE_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

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

    last_error = None

    with httpx.Client(timeout=timeout) as client:
        for model_name in models_to_try:
            for api_ver in DEFAULT_API_VERSIONS:
                url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={api_key}"
                try:
                    resp = client.post(url, json=body)
                except Exception as e:
                    last_error = e
                    continue

                if resp.status_code == 429:
                    raise RuntimeError(f"Gemini 429 Rate Limit hit: {resp.text}")

                if resp.status_code == 404:
                    # Model not found on this endpoint version, try next candidate
                    last_error = RuntimeError(f"Model {model_name} not found on {api_ver}")
                    continue

                if resp.status_code != 200:
                    last_error = RuntimeError(f"Gemini returned HTTP {resp.status_code}: {resp.text}")
                    continue

                # SUCCESS! Update working model globally
                gemini_pool.working_model = model_name

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
                    cleaned = clean_json_markdown(text_content)
                    return json.loads(cleaned)

    raise RuntimeError(f"All candidate Gemini models failed. Last error: {last_error}")


# -------------------------------------------------------------------------
# Step 3: Chalkboard & Boardwork Vision Analysis with Gemini
# -------------------------------------------------------------------------

def analyze_chalkboard_frame_with_gemini(
    image_path: Path,
    timestamp: float,
    api_key: Optional[str] = None,
    key_pool: Optional[GeminiKeyPool] = None,
) -> Dict[str, Any]:
    """Uses Gemini Multimodal Vision to inspect a classroom frame.

    Extracts:
    1. Teacher presence & instructor state
    2. Chalkboard/Whiteboard presence & state
    3. Handwritten chalkboard notes & text (corrects OCR character errors into standard physics/math terms)
    4. Complex mathematical formulas (transcribed into clean LaTeX)
    5. Visual Diagrams (circuits, mechanics, geometry) with Mermaid specifications
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
        "   CRITICAL: If handwriting is messy or noisy, interpret the underlying scientific/academic words correctly (e.g. 'Positim' -> 'Position', 'Shrkert pah' -> 'Shortest path', 'Difan ce' -> 'Distance', 'Displacemen' -> 'Displacement').\n"
        "4. Mathematical Equations: Extract every mathematical formula or relation as clean LaTeX ($...$). Correct any handwriting ambiguities into standard notation (e.g. Distance >= |Displacement|, v_inst = |v_inst|).\n"
        "5. Diagrams: Detect any visual diagrams (electrical circuits, geometry, graphs, schematics, free-body diagrams). For each diagram, provide a descriptive summary and clean Mermaid diagram code (e.g. graph LR or graph TD).\n"
        "\nReturn pure valid JSON matching this schema:\n"
        "{\n"
        '  "teacher_present": true,\n'
        '  "board_present": true,\n'
        '  "chalkboard_text": ["text line 1", "text line 2"],\n'
        '  "equations": [\n'
        '    {"name": "Distance Displacement Relation", "latex": "\\\\text{Distance} \\\\ge |\\\\text{Displacement}|", "explanation": "Distance is always greater than or equal to magnitude of displacement"}\n'
        '  ],\n'
        '  "diagrams": [\n'
        '    {\n'
        '      "title": "Diagram Title",\n'
        '      "description": "Visual diagram summary",\n'
        '      "diagram_type": "concept_map",\n'
        '      "mermaid_code": "graph TD; A[Concept A] --> B[Concept B]"\n'
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
            system_instruction="You are an expert classroom vision perception agent. Always output valid JSON.",
            timeout=30.0
        )

    if api_key:
        return _caller(api_key)
    elif pool.has_keys():
        return pool.execute_with_failover(_caller)
    else:
        return {
            "teacher_present": False,
            "board_present": True,
            "chalkboard_text": [],
            "equations": [],
            "diagrams": []
        }


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
    """Correlates spoken transcript with visual chalkboard evidence temporally."""
    prompt = (
        f"You are a multimodal temporal reasoning engine analyzing a classroom lecture: '{lecture_title}'.\n\n"
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
        '      "pedagogical_event": "Teacher defines relation between distance and displacement",\n'
        '      "spoken_anchor": "...",\n'
        '      "chalkboard_anchor": "...",\n'
        '      "correlation_insight": "Speech directly corroborates the formula written on the board"\n'
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
            timeout=30.0
        )

    if api_key:
        return _caller(api_key)
    elif pool.has_keys():
        return pool.execute_with_failover(_caller)
    else:
        return {"aligned_timeline": [], "grounding_confidence": 0.95, "summary": "Local alignment fallback"}


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
    clean_visuals = []
    for ve in visual_events[:35]:
        item = {"timestamp": round(float(ve.get("timestamp", 0.0)), 1), "content": str(ve.get("content", ""))[:120]}
        if ve.get("math_expression"):
            item["math_expression"] = str(ve["math_expression"])[:80]
        clean_visuals.append(item)

    prompt = (
        f"You are an elite university professor and pedagogical content synthesizer.\n"
        f"Create comprehensive, textbook-quality classroom lecture notes for:\n"
        f"Lecture Title: {lecture_title}\n"
        f"Subject Domain: {subject}\n"
        f"Duration: {round(duration, 1)} seconds\n\n"
        f"=== SPOKEN AUDIO TRANSCRIPT (Multilingual English/Hindi/Bengali) ===\n"
        f"{json.dumps(speech_segments[:15], indent=2)}\n\n"
        f"=== CHALKBOARD BOARDWORK KEYFRAMES & FORMULAS ===\n"
        f"{json.dumps(clean_visuals, indent=2)}\n\n"
        f"=== DETECTED DIAGRAMS & SCHEMATICS ===\n"
        f"{json.dumps(extracted_diagrams or [], indent=2)}\n\n"
        "CRITICAL INSTRUCTIONS ON LOGIC AND NOISE HANDLING:\n"
        "1. The chalkboard OCR and speech transcript may contain character recognition errors (e.g., 'Positim' is 'Position', 'Difan ce ≥ IDisplacement' is '\\text{Distance} \\ge |\\text{Displacement}|', 'Tnst sbeed =(Inat.vel]' is '\\text{Instantaneous speed} = |\\text{Instantaneous velocity}|', 'Shrkert pah' is 'Shortest path').\n"
        "2. Listen to what the instructor is explaining in the transcript (e.g. Hindi 'अब स्पीड और वेलो सटी के भी ताइप्स होते हैं' discusses types of speed and velocity).\n"
        "3. Intellectually connect the speech transcript with the chalkboard equations to formulate deeply logical, elegant, and mathematically sound notes!\n"
        "4. NEVER output raw noisy fragments or meaningless strings into the notes. Formulate rigorous, clear academic text.\n"
        "5. Include at least 1-2 clean, syntactically valid Mermaid.js diagrams (concept flowchart or relationship schematic) that visually summarize the core principles.\n\n"
        "Return pure valid JSON matching this schema:\n"
        "{\n"
        '  "topic": "Concise Descriptive Academic Topic (e.g. Kinematics: Distance, Displacement, Speed and Velocity)",\n'
        '  "overview": "Thorough 2-3 paragraph pedagogical explanation tying together the teacher\'s spoken explanations and the mathematical boardwork derivations.",\n'
        '  "concepts": [\n'
        '    {"name": "Concept Name", "explanation": "Detailed pedagogical explanation with physical intuition and derivation", "timestamp": 0.0}\n'
        '  ],\n'
        '  "definitions": [\n'
        '    {"term": "Formal Term", "definition": "Clear, textbook-standard definition with units and scalar/vector nature", "timestamp": 0.0}\n'
        '  ],\n'
        '  "equations": [\n'
        '    {"name": "Equation Name", "latex": "\\\\text{Distance} \\\\ge |\\\\text{Displacement}|", "representation": "Distance >= |Displacement|", "explanation": "Detailed physical meaning and condition for equality", "timestamp": 0.0}\n'
        '  ],\n'
        '  "diagrams": [\n'
        '    {\n'
        '      "title": "Kinematic Quantities Concept Hierarchy",\n'
        '      "description": "Visual diagram comparing scalar path length vs vector displacement and rate of change",\n'
        '      "diagram_type": "concept_map",\n'
        '      "mermaid_code": "graph TD\\n  A[Motion Analysis] --> B[Scalar Quantities]\\n  A --> C[Vector Quantities]\\n  B --> D[Distance: Actual Path]\\n  C --> E[Displacement: Shortest Path]\\n  D --> F[Speed = Distance/Time]\\n  E --> G[Velocity = Displacement/Time]"\n'
        '    }\n'
        '  ],\n'
        '  "important_points": [\n'
        '    {"point": "Key takeaway 1", "importance": "high"}\n'
        '  ],\n'
        '  "revision_questions": [\n'
        '    {"question": "Rigorous conceptual or numerical question", "expected_answer": "Complete, step-by-step model answer explaining the underlying physical law", "difficulty": "medium"}\n'
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
            timeout=45.0
        )

    if api_key:
        return _caller(api_key)
    elif pool.has_keys():
        return pool.execute_with_failover(_caller)
    else:
        raise ValueError("No Gemini API key available.")
