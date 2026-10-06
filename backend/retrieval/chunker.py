"""Semantic memory chunker for transforming LectureMemory into granular retrieval units."""

from typing import List
from lecture_memory.schemas import LectureMemory
from .schemas import ChunkType, MemoryChunk


class LectureMemoryChunker:
    """Extracts strongly-typed semantic chunks from canonical LectureMemory.

    Strictly ignores rejected hallucinations and preserves provenance on every chunk.
    """

    @classmethod
    def chunk_lecture(cls, memory: LectureMemory) -> List[MemoryChunk]:
        """Converts a LectureMemory instance into indexed semantic chunks."""
        chunks: List[MemoryChunk] = []
        sess_id = memory.session_id
        lec_id = memory.session_id

        # 1. Chunk Concepts
        for idx, c in enumerate(memory.concepts):
            prov = c.provenance.model_dump() if hasattr(c, "provenance") else {}
            st = c.timestamp_start if c.timestamp_start is not None else c.timestamp
            et = c.timestamp_end if c.timestamp_end is not None else c.timestamp
            chunks.append(
                MemoryChunk(
                    chunk_id=f"{sess_id}_concept_{idx+1:03d}",
                    lecture_id=lec_id,
                    session_id=sess_id,
                    chunk_type=ChunkType.CONCEPT,
                    source_item_id=c.id,
                    timestamp_start=st,
                    timestamp_end=et,
                    text=f"Concept {c.name}: {c.explanation}",
                    source_type=getattr(c.provenance, "source_type", "speech") if hasattr(c, "provenance") else "speech",
                    grounding_status="trusted",
                    provenance=prov,
                    metadata={"concept_name": c.name},
                )
            )

        # 2. Chunk Definitions
        for idx, d in enumerate(memory.definitions):
            prov = d.provenance.model_dump() if hasattr(d, "provenance") else {}
            chunks.append(
                MemoryChunk(
                    chunk_id=f"{sess_id}_def_{idx+1:03d}",
                    lecture_id=lec_id,
                    session_id=sess_id,
                    chunk_type=ChunkType.DEFINITION,
                    source_item_id=f"def_{idx+1}",
                    timestamp_start=d.timestamp,
                    timestamp_end=d.timestamp + 5.0,
                    text=f"Definition of {d.term}: {d.definition}",
                    source_type=getattr(d.provenance, "source_type", "speech") if hasattr(d, "provenance") else "speech",
                    grounding_status="trusted",
                    provenance=prov,
                    metadata={"term": d.term},
                )
            )

        # 3. Chunk Equations (TRUSTED ONLY; rejected equations excluded)
        for idx, eq in enumerate(memory.equations):
            prov = eq.provenance.model_dump() if hasattr(eq, "provenance") else {}
            chunks.append(
                MemoryChunk(
                    chunk_id=f"{sess_id}_eq_{idx+1:03d}",
                    lecture_id=lec_id,
                    session_id=sess_id,
                    chunk_type=ChunkType.EQUATION,
                    source_item_id=f"eq_{idx+1}",
                    timestamp_start=eq.timestamp,
                    timestamp_end=eq.timestamp + 5.0,
                    text=f"Formula {eq.name}: {eq.representation}. Explanation: {eq.explanation}",
                    source_type=getattr(eq.provenance, "source_type", "speech") if hasattr(eq, "provenance") else "speech",
                    grounding_status="trusted",
                    provenance=prov,
                    metadata={"formula": eq.representation, "name": eq.name},
                )
            )

        # 4. Chunk Important Points
        for idx, pt in enumerate(memory.important_points):
            prov = pt.provenance.model_dump() if hasattr(pt, "provenance") else {}
            chunks.append(
                MemoryChunk(
                    chunk_id=f"{sess_id}_pt_{idx+1:03d}",
                    lecture_id=lec_id,
                    session_id=sess_id,
                    chunk_type=ChunkType.IMPORTANT_POINT,
                    source_item_id=f"pt_{idx+1}",
                    timestamp_start=pt.timestamp,
                    timestamp_end=pt.timestamp + 5.0,
                    text=f"Key Takeaway: {pt.point}",
                    source_type=getattr(pt.provenance, "source_type", "speech") if hasattr(pt, "provenance") else "speech",
                    grounding_status="trusted",
                    provenance=prov,
                    metadata={"importance": pt.importance},
                )
            )

        # 5. Chunk Revision Questions
        for idx, q in enumerate(memory.revision_questions):
            prov = q.provenance.model_dump() if hasattr(q, "provenance") else {}
            chunks.append(
                MemoryChunk(
                    chunk_id=f"{sess_id}_q_{idx+1:03d}",
                    lecture_id=lec_id,
                    session_id=sess_id,
                    chunk_type=ChunkType.QUESTION,
                    source_item_id=f"q_{idx+1}",
                    timestamp_start=q.timestamp,
                    timestamp_end=q.timestamp + 5.0,
                    text=f"Revision Question: {q.question} Answer: {q.answer}",
                    source_type=getattr(q.provenance, "source_type", "derived") if hasattr(q, "provenance") else "derived",
                    grounding_status="trusted",
                    provenance=prov,
                    metadata={"question": q.question},
                )
            )

        # 6. Chunk Visual References (Retains source_type="visual")
        for idx, vr in enumerate(memory.visual_references):
            prov = vr.provenance.model_dump() if hasattr(vr, "provenance") else {}
            extracted = vr.extracted_text or vr.description or "Visual keyframe note"
            chunks.append(
                MemoryChunk(
                    chunk_id=f"{sess_id}_visual_{idx+1:03d}",
                    lecture_id=lec_id,
                    session_id=sess_id,
                    chunk_type=ChunkType.VISUAL_EXPLANATION,
                    source_item_id=vr.keyframe_id or f"vr_{idx+1}",
                    timestamp_start=vr.timestamp,
                    timestamp_end=vr.timestamp + 3.0,
                    text=f"Visual Board Evidence ({vr.event_type}): {extracted}",
                    source_type="visual",  # Strictly preserved as visual
                    grounding_status="trusted" if vr.ocr_status == "success" else "uncertain",
                    provenance=prov,
                    metadata={"event_type": vr.event_type, "ocr_status": vr.ocr_status},
                )
            )

        return chunks
