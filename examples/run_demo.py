"""Run the complete synthetic pipeline without network access or credentials."""

from __future__ import annotations

import json
from pathlib import Path

from traceable_rag.corpus import load_jsonl_records, load_knowledge_units
from traceable_rag.evaluation import evaluate_traceability
from traceable_rag.evidence import build_evidence_package
from traceable_rag.generation import MockGenerator
from traceable_rag.provenance import resolve_provenance
from traceable_rag.retrieval import BM25Retriever


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    units = load_knowledge_units(root / "examples" / "synthetic_corpus.jsonl")
    question = load_jsonl_records(root / "examples" / "synthetic_questions.jsonl")[0]
    retriever = BM25Retriever(units)
    retrieved = retriever.retrieve(question["question"], top_k=3)
    evidence_package = build_evidence_package(retrieved)
    generated = MockGenerator().generate(question["question"], evidence_package)
    resolved = resolve_provenance(generated, evidence_package)
    metrics = evaluate_traceability(
        retrieved,
        question["relevant_unit_ids"],
        generated,
        evidence_package,
        gold_answer=question["gold_answer"],
        supporting_unit_ids=question["supporting_unit_ids"],
        k=3,
    )

    print("Question")
    print(question["question"])
    print("\nRetrieved evidence")
    for result in retrieved:
        print(f"{result.rank}. {result.unit.unit_id} (score={result.score:.3f})")
    print("\nEvidence package")
    print(json.dumps(evidence_package.as_dict(), indent=2, ensure_ascii=False))
    print("\nStructured answer")
    print(json.dumps(generated.to_dict(), indent=2, ensure_ascii=False))
    print("\nResolved provenance")
    print(json.dumps(resolved.to_dict(), indent=2, ensure_ascii=False))
    print("\nTraceability metrics")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
