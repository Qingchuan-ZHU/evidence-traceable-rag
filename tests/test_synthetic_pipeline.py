from pathlib import Path

from traceable_rag.corpus import load_jsonl_records, load_knowledge_units
from traceable_rag.evaluation import evaluate_traceability
from traceable_rag.evidence import build_evidence_package
from traceable_rag.generation import MockGenerator
from traceable_rag.provenance import resolve_provenance
from traceable_rag.retrieval import BM25Retriever


ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_synthetic_pipeline_is_api_free() -> None:
    units = load_knowledge_units(ROOT / "examples" / "synthetic_corpus.jsonl")
    question = load_jsonl_records(ROOT / "examples" / "synthetic_questions.jsonl")[0]
    retrieved = BM25Retriever(units).retrieve(question["question"], top_k=3)
    package = build_evidence_package(retrieved)
    generated = MockGenerator().generate(question["question"], package)
    resolved = resolve_provenance(generated, package)
    metrics = evaluate_traceability(
        retrieved,
        question["relevant_unit_ids"],
        generated,
        package,
        gold_answer=question["gold_answer"],
        supporting_unit_ids=question["supporting_unit_ids"],
        k=3,
    )

    assert units
    assert retrieved
    assert generated.citation_ids == ("E1",)
    assert resolved.valid is True
    assert metrics["retrieval_hit_at_k"] == 1.0
    assert metrics["evidence_available"] is True
    assert metrics["answer_correct"] is True
    assert metrics["provenance_resolved"] is True
    assert metrics["provenance_integrity"] is True
    assert metrics["supporting_units_cited"] is True
    assert metrics["end_to_end_traceability"] is True
