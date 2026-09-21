from traceable_rag.evidence import build_evidence_package
from traceable_rag.generation import GenerationOutput
from traceable_rag.provenance import resolve_provenance
from traceable_rag.schema import KnowledgeUnit


def test_unknown_citation_is_a_provenance_failure() -> None:
    unit = KnowledgeUnit(
        unit_id="u-1",
        document_id="synthetic-doc",
        page=1,
        clause="1.1",
        text="A fictional rule.",
    )
    result = resolve_provenance(
        GenerationOutput(answer="A fictional answer.", citation_ids=("E999",)),
        build_evidence_package([unit]),
    )

    assert result.valid is False
    assert result.invalid_citations == ("E999",)
    assert result.resolved == ()
    assert result.errors == ("invalid_citation",)


def test_malformed_structured_output_is_rejected() -> None:
    result = resolve_provenance(
        {"answer": "A fictional answer.", "citation_ids": "E1"},
        build_evidence_package(
            [
                KnowledgeUnit(
                    unit_id="u-1",
                    document_id="synthetic-doc",
                    page=1,
                    clause="1.1",
                    text="A fictional rule.",
                )
            ]
        ),
    )

    assert result.valid is False
    assert result.errors[0].startswith("structured_output_invalid:")
