import pytest

from traceable_rag.schema import EvidenceItem, EvidencePackage, KnowledgeUnit


def _unit() -> KnowledgeUnit:
    return KnowledgeUnit(
        unit_id="u-1",
        document_id="synthetic-doc",
        page=1,
        clause="1.1",
        text="A fictional rule.",
    )


@pytest.mark.parametrize("page", ["2", 2.0, True, None])
def test_invalid_page_type_raises_value_error(page) -> None:
    with pytest.raises(ValueError, match="page must be a positive integer"):
        KnowledgeUnit(
            unit_id="u-1",
            document_id="synthetic-doc",
            page=page,
            clause="1.1",
            text="A fictional rule.",
        )


@pytest.mark.parametrize("citation_id", ["E0", "E00", "E01", "E-1", "EX"])
def test_invalid_local_citation_ids_are_rejected(citation_id: str) -> None:
    item = EvidenceItem(citation_id=citation_id, unit=_unit())

    with pytest.raises(ValueError, match="invalid local citation ID"):
        EvidencePackage({citation_id: item})
