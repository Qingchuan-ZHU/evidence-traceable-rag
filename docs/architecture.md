# Architecture

The reference pipeline deliberately has small, inspectable boundaries:

```text
KnowledgeUnit records
        |
        v
    Retriever  ------------------------------+
        |                                    |
        v                                    |
RetrievedUnit list                           |
        |                                    |
        v                                    |
EvidencePackage { E1, E2, ... }              |
        |                                    |
        v                                    |
Generator -> { answer, citation_ids }       |
        |                                    |
        +-------------> deterministic resolver
                                      |
                                      v
                         document/page/clause metadata
```

## Contracts

`KnowledgeUnit` is the corpus-level record. It owns the stable unit identity,
document identity, page, clause, text, and optional metadata.

`Retriever` returns ranked `RetrievedUnit` objects. The bundled implementation
is a small in-memory BM25 retriever so the demo has no model download or service
dependency.

`EvidencePackage` creates a new local namespace for every retrieval result. Its
keys are `E1`, `E2`, and so on; each item stores the unit ID and software-owned
metadata required for later resolution.

`Generator` returns only an answer and citation IDs. `MockGenerator` is provided
for deterministic tests. An application can implement the same protocol with
an external language model without changing provenance resolution.

`resolve_provenance` checks each returned ID against the current package. It
never accepts document, page, or clause strings authored by the generator as
authoritative provenance.

## Invariants

1. Local citation IDs are meaningful only inside their evidence package.
2. An unknown citation ID is a provenance failure.
3. Resolved metadata is read from the package's `KnowledgeUnit`.
4. Answer evaluation and provenance evaluation remain separate metrics.
