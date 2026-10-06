"""Language classification and metadata utilities for GyanDrishti.

Handles multilingual speech analysis across English (en), Hindi (hi), and
Bengali (bn), with dedicated support for code-switching (e.g., Hinglish, Banglish,
and trilingual classroom lectures).

Design Philosophy:
- Preserves raw transcripts exactly as spoken (no auto-translation).
- Accurately identifies multi-language segments using hybrid script analysis,
  lexical transliteration markers, and model-level language classification.
- Strictly avoids fake precision: honest segment-level classification rather
  than fabricated word-level boundaries.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Set

# Unicode script ranges
DEV_REGEX = re.compile(r"[\u0900-\u097F]")  # Devanagari (Hindi)
BEN_REGEX = re.compile(r"[\u0980-\u09FF]")  # Bengali (Bangla)
LAT_REGEX = re.compile(r"[a-zA-Z]")          # Latin (English / Romanized)

# High-frequency Romanized Indic stopwords for detecting Hinglish / Banglish
# when spoken words are transcribed in Latin script or mixed with English terms.
HINGLISH_TOKENS: Set[str] = {
    "ab", "hum", "ham", "ke", "ko", "ki", "ka", "karenge", "karna", "baad",
    "mein", "aur", "ye", "yeh", "woh", "voh", "hota", "hoti", "hote", "hai",
    "hain", "kya", "toh", "to", "lekin", "samajh", "dekh", "dekho", "karte",
    "kisi", "iska", "uski", "unka", "hoga", "hogi", "bol", "raha", "rahe",
    "padhenge", "padhna", "calculate", "equation", "formula", "pehle", "phir",
}

BANGLISH_TOKENS: Set[str] = {
    "ekhane", "amra", "aamra", "dekhchi", "dekhbo", "hobe", "holo", "kore",
    "kora", "ei", "eta", "sheta", "seta", "kintu", "ar", "aar", "ebong",
    "ache", "achhe", "chilo", "bujhte", "poriborton", "shob", "sob", "korbo",
    "dekhun", "dekhte", "te", "er", "take", "theke", "diye", "jabe", "jaay",
}

VALID_LANGUAGES: Set[str] = {"en", "hi", "bn"}


def detect_script_presence(text: str) -> dict[str, int]:
    """Counts character occurrences belonging to Devanagari, Bengali, and Latin scripts.

    Returns:
        dict with counts for 'devanagari', 'bengali', and 'latin'.
    """
    dev_count = len(DEV_REGEX.findall(text))
    ben_count = len(BEN_REGEX.findall(text))
    lat_count = len(LAT_REGEX.findall(text))
    return {
        "devanagari": dev_count,
        "bengali": ben_count,
        "latin": lat_count,
    }


def detect_segment_scripts(text: str, min_char_count: int = 1) -> List[str]:
    """Identifies the writing scripts present in text.

    Returns:
        Sorted list containing any of 'Bengali', 'Devanagari', 'Latin'.
    """
    counts = detect_script_presence(text)
    scripts: List[str] = []
    if counts["bengali"] >= min_char_count:
        scripts.append("Bengali")
    if counts["devanagari"] >= min_char_count:
        scripts.append("Devanagari")
    if counts["latin"] >= min_char_count:
        scripts.append("Latin")
    return sorted(scripts)


def detect_romanized_indic_tokens(text: str) -> tuple[bool, bool]:
    """Checks whether Latin text contains recognizable Hinglish or Banglish tokens.

    Returns:
        tuple (has_hinglish: bool, has_banglish: bool)
    """
    words = {w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", text)}
    if not words:
        return False, False

    hinglish_matches = words.intersection(HINGLISH_TOKENS)
    banglish_matches = words.intersection(BANGLISH_TOKENS)

    # Require at least 2 distinct transliterated tokens to minimize false positives,
    # or 1 token if total words is small (<= 5).
    threshold = 1 if len(words) <= 5 else 2
    has_hinglish = len(hinglish_matches) >= threshold
    has_banglish = len(banglish_matches) >= threshold

    return has_hinglish, has_banglish


def detect_segment_languages(
    text: str,
    model_language: Optional[str] = None,
    min_char_count: int = 2,
) -> List[str]:
    """Determines the set of languages present in a given segment text.

    Combines:
    1. Direct native script analysis (Devanagari for 'hi', Bengali for 'bn').
    2. Latin script presence with English / technical words ('en').
    3. Lexical analysis for transliterated Hinglish and Banglish.
    4. Model-level language detection signal from Whisper.

    Args:
        text: Segment text string.
        model_language: ISO language code emitted by the ASR model (e.g. 'hi', 'bn', 'en').
        min_char_count: Minimum characters required in a script to count as distinct language.

    Returns:
        Sorted list of language codes, e.g. ['en'], ['hi', 'en'], ['bn', 'en'], ['bn', 'hi', 'en'].
    """
    cleaned = text.strip()
    if not cleaned:
        if model_language in VALID_LANGUAGES:
            return [model_language]
        return ["en"]

    counts = detect_script_presence(cleaned)
    dev_count = counts["devanagari"]
    ben_count = counts["bengali"]
    lat_count = counts["latin"]

    detected: Set[str] = set()

    # 1. Direct native script detection
    if dev_count >= min_char_count:
        detected.add("hi")
    if ben_count >= min_char_count:
        detected.add("bn")

    # 2. Latin script analysis
    if lat_count >= min_char_count:
        detected.add("en")

        # Check for Romanized Hinglish / Banglish
        has_hinglish, has_banglish = detect_romanized_indic_tokens(cleaned)
        if has_hinglish:
            detected.add("hi")
        if has_banglish:
            detected.add("bn")

    # 3. Model language signal
    # If the model strongly detected Hindi or Bengali, but text is primarily Latin (or vice versa),
    # incorporate the model signal to account for code-switched technical lecture speech.
    if model_language in VALID_LANGUAGES:
        if not detected:
            detected.add(model_language)
        elif model_language in {"hi", "bn"}:
            # Teacher spoke Hindi or Bengali, possibly with English technical jargon
            detected.add(model_language)

    # Fallback to English if nothing matched
    if not detected:
        detected.add("en")

    return sorted(list(detected))


def aggregate_languages(segments: Iterable[Any]) -> List[str]:
    """Aggregates all unique languages across multiple segments.

    Args:
        segments: Iterable of segment objects with a .language attribute or dicts with a 'language' key.

    Returns:
        Sorted list of all unique languages present in the session.
    """
    all_langs: Set[str] = set()
    for seg in segments:
        langs = getattr(seg, "language", None)
        if langs is None and isinstance(seg, dict):
            langs = seg.get("language", [])
        if isinstance(langs, list):
            for lang in langs:
                if lang in VALID_LANGUAGES:
                    all_langs.add(lang)
    return sorted(list(all_langs)) if all_langs else ["en"]
