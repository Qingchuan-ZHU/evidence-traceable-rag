"""A compact deterministic lexical retriever with a stable interface."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol, Sequence

from .schema import KnowledgeUnit

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")


def tokenize(text: str) -> list[str]:
    """Tokenize English-like synthetic text deterministically."""

    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


@dataclass(frozen=True)
class RetrievedUnit:
    unit: KnowledgeUnit
    score: float
    rank: int


class Retriever(Protocol):
    """Minimal retrieval contract used by the pipeline."""

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedUnit]:
        ...


class BM25Retriever:
    """Small in-memory BM25 retriever with no external model or service."""

    def __init__(
        self,
        units: Sequence[KnowledgeUnit],
        *,
        k1: float = 1.2,
        b: float = 0.75,
    ) -> None:
        if not units:
            raise ValueError("BM25Retriever requires at least one knowledge unit")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 parameters are out of range")
        self.units = tuple(units)
        self.k1 = k1
        self.b = b
        self._term_frequencies = tuple(
            Counter(tokenize(f"{unit.clause} {unit.text}")) for unit in self.units
        )
        self._document_frequency: Counter[str] = Counter()
        for frequencies in self._term_frequencies:
            self._document_frequency.update(frequencies.keys())
        self._lengths = tuple(sum(frequencies.values()) for frequencies in self._term_frequencies)
        self._average_length = sum(self._lengths) / len(self._lengths)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedUnit]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        query_terms = tokenize(query)
        if not query_terms:
            return []
        query_counts = Counter(query_terms)
        scored: list[tuple[float, KnowledgeUnit]] = []
        document_count = len(self.units)
        for index, unit in enumerate(self.units):
            frequencies = self._term_frequencies[index]
            length = self._lengths[index]
            score = 0.0
            for term, query_frequency in query_counts.items():
                term_frequency = frequencies.get(term, 0)
                if not term_frequency:
                    continue
                document_frequency = self._document_frequency[term]
                idf = math.log(
                    1.0
                    + (document_count - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                denominator = term_frequency + self.k1 * (
                    1.0 - self.b + self.b * length / self._average_length
                )
                score += idf * (
                    term_frequency * (self.k1 + 1.0) / denominator
                ) * query_frequency
            if score > 0:
                scored.append((score, unit))
        scored.sort(key=lambda entry: (-entry[0], entry[1].unit_id))
        return [
            RetrievedUnit(unit=unit, score=score, rank=rank)
            for rank, (score, unit) in enumerate(scored[:top_k], start=1)
        ]
