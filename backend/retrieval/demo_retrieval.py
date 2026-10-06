"""Demonstration of Local Semantic Lecture Memory Retrieval / RAG (Milestone 8).

Demonstrates:
  Lecture Memory
        ↓
  Memory Chunker
        ↓
  Local Dense Embeddings
        ↓
  Local Vector Index
        ↓
  Semantic Retrieval (Ranked evidence items with provenance and timestamps)
"""

import time
from lecture_memory.schemas import (
    LectureMemory,
    MemoryConcept,
    MemoryEquation,
    MemoryImportantPoint,
    MemoryVisualReference,
    Provenance,
)
from retrieval.retriever import SemanticLectureRetriever


def build_demo_memory():
    prov_sp = Provenance(
        source_type="speech",
        timestamp_start=12.0,
        timestamp_end=18.0,
        evidence_snippet="Ohm's law relates current, voltage and resistance.",
    )
    prov_vis = Provenance(
        source_type="visual",
        timestamp_start=15.0,
        timestamp_end=15.0,
        local_frame_reference="recordings/frames/camera_f012_15000.jpg",
    )

    return LectureMemory(
        session_id="lecture_circuits_101",
        title="Introduction to Electric Circuit Theory",
        subject="Electrical Engineering",
        overview="Foundational lecture covering Ohm's law, circuit nodes, and basic energy dissipation.",
        concepts=[
            MemoryConcept(
                id="c_ohm",
                name="Ohm's Law",
                explanation="Ohm's law relates current, voltage and resistance in a linear conductor.",
                timestamp=12.0,
                timestamp_start=12.0,
                timestamp_end=18.0,
                provenance=prov_sp,
            ),
            MemoryConcept(
                id="c_kcl",
                name="Kirchhoff's Current Law",
                explanation="The sum of electric currents entering any circuit node equals zero.",
                timestamp=42.0,
                timestamp_start=42.0,
                timestamp_end=48.0,
                provenance=prov_sp,
            ),
        ],
        equations=[
            MemoryEquation(
                name="Ohm's Law Formulation",
                representation="I = V / R",
                explanation="Electric current equals electric potential difference divided by resistance.",
                timestamp=14.5,
                grounding_status="supported",
                provenance=prov_sp,
            )
        ],
        important_points=[
            MemoryImportantPoint(
                point="Reducing circuit resistance dramatically increases electric current.",
                timestamp=20.0,
                importance="high",
                provenance=prov_sp,
            )
        ],
        visual_references=[
            MemoryVisualReference(
                timestamp=15.0,
                source="Camera",
                event_type="Board Writing",
                local_frame_reference="recordings/frames/camera_f012_15000.jpg",
                extracted_text="Board formula: I = V / R with circuit schematic",
                ocr_status="success",
                ocr_confidence=0.92,
                provenance=prov_vis,
            )
        ],
    )


def run_demo():
    print("=" * 80)
    print("GYANDRISHTI LOCAL SEMANTIC MEMORY RETRIEVAL (MILESTONE 8)")
    print("=" * 80)

    retriever = SemanticLectureRetriever()
    memory = build_demo_memory()

    # Indexing performance metrics
    print("\n[PHASE 1] Indexing Completed Lecture Memory...")
    perf = retriever.index_lecture(memory)
    print(f"Chunks Extracted:         {int(perf['chunks_count'])}")
    print(f"Chunking Latency:         {perf['chunking_ms']:.2f}ms")
    print(f"Embedding Latency:        {perf['embedding_ms']:.2f}ms")
    print(f"Vector Indexing Latency:  {perf['indexing_ms']:.2f}ms")
    print(f"Total Indexing Time:      {perf['total_ms']:.2f}ms")
    print(f"Vector Space Dimension:   {retriever.index.dimension} dimensions")

    # Queries
    queries = [
        "What is Ohm's law?",
        "How is electric current calculated from voltage?",
        "What happens when resistance decreases?",
    ]

    for q in queries:
        print("\n" + "=" * 80)
        print(f"QUERY: \"{q}\"")
        print("=" * 80)

        t0 = time.perf_counter()
        results = retriever.search(q, top_k=3)
        retrieval_ms = (time.perf_counter() - t0) * 1000.0

        print(f"Retrieval Latency: {retrieval_ms:.2f}ms")
        print("\nTOP RANKED RESULTS:")

        for rank, res in enumerate(results, start=1):
            c = res.chunk
            print(f"\n{rank}.")
            print(f"Score:          {res.score:.4f}")
            print(f"Lecture:        {c.lecture_id}")
            print(f"Chunk Type:     {c.chunk_type.value}")
            print(f"Timestamp:      {c.timestamp_start:.1f}s – {c.timestamp_end:.1f}s")
            print(f"Source:         {c.source_type}")
            print(f"Grounding:      {c.grounding_status}")
            print(f"Text:           \"{c.text}\"")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE — Local Vector Space, Zero LLM Call, 100% Evidence Grounded.")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
