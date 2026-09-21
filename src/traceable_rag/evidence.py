"""Construction of evidence-package-local citation IDs."""

from __future__ import annotations

from collections.abc import Sequence

from .retrieval import RetrievedUnit
from .schema import EvidenceItem, EvidencePackage, KnowledgeUnit


def build_evidence_package(
    retrieved_units: Sequence[RetrievedUnit | KnowledgeUnit],
    *,
    max_items: int | None = None,
) -> EvidencePackage:
    """Create a fresh local citation namespace from retrieved units."""

    if max_items is not None and max_items < 1:
        raise ValueError("max_items must be positive")
    items: dict[str, EvidenceItem] = {}
    seen_unit_ids: set[str] = set()
    for result in retrieved_units:
        unit = result.unit if isinstance(result, RetrievedUnit) else result
        if unit.unit_id in seen_unit_ids:
            continue
        if max_items is not None and len(items) >= max_items:
            break
        citation_id = f"E{len(items) + 1}"
        items[citation_id] = EvidenceItem(citation_id=citation_id, unit=unit)
        seen_unit_ids.add(unit.unit_id)
    return EvidencePackage(items)
