"""Layered, deterministic traceability metrics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol

from .generation import GenerationOutput
from .provenance import resolve_provenance
from .retrieval import RetrievedUnit
from .schema import EvidencePackage, KnowledgeUnit

AnswerOutput = GenerationOutput | Mapping[str, object]


class AnswerEvaluator(Protocol):
    """Interface for answer evaluation, separate from provenance resolution."""

    def evaluate(self, answer_output: AnswerOutput, gold_answer: str) -> bool:
        ...


class EvidenceSupportEvaluator(Protocol):
    """Optional interface for independently audited semantic support judges."""

    def evaluate(
        self,
        answer_output: AnswerOutput,
        evidence_package: EvidencePackage,
    ) -> bool:
        ...


def _unit_id(result: RetrievedUnit | KnowledgeUnit) -> str:
    return result.unit.unit_id if isinstance(result, RetrievedUnit) else result.unit_id


def _as_generation_output(answer_output: AnswerOutput) -> GenerationOutput | None:
    if isinstance(answer_output, GenerationOutput):
        return answer_output
    try:
        return GenerationOutput.from_dict(answer_output)
    except (TypeError, ValueError):
        return None


def retrieval_hit_at_k(
    retrieved: Sequence[RetrievedUnit | KnowledgeUnit],
    relevant_unit_ids: Iterable[str],
    *,
    k: int = 5,
) -> float:
    if k < 1:
        raise ValueError("k must be positive")
    relevant = set(relevant_unit_ids)
    if not relevant:
        return 0.0
    return float(any(_unit_id(item) in relevant for item in retrieved[:k]))


def structured_output_valid(answer_output: AnswerOutput) -> bool:
    return _as_generation_output(answer_output) is not None


def citation_ids_valid(
    answer_output: AnswerOutput,
    evidence_package: EvidencePackage,
) -> bool:
    result = resolve_provenance(answer_output, evidence_package)
    return structured_output_valid(answer_output) and bool(result.resolved) and not result.invalid_citations


def provenance_resolved(
    answer_output: AnswerOutput,
    evidence_package: EvidencePackage,
) -> bool:
    return resolve_provenance(answer_output, evidence_package).valid


def provenance_integrity(
    answer_output: AnswerOutput,
    evidence_package: EvidencePackage,
) -> bool:
    """All selected citation IDs resolve to current package-owned metadata."""

    return provenance_resolved(answer_output, evidence_package)


def supporting_units_cited(
    answer_output: AnswerOutput,
    evidence_package: EvidencePackage,
    supporting_unit_ids: Iterable[str],
) -> bool:
    """Check deterministic coverage of gold synthetic supporting units."""

    expected = set(supporting_unit_ids)
    if not expected:
        return False
    result = resolve_provenance(answer_output, evidence_package)
    resolved_unit_ids = {item.unit_id for item in result.resolved}
    return result.valid and expected.issubset(resolved_unit_ids)


def _normalize_exact(text: str) -> str:
    return " ".join(text.casefold().split())


class ExactMatchAnswerEvaluator:
    """Deterministic synthetic evaluator using case-folded whitespace exact match."""

    def evaluate(self, answer_output: AnswerOutput, gold_answer: str) -> bool:
        output = _as_generation_output(answer_output)
        if output is None or not isinstance(gold_answer, str):
            return False
        return _normalize_exact(output.answer) == _normalize_exact(gold_answer)


def answer_correct(
    answer_output: AnswerOutput,
    gold_answer: str,
    evaluator: AnswerEvaluator | None = None,
) -> bool:
    """Evaluate answer correctness with an explicit deterministic default."""

    return (evaluator or ExactMatchAnswerEvaluator()).evaluate(answer_output, gold_answer)


def answer_correctness_exact(answer_output: AnswerOutput, gold_answer: str) -> bool:
    """Named convenience wrapper for the synthetic exact-match evaluator."""

    return ExactMatchAnswerEvaluator().evaluate(answer_output, gold_answer)


def evaluate_traceability(
    retrieved: Sequence[RetrievedUnit | KnowledgeUnit],
    relevant_unit_ids: Iterable[str],
    answer_output: AnswerOutput,
    evidence_package: EvidencePackage,
    *,
    gold_answer: str,
    supporting_unit_ids: Iterable[str],
    k: int = 5,
    answer_evaluator: AnswerEvaluator | None = None,
) -> dict[str, float | bool]:
    """Return three core layers and their auditable supporting indicators."""

    relevant_ids = tuple(relevant_unit_ids)
    supporting_ids = tuple(supporting_unit_ids)
    retrieval_hit = retrieval_hit_at_k(retrieved, relevant_ids, k=k)
    structured_valid = structured_output_valid(answer_output)
    provenance_valid = provenance_integrity(answer_output, evidence_package)
    supporting_covered = supporting_units_cited(
        answer_output,
        evidence_package,
        supporting_ids,
    )
    return {
        "retrieval_hit_at_k": retrieval_hit,
        "evidence_available": retrieval_hit == 1.0,
        "answer_correct": answer_correct(
            answer_output,
            gold_answer,
            evaluator=answer_evaluator,
        ),
        "provenance_integrity": provenance_valid,
        "structured_output_valid": structured_valid,
        "citation_ids_valid": citation_ids_valid(answer_output, evidence_package),
        "provenance_resolved": provenance_resolved(answer_output, evidence_package),
        "supporting_units_cited": supporting_covered,
        "end_to_end_traceability": structured_valid and provenance_valid and supporting_covered,
    }
