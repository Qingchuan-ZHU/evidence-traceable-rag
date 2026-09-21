import pytest

from traceable_rag.evaluation import answer_correct, evaluate_traceability
from traceable_rag.evidence import build_evidence_package
from traceable_rag.generation import GenerationOutput
from traceable_rag.provenance import resolve_provenance
from traceable_rag.retrieval import RetrievedUnit
from traceable_rag.schema import KnowledgeUnit


GOLD = "The fictional limit is 72 units."


def _unit(unit_id: str, text: str) -> KnowledgeUnit:
    return KnowledgeUnit(
        unit_id=unit_id,
        document_id="synthetic-doc",
        page=2,
        clause="2.1",
        text=text,
    )


def _metrics(
    retrieved: list[RetrievedUnit],
    answer: GenerationOutput,
    package,
    *,
    relevant: list[str],
    supporting: list[str],
):
    return evaluate_traceability(
        retrieved,
        relevant,
        answer,
        package,
        gold_answer=GOLD,
        supporting_unit_ids=supporting,
        k=3,
    )


def test_case_a_all_layers_pass() -> None:
    unit = _unit("u-correct", GOLD)
    retrieved = [RetrievedUnit(unit=unit, score=1.0, rank=1)]
    package = build_evidence_package(retrieved)
    metrics = _metrics(
        retrieved,
        GenerationOutput(answer=GOLD, citation_ids=("E1",)),
        package,
        relevant=["u-correct"],
        supporting=["u-correct"],
    )

    assert metrics["evidence_available"] is True
    assert metrics["answer_correct"] is True
    assert metrics["provenance_integrity"] is True
    assert metrics["supporting_units_cited"] is True
    assert metrics["end_to_end_traceability"] is True


def test_evidence_availability_is_false_when_package_truncates_retrieval_hit() -> None:
    required = _unit("u-required", GOLD)
    distractor = _unit("u-distractor", "The fictional color is amber.")
    retrieved = [
        RetrievedUnit(unit=distractor, score=2.0, rank=1),
        RetrievedUnit(unit=required, score=1.0, rank=2),
    ]
    metrics = _metrics(
        retrieved,
        GenerationOutput(answer=GOLD, citation_ids=("E1",)),
        build_evidence_package(retrieved, max_items=1),
        relevant=[required.unit_id],
        supporting=[required.unit_id],
    )

    assert metrics["retrieval_hit_at_k"] == 1.0
    assert metrics["evidence_available"] is False


def test_evidence_availability_requires_all_required_units() -> None:
    first = _unit("u-first", GOLD)
    second = _unit("u-second", "The fictional color is amber.")
    retrieved = [
        RetrievedUnit(unit=first, score=2.0, rank=1),
        RetrievedUnit(unit=second, score=1.0, rank=2),
    ]
    metrics = _metrics(
        retrieved,
        GenerationOutput(answer=GOLD, citation_ids=("E1",)),
        build_evidence_package(retrieved, max_items=1),
        relevant=[first.unit_id, second.unit_id],
        supporting=[first.unit_id],
    )

    assert metrics["retrieval_hit_at_k"] == 1.0
    assert metrics["evidence_available"] is False


def test_evidence_availability_is_true_when_all_required_units_are_packaged() -> None:
    first = _unit("u-first", GOLD)
    second = _unit("u-second", "The fictional color is amber.")
    retrieved = [
        RetrievedUnit(unit=first, score=2.0, rank=1),
        RetrievedUnit(unit=second, score=1.0, rank=2),
    ]
    metrics = _metrics(
        retrieved,
        GenerationOutput(answer=GOLD, citation_ids=("E1",)),
        build_evidence_package(retrieved),
        relevant=[first.unit_id, second.unit_id],
        supporting=[first.unit_id],
    )

    assert metrics["retrieval_hit_at_k"] == 1.0
    assert metrics["evidence_available"] is True


