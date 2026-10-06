"""Storage module for GyanDrishti Local Lecture Memory (Milestone 5).

Provides local-only, atomic, schema-validated JSON persistence with zero
cloud dependencies and strict protection against path traversal attacks.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from .schemas import LectureMemory

logger = logging.getLogger(__name__)

# Default base directory for lecture memory storage
DEFAULT_STORAGE_DIR = Path("data/lectures")


class LectureMemoryStorageError(Exception):
    """Base exception for lecture memory storage errors."""
    pass


class MemoryNotFoundError(LectureMemoryStorageError):
    """Raised when a requested lecture memory file is not found."""
    pass


class CorruptMemoryError(LectureMemoryStorageError):
    """Raised when stored lecture memory JSON is malformed or invalid."""
    pass


class InvalidSessionIdError(LectureMemoryStorageError):
    """Raised when a session ID contains invalid characters or path traversal attempts."""
    pass


def _validate_session_id(session_id: str) -> str:
    """Sanitizes and validates session ID against directory traversal attacks."""
    clean_id = session_id.strip()
    if not clean_id:
        raise InvalidSessionIdError("Session ID cannot be empty.")
    if "/" in clean_id or "\\" in clean_id or ".." in clean_id:
        raise InvalidSessionIdError(f"Invalid characters or traversal detected in session_id: '{session_id}'")
    if not re.match(r"^[A-Za-z0-9_-]+$", clean_id):
        raise InvalidSessionIdError(f"Session ID '{session_id}' must contain only alphanumeric, dash, or underscore characters.")
    return clean_id


class LectureMemoryStorage:
    """Local atomic persistence manager for canonical LectureMemory objects."""

    def __init__(self, base_dir: Optional[str | Path] = None) -> None:
        """Initializes storage manager with a local filesystem directory.

        Args:
            base_dir: Root directory for lecture memories. Defaults to 'data/lectures'.
        """
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_lecture_dir(self, session_id: str) -> Path:
        valid_id = _validate_session_id(session_id)
        lecture_dir = self.base_dir / valid_id
        return lecture_dir

    def save(self, memory: LectureMemory) -> Path:
        """Atomically saves LectureMemory to disk.

        Writes:
        - memory.json (full canonical representation)
        - metadata.json (lightweight index for fast listing)
        """
        lecture_dir = self._get_lecture_dir(memory.session_id)
        lecture_dir.mkdir(parents=True, exist_ok=True)

        memory_file = lecture_dir / "memory.json"
        tmp_memory_file = lecture_dir / "memory.json.tmp"

        # 1. Atomic write of canonical memory.json
        payload = memory.to_json(indent=2)
        with open(tmp_memory_file, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_memory_file, memory_file)

        # 2. Write lightweight metadata index
        meta_file = lecture_dir / "metadata.json"
        meta_payload = {
            "session_id": memory.session_id,
            "title": memory.title,
            "subject": memory.subject,
            "date": memory.date,
            "created_at": memory.created_at,
            "duration": memory.duration,
            "concepts_count": len(memory.concepts),
            "equations_count": len(memory.equations),
            "grounding_score": memory.grounding_summary.get("overall_grounding_score", 1.0),
            "schema_version": memory.schema_version,
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2)

        logger.info("Successfully persisted lecture memory for session '%s' at %s", memory.session_id, memory_file)
        return memory_file

    def load(self, session_id: str) -> LectureMemory:
        """Loads and validates a canonical LectureMemory from local storage."""
        lecture_dir = self._get_lecture_dir(session_id)
        memory_file = lecture_dir / "memory.json"

        if not memory_file.exists():
            raise MemoryNotFoundError(f"Lecture memory not found for session_id '{session_id}' at {memory_file}")

        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            raise LectureMemoryStorageError(f"Failed to read memory file {memory_file}: {e}") from e

        try:
            return LectureMemory.from_json(content)
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            raise CorruptMemoryError(f"Corrupt or schema-invalid lecture memory in {memory_file}: {e}") from e

    def list_lectures(self) -> List[Dict[str, Any]]:
        """Returns indexed summaries of all stored lecture sessions, sorted by creation date."""
        results: List[Dict[str, Any]] = []

        if not self.base_dir.exists():
            return results

        for child in self.base_dir.iterdir():
            if child.is_dir():
                meta_file = child / "metadata.json"
                memory_file = child / "memory.json"

                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            results.append(meta)
                            continue
                    except Exception as e:
                        logger.warning("Error reading metadata from %s: %e", meta_file, e)

                if memory_file.exists():
                    try:
                        with open(memory_file, "r", encoding="utf-8") as f:
                            mem = LectureMemory.from_json(f.read())
                            results.append({
                                "session_id": mem.session_id,
                                "title": mem.title,
                                "subject": mem.subject,
                                "date": mem.date,
                                "created_at": mem.created_at,
                                "duration": mem.duration,
                                "concepts_count": len(mem.concepts),
                                "equations_count": len(mem.equations),
                                "grounding_score": mem.grounding_summary.get("overall_grounding_score", 1.0),
                                "schema_version": mem.schema_version,
                            })
                    except Exception as e:
                        logger.warning("Skipping unreadable lecture file %s: %s", memory_file, e)

        # Sort descending by created_at
        results.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return results

    def delete(self, session_id: str) -> bool:
        """Removes a lecture memory directory from disk."""
        lecture_dir = self._get_lecture_dir(session_id)
        if not lecture_dir.exists():
            return False

        for f in lecture_dir.iterdir():
            f.unlink()
        lecture_dir.rmdir()
        return True
