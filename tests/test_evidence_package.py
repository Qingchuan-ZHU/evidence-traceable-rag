from traceable_rag.evidence import build_evidence_package
from traceable_rag.retrieval import RetrievedUnit
from traceable_rag.schema import KnowledgeUnit


def test_evidence_package_uses_local_ids_and_preserves_metadata() -> None:
    unit = KnowledgeUnit(
        unit_id="u-1",
        document_id="synthetic-doc",
        page=4,
        clause="4.2",
        text="A fictional rule.",
        metadata={"topic": "demo"},
    )
    package = build_evidence_package([RetrievedUnit(unit=unit, score=1.0, rank=1)])

    assert list(package) == ["E1"]
    assert package.as_dict() == {
        "E1": {
            "unit_id": "u-1",
            "text": "A fictional rule.",
            "metadata": {
                "topic": "demo",
                "document_id": "synthetic-doc",
                "page": 4,
                "clause": "4.2",
            },
        }
    }
