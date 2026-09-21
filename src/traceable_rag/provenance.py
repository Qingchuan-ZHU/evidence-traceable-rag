"""Deterministic resolution from local citation IDs to package metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .generation import GenerationOutput
from .schema import EvidencePackage


@dataclass(frozen=True)
class ResolvedProvenance:
    citation_id: str
    unit_id: str
    document_id: str
    page: int
    clause: str

    def to_dict(self) -> dict[str, object]:
        return {
            "citation_id": self.citation_id,
            "unit_id": self.unit_id,
            "document_id": self.document_id,
            "page": self.page,
            "clause": self.clause,
        }


@dataclass(frozen=True)
class ProvenanceResult:
    valid: bool
    resolved: tuple[ResolvedProvenance, ...]
    invalid_citations: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "resolved": [item.to_dict() for item in self.resolved],
            "invalid_citations": list(self.invalid_citations),
            "errors": list(self.errors),
        }


def _parse_output(
    answer_output: GenerationOutput | Mapping[str, object],
) -> tuple[GenerationOutput | None, str | None]:
    if isinstance(answer_output, GenerationOutput):
        return answer_output, None
    try:
        return GenerationOutput.from_dict(answer_output), None
    except (TypeError, ValueError) as exc:
        return None, str(exc)


def resolve_provenance(
    answer_output: GenerationOutput | Mapping[str, object],
    evidence_package: EvidencePackage,
) -> ProvenanceResult:
    """Resolve only IDs present in the current evidence package."""

    output, parse_error = _parse_output(answer_output)
    if output is None:
        return ProvenanceResult(
            valid=False,
            resolved=(),
            errors=(f"structured_output_invalid: {parse_error}",),
        )
    if not output.citation_ids:
        return ProvenanceResult(
            valid=False,
            resolved=(),
            errors=("no_citations",),
        )

    resolved: list[ResolvedProvenance] = []
    invalid: list[str] = []
    for citation_id in output.citation_ids:
        item = evidence_package.get(citation_id)
        if item is None:
            invalid.append(citation_id)
            continue
        unit = item.unit
        resolved.append(
            ResolvedProvenance(
                citation_id=citation_id,
                unit_id=unit.unit_id,
                document_id=unit.document_id,
                page=unit.page,
                clause=unit.clause,
            )
        )
    return ProvenanceResult(
        valid=not invalid,
        resolved=tuple(resolved),
        invalid_citations=tuple(invalid),
        errors=("invalid_citation",) if invalid else (),
    )
