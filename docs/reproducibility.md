# Reproducibility

The reference workflow is intentionally offline and CPU-friendly.

## Environment

- Python 3.11 or 3.12;
- no GPU requirement;
- no network requirement after the package is available;
- no API key;
- no external model download.

## Commands

```bash
python -m pip install -e ".[test]"
pytest -q
python examples/run_demo.py
python scripts/check_public_release.py
python scripts/check_git_history.py
```

The test workflow runs the same package checks on Python 3.11 and 3.12. The
demo uses a deterministic BM25 retriever and `MockGenerator`, so its output is
repeatable for the checked-in synthetic inputs.

`GenerationOutput` rejects duplicate citation IDs. `EvidencePackage` accepts
only positive local IDs matching `E1`, `E2`, and so on. These strict contracts
make malformed or ambiguous provenance fail closed.

## Extending the reference implementation

An application may replace the retriever or generator behind the existing
contracts. It should preserve the evidence-package-local citation namespace and
continue resolving provenance from package-owned metadata. Any external judge
should be recorded as a separate evaluation component with its own inputs and
outputs.
