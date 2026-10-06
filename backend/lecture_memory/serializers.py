"""Serialization and export utilities for GyanDrishti Canonical Lecture Memory.

Provides conversion between canonical backend LectureMemory and:
1. Frontend-compatible API dictionaries (LectureViewer.jsx)
2. Comprehensive Markdown lecture notes / revision cheatsheets.
"""

from __future__ import annotations

from typing import Any, Dict
from .schemas import LectureMemory


def to_frontend_dict(memory: LectureMemory) -> Dict[str, Any]:
    """Converts a LectureMemory instance to the exact shape expected by the frontend."""
    return memory.to_frontend_dict()


def to_markdown_notes(memory: LectureMemory) -> str:
    """Formats a LectureMemory instance into structured Markdown study notes."""
    lines = [
        f"# {memory.title}",
        f"**Subject:** {memory.subject} | **Date:** {memory.date} | **Duration:** {int(memory.duration // 60)}m {int(memory.duration % 60)}s",
        f"**Session ID:** `{memory.session_id}` | **Local Storage:** Verified",
        "",
        "## Overview",
        memory.overview,
        "",
    ]

    if memory.concepts:
        lines.append("## Key Concepts")
        for c in memory.concepts:
            lines.append(f"### {c.name} ({int(c.timestamp // 60)}:{int(c.timestamp % 60):02d})")
            lines.append(c.explanation)
            lines.append("")

    if memory.definitions:
        lines.append("## Definitions")
        for d in memory.definitions:
            lines.append(f"- **{d.term}:** {d.definition} *(at {d.timestamp:.1f}s)*")
        lines.append("")

    if memory.equations:
        lines.append("## Mathematical Formulations (Verified)")
        for eq in memory.equations:
            lines.append(f"### {eq.name}")
            lines.append(f"$$\n{eq.representation}\n$$")
            lines.append(f"*{eq.explanation}*")
            lines.append("")

    if memory.important_points:
        lines.append("## Key Takeaways")
        for pt in memory.important_points:
            star = "⭐" if pt.importance == "high" else "•"
            lines.append(f"{star} {pt.point}")
        lines.append("")

    if memory.revision_questions:
        lines.append("## Revision & Self-Assessment")
        for idx, q in enumerate(memory.revision_questions, start=1):
            lines.append(f"{idx}. **Question:** {q.question}")
            lines.append(f"   - **Answer:** {q.answer}")
        lines.append("")

    return "\n".join(lines)
