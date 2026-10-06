"""Unit tests for LectureMemoryStorage (Milestone 5)."""

import json
from pathlib import Path
import pytest

from lecture_memory.schemas import LectureMemory
from lecture_memory.storage import (
    CorruptMemoryError,
    InvalidSessionIdError,
    LectureMemoryStorage,
    MemoryNotFoundError,
)


def test_storage_save_and_load(tmp_path: Path) -> None:
    """TEST 13: Storage save/load works."""
    storage = LectureMemoryStorage(base_dir=tmp_path)
    memory = LectureMemory(
        session_id="lecture_20261006_test",
        title="Test Physics Session",
        duration=180.0,
        overview="Testing storage operations.",
    )

    saved_path = storage.save(memory)
    assert saved_path.exists()
    assert (tmp_path / "lecture_20261006_test" / "metadata.json").exists()

    loaded = storage.load("lecture_20261006_test")
    assert loaded.session_id == memory.session_id
    assert loaded.title == memory.title
    assert loaded.duration == memory.duration


def test_storage_corrupt_json_error(tmp_path: Path) -> None:
    """TEST 14: Corrupt JSON produces a clear error."""
    storage = LectureMemoryStorage(base_dir=tmp_path)
    session_dir = tmp_path / "corrupt_session"
    session_dir.mkdir(parents=True)
    bad_file = session_dir / "memory.json"
    with open(bad_file, "w") as f:
        f.write("{ malformed json content ]")

    with pytest.raises(CorruptMemoryError, match="Corrupt or schema-invalid"):
        storage.load("corrupt_session")


def test_storage_memory_not_found(tmp_path: Path) -> None:
    storage = LectureMemoryStorage(base_dir=tmp_path)
    with pytest.raises(MemoryNotFoundError):
        storage.load("nonexistent_session")


def test_storage_invalid_session_id_path_traversal(tmp_path: Path) -> None:
    storage = LectureMemoryStorage(base_dir=tmp_path)
    with pytest.raises(InvalidSessionIdError):
        storage.load("../../etc/passwd")

    with pytest.raises(InvalidSessionIdError):
        storage.load("sub/folder")


def test_storage_list_lectures(tmp_path: Path) -> None:
    storage = LectureMemoryStorage(base_dir=tmp_path)
    m1 = LectureMemory(session_id="lec_1", title="Title 1", overview="Overview 1", duration=100.0)
    m2 = LectureMemory(session_id="lec_2", title="Title 2", overview="Overview 2", duration=200.0)

    storage.save(m1)
    storage.save(m2)

    lectures = storage.list_lectures()
    assert len(lectures) == 2
    session_ids = {l["session_id"] for l in lectures}
    assert "lec_1" in session_ids
    assert "lec_2" in session_ids
