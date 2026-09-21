from traceable_rag.evaluation import evaluate_traceability
from traceable_rag.evidence import build_evidence_package
from traceable_rag.generation import GenerationOutput
from traceable_rag.retrieval import RetrievedUnit
from traceable_rag.schema import KnowledgeUnit


def test_layered_metrics_keep_retrieval_and_provenance_distinct() -> None:
    unit = KnowledgeUnit(
        unit_id="u-1",
        document_id="synthetic-doc",
        page=1,
        clause="1.1",
        text="A fictional rule.",
    )
    retrieved = [RetrievedUnit(unit=unit, score=1.0, rank=1)]
    package = build_evidence_package(retrieved)
    metrics = evaluate_traceability(
        retrieved,
        ["u-1"],
        GenerationOutput(answer="An answer.", citation_ids=("E1",)),
        package,
        gold_answer="An answer.",
        supporting_unit_ids=["u-1"],
        k=1,
    )

    assert metrics == {
        "retrieval_hit_at_k": 1.0,
        "evidence_available": True,
        "answer_correct": True,
        "provenance_integrity": True,
        "structured_output_valid": True,
        "citation_ids_valid": True,
        "provenance_resolved": True,
        "supporting_units_cited": True,
        "end_to_end_traceability": True,
    }


def test_correct_answer_does_not_make_an_invalid_citation_valid() -> None:
    unit = KnowledgeUnit(
        unit_id="u-1",
        document_id="synthetic-doc",
        page=1,
        clause="1.1",
        text="A fictional rule.",
    )
    retrieved = [RetrievedUnit(unit=unit, score=1.0, rank=1)]
    package = build_evidence_package(retrieved)
    metrics = evaluate_traceability(
        retrieved,
        ["u-1"],
        GenerationOutput(answer=unit.text, citation_ids=("E999",)),
        package,
        gold_answer=unit.text,
        supporting_unit_ids=["u-1"],
        k=1,
    )

    assert metrics["retrieval_hit_at_k"] == 1.0
    assert metrics["evidence_available"] is True
    assert metrics["answer_correct"] is True
    assert metrics["structured_output_valid"] is True
    assert metrics["citation_ids_valid"] is False
    assert metrics["provenance_resolved"] is False
    assert metrics["provenance_integrity"] is False
    assert metrics["supporting_units_cited"] is False
    assert metrics["end_to_end_traceability"] is False
