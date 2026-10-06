"""Unit tests for language detection and code-switching analysis."""

from speech_engine.language import (
    aggregate_languages,
    detect_romanized_indic_tokens,
    detect_script_presence,
    detect_segment_languages,
)
from speech_engine.schemas import TranscriptionSegment


def test_pure_english() -> None:
    text = "Today we're going to study electromagnetic induction."
    langs = detect_segment_languages(text)
    assert langs == ["en"]


def test_hindi_english_code_switching() -> None:
    text = "अब हम Faraday's law के बारे में पढ़ेंगे।"
    langs = detect_segment_languages(text)
    assert "hi" in langs
    assert "en" in langs
    assert langs == ["en", "hi"]


def test_bengali_english_code_switching() -> None:
    text = "এখানে আমরা দেখছি যে magnetic flux পরিবর্তন হচ্ছে।"
    langs = detect_segment_languages(text)
    assert "bn" in langs
    assert "en" in langs
    assert langs == ["bn", "en"]


def test_pure_bengali() -> None:
    text = "এখানে আমরা পরিবর্তন দেখছি"
    langs = detect_segment_languages(text)
    assert langs == ["bn"]


def test_pure_hindi() -> None:
    text = "अब हम इस पर चर्चा करेंगे"
    langs = detect_segment_languages(text)
    assert langs == ["hi"]


def test_romanized_hinglish() -> None:
    text = "Ab is equation ko differentiate karne ke baad hum EMF calculate karenge."
    langs = detect_segment_languages(text)
    assert "hi" in langs
    assert "en" in langs


def test_romanized_banglish() -> None:
    text = "Ekhane amra basically flux-er change-ta dekhchi."
    langs = detect_segment_languages(text)
    assert "bn" in langs
    assert "en" in langs


def test_three_way_mixed() -> None:
    text = "এখানে basically আমরা देख सकते हैं कि the current is increasing."
    langs = detect_segment_languages(text)
    assert "bn" in langs
    assert "hi" in langs
    assert "en" in langs


def test_aggregate_languages() -> None:
    segments = [
        TranscriptionSegment(id=1, start=0.0, end=2.0, text="hello", language=["en"]),
        TranscriptionSegment(id=2, start=2.0, end=4.0, text="नमस्ते", language=["hi", "en"]),
        TranscriptionSegment(id=3, start=4.0, end=6.0, text="নমস্কার", language=["bn"]),
    ]
    summary = aggregate_languages(segments)
    assert summary == ["bn", "en", "hi"]
