"""Structured generation contracts and an API-free demo generator."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from .schema import EvidencePackage


@dataclass(frozen=True)
class GenerationOutput:
    """The only output a generator needs to provide to provenance software."""

    answer: str
    citation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.answer, str):
            raise ValueError("answer must be a string")
        if any(not isinstance(citation_id, str) or not citation_id for citation_id in self.citation_ids):
            raise ValueError("citation_ids must contain non-empty strings")
        if len(set(self.citation_ids)) != len(self.citation_ids):
            raise ValueError("citation_ids must not contain duplicates")

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "GenerationOutput":
        if set(payload) != {"answer", "citation_ids"}:
            raise ValueError("structured output must contain answer and citation_ids only")
        answer = payload["answer"]
        citation_ids = payload["citation_ids"]
        if not isinstance(answer, str):
            raise ValueError("answer must be a string")
        if not isinstance(citation_ids, list) or not all(
            isinstance(citation_id, str) for citation_id in citation_ids
        ):
            raise ValueError("citation_ids must be a JSON list of strings")
        return cls(answer=answer, citation_ids=tuple(citation_ids))

    def to_dict(self) -> dict[str, object]:
        return {"answer": self.answer, "citation_ids": list(self.citation_ids)}


class Generator(Protocol):
    """Generation contract shared by mock and optional external adapters."""

    def generate(self, question: str, evidence_package: EvidencePackage) -> GenerationOutput:
        ...


class MockGenerator:
    """Return the first package item as a deterministic API-free demonstration."""

    def generate(self, question: str, evidence_package: EvidencePackage) -> GenerationOutput:
        del question
        if not evidence_package.items:
            return GenerationOutput(answer="Insufficient evidence.", citation_ids=())
        item = next(iter(evidence_package.items.values()))
        return GenerationOutput(answer=item.unit.text, citation_ids=(item.citation_id,))
