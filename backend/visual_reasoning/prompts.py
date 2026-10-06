"""Prompts for local Vision-Language Model diagram reasoning."""

VLM_DIAGRAM_ANALYSIS_PROMPT = """You are analyzing a keyframe captured from a classroom lecture board or slide.
Observe the visual scene and output a JSON object describing any diagram, graph, schematic, or layout present.

Return ONLY a JSON object with this exact structure:
{
  "diagram_type": "circuit_diagram" | "graph_plot" | "geometric_diagram" | "flowchart_block" | "equation_layout" | "table" | "generic_diagram" | "no_diagram",
  "description": "Clear concise 1-2 sentence description of the visual diagram and its pedagogical purpose.",
  "entities_detected": ["entity1", "entity2"],
  "relations_detected": ["entity1 connects to entity2"],
  "visible_equations": ["equation observed in diagram"],
  "confidence": 0.85
}

RULES:
1. Do NOT guess text that cannot be clearly seen.
2. If there is no diagram or only plain text notes, set diagram_type to "no_diagram".
3. Return valid JSON only, without markdown fences or pleasantries.
"""


def build_vlm_prompt(subject_hint: str = "General Science") -> str:
    """Builds a contextualized VLM prompt."""
    return f"Subject Context: {subject_hint}\n\n{VLM_DIAGRAM_ANALYSIS_PROMPT}"
