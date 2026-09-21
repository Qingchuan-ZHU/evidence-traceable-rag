"""Synthetic reference implementation of evidence-traceable RAG."""

from .evidence import build_evidence_package
from .evaluation import (
    AnswerEvaluator,
    EvidenceSupportEvaluator,
    ExactMatchAnswerEvaluator,
    answer_correct,
    evaluate_traceability,
    supporting_units_cited,
)
from .generation import GenerationOutput, Generator, MockGenerator
from .provenance import ProvenanceResult, resolve_provenance
from .schema import EvidenceItem, EvidencePackage, KnowledgeUnit

__all__ = [
    "EvidenceItem",
    "EvidencePackage",
    "AnswerEvaluator",
    "EvidenceSupportEvaluator",
    "ExactMatchAnswerEvaluator",
    "GenerationOutput",
    "Generator",
    "KnowledgeUnit",
    "MockGenerator",
    "ProvenanceResult",
    "build_evidence_package",
    "answer_correct",
    "evaluate_traceability",
    "resolve_provenance",
    "supporting_units_cited",
]
