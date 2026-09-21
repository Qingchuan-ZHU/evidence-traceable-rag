from traceable_rag.evidence import build_evidence_package
from traceable_rag.generation import GenerationOutput
from traceable_rag.provenance import resolve_provenance
from traceable_rag.schema import KnowledgeUnit


def _package():
    return build_evidence_package(
        [
            KnowledgeUnit(
                unit_id="u-1",
                document_id="synthetic-doc",
                page=2,
                clause="2.1",
                text="A fictional rule.",
            )
        ]
    )


def test_valid_local_citation_resolves_to_package_metadata() -> None:
    result = resolve_provenance(
        GenerationOutput(answer="A fictional answer.", citation_ids=("E1",)),
        _package(),
    )

    assert result.valid is True
    assert result.invalid_citations == ()
    assert result.resolved[0].unit_id == "u-1"
    assert result.resolved[0].document_id == "synthetic-doc"
    assert result.resolved[0].page == 2
    assert result.resolved[0].clause == "2.1"


def test_mapping_contract_is_supported() -> None:
    result = resolve_provenance(
        {"answer": "A fictional answer.", "citation_ids": ["E1"]},
        _package(),
    )

    assert result.valid is True
