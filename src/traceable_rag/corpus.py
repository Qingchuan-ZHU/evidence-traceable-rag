"""Offline JSONL loading for synthetic knowledge units."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import KnowledgeUnit


def load_jsonl_records(path: str | Path) -> list[dict[str, Any]]:
    """Load JSON records while allowing comment lines for dataset notices."""

    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"JSONL line {line_number} must contain an object")
            records.append(record)
    return records


def load_knowledge_units(path: str | Path) -> list[KnowledgeUnit]:
    """Load all knowledge-unit records from a JSONL file."""

    return [KnowledgeUnit.from_dict(record) for record in load_jsonl_records(path)]