def test_case_b_correct_answer_invalid_citation() -> None:
    unit = _unit("u-correct", GOLD)
    retrieved = [RetrievedUnit(unit=unit, score=1.0, rank=1)]
    package = build_evidence_package(retrieved)
    metrics = _metrics(
        retrieved,
        GenerationOutput(answer=GOLD, citation_ids=("E999",)),
        package,
        relevant=["u-correct"],
        supporting=["u-correct"],
    )

    assert metrics["evidence_available"] is True
    assert metrics["answer_correct"] is True
    assert metrics["provenance_integrity"] is False
    assert metrics["supporting_units_cited"] is False


def test_case_c_valid_provenance_incorrect_answer() -> None:
    unit = _unit("u-correct", GOLD)
    retrieved = [RetrievedUnit(unit=unit, score=1.0, rank=1)]
    package = build_evidence_package(retrieved)
    metrics = _metrics(
        retrieved,
        GenerationOutput(answer="A different fictional answer.", citation_ids=("E1",)),
        package,
        relevant=["u-correct"],
        supporting=["u-correct"],
    )

    assert metrics["evidence_available"] is True
    assert metrics["answer_correct"] is False
    assert metrics["provenance_integrity"] is True
    assert metrics["supporting_units_cited"] is True
    assert metrics["end_to_end_traceability"] is True


def test_case_d_retrieval_miss_but_answer_correct() -> None:
    unit = _unit("u-correct", GOLD)
    metrics = _metrics(
        [],
        GenerationOutput(answer=GOLD, citation_ids=()),
        build_evidence_package([]),
        relevant=[unit.unit_id],
        supporting=[unit.unit_id],
    )

    assert metrics["evidence_available"] is False
    assert metrics["answer_correct"] is True
    assert metrics["provenance_integrity"] is False
    assert metrics["end_to_end_traceability"] is False


def test_case_e_valid_citation_wrong_supporting_unit() -> None:
    correct = _unit("u-correct", GOLD)
    wrong = _unit("u-wrong", "The fictional color is amber.")
    retrieved = [
        RetrievedUnit(unit=correct, score=2.0, rank=1),
        RetrievedUnit(unit=wrong, score=1.0, rank=2),
    ]
    package = build_evidence_package(retrieved)
    metrics = _metrics(
        retrieved,
        GenerationOutput(answer=GOLD, citation_ids=("E2",)),
        package,
        relevant=["u-correct"],
        supporting=["u-correct"],
    )

    assert metrics["evidence_available"] is True
    assert metrics["answer_correct"] is True
    assert metrics["provenance_integrity"] is True
    assert metrics["supporting_units_cited"] is False
    assert metrics["end_to_end_traceability"] is False


def test_empty_citation_is_provenance_failure() -> None:
    unit = _unit("u-correct", GOLD)
    result = resolve_provenance(
        GenerationOutput(answer=GOLD, citation_ids=()),
        build_evidence_package([unit]),
    )

    assert result.valid is False
    assert result.errors == ("no_citations",)


def test_mixed_valid_invalid_citations_fail_provenance() -> None:
    unit = _unit("u-correct", GOLD)
    result = resolve_provenance(
        GenerationOutput(answer=GOLD, citation_ids=("E1", "E999")),
        build_evidence_package([unit]),
    )

    assert result.valid is False
    assert result.invalid_citations == ("E999",)
    assert [item.citation_id for item in result.resolved] == ["E1"]


def test_duplicate_citation_policy_rejects_duplicates() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        GenerationOutput(answer=GOLD, citation_ids=("E1", "E1"))


def test_exact_answer_evaluator_normalizes_case_and_whitespace_only() -> None:
    output = {"answer": "  THE fictional limit is 72 units. ", "citation_ids": []}

    assert answer_correct(output, "the fictional limit is 72 units.") is True
    assert answer_correct(output, "The fictional limit is 73 units.") is False
