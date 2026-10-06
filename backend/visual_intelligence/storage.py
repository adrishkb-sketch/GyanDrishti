"""Local filesystem storage for visual intelligence results.

Provides atomic, safe, offline-first persistence of OCR analysis results
without modifying original video keyframe media.
"""

import json
import os
import re
from pathlib import Path
from typing import List

from .schemas import VisualAnalysisResult


class VisualEvidenceStorageError(Exception):
    """Base exception for visual intelligence persistence failures."""
    pass


class InvalidSessionIdError(VisualEvidenceStorageError):
    """Raised when session ID contains path traversal or illegal characters."""
    pass


class ResultsNotFoundError(VisualEvidenceStorageError):
    """Raised when requested visual analysis results do not exist."""
    pass


class CorruptResultsError(VisualEvidenceStorageError):
    """Raised when visual analysis results JSON is malformed."""
    pass


class VisualEvidenceStorage:
    """Manages local atomic JSON storage of visual intelligence analysis outputs."""

    def __init__(self, base_dir: str = "data/visual_intelligence") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_session_id(self, session_id: str) -> None:
        if not session_id or not isinstance(session_id, str):
            raise InvalidSessionIdError("session_id must be a non-empty string")
        if not re.match(r"^[a-zA-Z0-9_\-]+$", session_id):
            raise InvalidSessionIdError(
                f"session_id '{session_id}' contains invalid characters or path traversal attempt"
            )

    def get_session_dir(self, session_id: str) -> Path:
        self._validate_session_id(session_id)
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def save_results(
        self,
        session_id: str,
        results: List[VisualAnalysisResult],
    ) -> Path:
        """Atomically saves a list of VisualAnalysisResults to JSON."""
        session_dir = self.get_session_dir(session_id)
        target_path = session_dir / "visual_analysis.json"
        temp_path = session_dir / "visual_analysis.tmp"

        payload = [r.model_dump(mode="json") for r in results]
        json_data = json.dumps(payload, indent=2, ensure_ascii=False)

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(json_data)
            os.replace(temp_path, target_path)
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

        return target_path

    def load_results(self, session_id: str) -> List[VisualAnalysisResult]:
        """Loads and parses visual analysis results for a session."""
        session_dir = self.get_session_dir(session_id)
        target_path = session_dir / "visual_analysis.json"

        if not target_path.exists():
            raise ResultsNotFoundError(f"Visual results for '{session_id}' not found at {target_path}")

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Expected list of visual analysis items")
            return [VisualAnalysisResult.model_validate(item) for item in data]
        except (json.JSONDecodeError, ValueError) as e:
            raise CorruptResultsError(f"Malformed visual results for '{session_id}': {str(e)}") from e
