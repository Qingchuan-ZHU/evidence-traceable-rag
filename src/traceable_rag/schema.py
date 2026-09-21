"""Small, explicit data contracts used by the reference pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

_CITATION_ID_RE = re.compile(r"^E[1-9][0-9]*$")


@dataclass(frozen=True)
class KnowledgeUnit:
    """A retrievable unit with stable document metadata."""

    unit_id: str
    document_id: str
    page: int
    clause: str
    text: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.unit_id.strip():
            raise ValueError("unit_id must not be empty")
        if not self.document_id.strip():
            raise ValueError("document_id must not be empty")
        if isinstance(self.page, bool) or not isinstance(self.page, int) or self.page < 1:
            raise ValueError("page must be a positive integer")
        if not self.clause.strip():
            raise ValueError("clause must not be empty")
        if not self.text.strip():
            raise ValueError("text must not be empty")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_dict(cls, record: Mapping[str, Any]) -> "KnowledgeUnit":
        required = {"unit_id", "document_id", "page", "clause", "text"}
        missing = required.difference(record)
        if missing:
            raise ValueError(f"knowledge unit missing fields: {sorted(missing)}")
        return cls(
            unit_id=str(record["unit_id"]),
            document_id=str(record["document_id"]),
            page=record["page"],
            clause=str(record["clause"]),
            text=str(record["text"]),
            metadata=record.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "document_id": self.document_id,
            "page": self.page,
            "clause": self.clause,
            "text": self.text,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EvidenceItem:
    """One item in an evidence-package-local citation namespace."""

    citation_id: str
    unit: KnowledgeUnit

    def to_dict(self) -> dict[str, Any]:
        metadata = {
            **dict(self.unit.metadata),
            "document_id": self.unit.document_id,
            "page": self.unit.page,
            "clause": self.unit.clause,
        }
        return {
            "unit_id": self.unit.unit_id,
            "text": self.unit.text,
            "metadata": metadata,
        }


@dataclass(frozen=True)
class EvidencePackage:
    """Ordered evidence items addressed by local IDs such as ``E1`` and ``E2``."""

    items: Mapping[str, EvidenceItem]

    def __post_init__(self) -> None:
        normalized = dict(self.items)
        for citation_id, item in normalized.items():
            if not isinstance(citation_id, str) or _CITATION_ID_RE.fullmatch(citation_id) is None:
                raise ValueError(f"invalid local citation ID: {citation_id}")
            if item.citation_id != citation_id:
                raise ValueError("evidence item ID does not match package key")
        object.__setattr__(self, "items", normalized)

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def get(self, citation_id: str) -> EvidenceItem | None:
        return self.items.get(citation_id)

    def as_dict(self) -> dict[str, dict[str, Any]]:
        return {citation_id: item.to_dict() for citation_id, item in self.items.items()}
