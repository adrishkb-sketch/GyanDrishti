import pytest
import time
from unittest.mock import MagicMock, patch

from gemini_engine import (
    GeminiKeyPool,
    clean_json_markdown,
    extract_mermaid_blocks,
    analyze_chalkboard_frame_with_gemini,
    align_multimodal_with_gemini,
    synthesize_lecture_notes_with_gemini
)


def test_gemini_key_pool_init():
    keys = ["key_alpha", "key_beta", "key_gamma"]
    pool = GeminiKeyPool(api_keys=keys)
    assert pool.get_key_count() == 3
    stats = pool.get_stats()
    assert stats["total_keys"] == 3
    assert stats["active_keys"] == 3
    assert stats["rate_limited_keys"] == 0


def test_gemini_key_pool_round_robin():
    keys = ["key_alpha", "key_beta"]
    pool = GeminiKeyPool(api_keys=keys, min_call_interval_sec=0.0)
    k1 = pool.get_next_key()
    k2 = pool.get_next_key()
    k3 = pool.get_next_key()
    assert k1 == "key_alpha"
    assert k2 == "key_beta"
    assert k3 == "key_alpha"


def test_gemini_key_pool_rate_limit_failover():
    keys = ["key_primary", "key_backup"]
    pool = GeminiKeyPool(api_keys=keys, cooldown_seconds=10.0, min_call_interval_sec=0.0)

    # Primary key hits 429
    pool.mark_rate_limited("key_primary")
    stats = pool.get_stats()
    assert stats["rate_limited_keys"] == 1

    # Should automatically hand out backup key
    next_key = pool.get_next_key()
    assert next_key == "key_backup"


def test_execute_with_failover_rotates_on_429():
    pool = GeminiKeyPool(api_keys=["key_1", "key_2"], cooldown_seconds=30.0, min_call_interval_sec=0.0)

    call_count = 0

    def mock_operation(api_key):
        nonlocal call_count
        call_count += 1
        if api_key == "key_1":
            raise Exception("429 ResourceExhausted: Quota exceeded for model")
        return f"success_with_{api_key}"

    result = pool.execute_with_failover(mock_operation)
    assert result == "success_with_key_2"
    assert call_count == 2
    assert "key_1" in pool.rate_limited_until


def test_clean_json_markdown():
    raw_markdown = """```json
    {
        "status": "ok",
        "value": 42
    }
    ```"""
    cleaned = clean_json_markdown(raw_markdown)
    assert cleaned.strip() == '{\n        "status": "ok",\n        "value": 42\n    }'


def test_extract_mermaid_blocks():
    text = """
    Here is the concept graph:
    ```mermaid
    graph TD
        A[Voltage] --> B[Current]
    ```
    And notes continue.
    """
    blocks = extract_mermaid_blocks(text)
    assert len(blocks) == 1
    assert "graph TD" in blocks[0]
    assert "Voltage" in blocks[0]


def test_fallback_when_gemini_fails_or_no_keys():
    pool = GeminiKeyPool(api_keys=[])
    
    # Should gracefully return empty structure without crashing
    res = analyze_chalkboard_frame_with_gemini(
        image_path="/nonexistent.jpg",
        timestamp=0.0,
        key_pool=pool
    )
    assert res["board_present"] is True
    assert res["chalkboard_text"] == []
