# Evidence-Traceable RAG

This repository provides a synthetic reference implementation of
machine-verifiable evidence provenance for retrieval-augmented generation.

It is not the engineering case-study dataset or the internal experimental
repository. Every example in this repository is original synthetic data.

## Motivation

Retrieval success, answer correctness, and provenance integrity are related but
distinct properties. A fluent answer can still cite an unavailable evidence
item, and a valid citation can still support an incorrect answer.

The central design principle is:

> LLM generates the answer; software determines provenance.

## Reliability layers

The reference implementation keeps three layers separate:

1. **Evidence Availability** — did retrieval return the required knowledge unit?
2. **Answer Correctness** — does the answer agree with the task's deterministic
   label or an explicitly configured evaluator?
3. **Provenance Integrity** — do all citation IDs resolve to the current
   evidence package?

Retrieval success != answer correctness != provenance integrity.

## Core design

```text
Question
   |
   v
retrieval
   |
   v
evidence package { E1, E2, ... }
   |
   v
answer + local citation IDs
   |
   v
deterministic provenance resolver
```

Citation IDs are local to one evidence package. The generator may return `E1`
or `E2`, but it does not author document, page, or clause metadata. The
resolver obtains those fields only from the package that software constructed.

## Quick start

```bash
python -m pip install -e ".[test]"
python examples/run_demo.py
```

The demo runs without a GPU, network access, API key, or downloaded model. It
prints the question, retrieved evidence, evidence package, structured answer,
and resolved provenance.

Run the test suite with:

```bash
pytest -q
```

## Synthetic data

The corpus uses an invented manual and invented rules such as a fictional
operating limit and a fictional inspection interval. It is explicitly marked:

> SYNTHETIC DATA — NOT DERIVED FROM ANY TECHNICAL STANDARD.

These rules exist only to demonstrate document identity, page identity, clause
identity, local citation IDs, and deterministic provenance resolution.

## Evaluation

The package exposes a deterministic synthetic evaluator for three distinct
layers:

- **Evidence Availability** — required evidence reached the generation stage;
- **Answer Correctness** — the answer exactly matches the normalized synthetic
  gold answer under `ExactMatchAnswerEvaluator`;
- **Provenance Integrity** — every selected citation ID belongs to the current
  evidence package and resolves to software-owned metadata.

The evaluator also reports:

- `retrieval_hit_at_k`
- `evidence_available`
- `answer_correct`
- `provenance_integrity`
- `structured_output_valid`
- `citation_ids_valid`
- `provenance_resolved`
- `supporting_units_cited`
- `end_to_end_traceability`

`supporting_units_cited` is a deterministic synthetic proxy: all expected
supporting unit IDs must be represented among resolved citations. It is not a
semantic evidence-support judge. **Provenance integrity != semantic evidence
support.** Semantic evidence support asks whether the cited evidence actually
supports the answer and requires an independently audited human or LLM
evaluator.

The reference `end_to_end_traceability` metric is defined as:

```text
structured_output_valid
AND provenance_integrity
AND supporting_units_cited
```

This reference metric is a deterministic synthetic proxy for end-to-end
machine-verifiable traceability. A production deployment may replace
supporting-unit coverage with an independently audited semantic support
evaluator.

See [docs/evaluation_framework.md](docs/evaluation_framework.md) for the
three-layer evaluation framework and illustrative cases.

## Failure-mode demonstration

The synthetic tests make the separation observable:

| Case | Evidence | Answer | Citation | Supporting units |
| --- | --- | --- | --- | --- |
| A | available | correct | valid | covered |
| B | available | correct | invalid | not covered |
| C | available | incorrect | valid | covered |
| D | missed | happens to be correct | unavailable | not covered |
| E | available | correct | valid | wrong unit cited |

See [tests/test_failure_modes.py](tests/test_failure_modes.py).

## Paper

This repository accompanies:

“Disentangling Answer Correctness and Evidence Provenance in
Retrieval-Augmented Generation for Engineering Standards”.

The public manuscript is maintained separately; see [paper/README.md](paper/README.md).
This repository does not reproduce restricted case-study experiments.

## Data and confidentiality boundary

No proprietary engineering corpus, technical-standard text, private benchmark,
or internal experimental artifact is distributed. The repository contains no
real standards, parsed standards, model weights, adapter files, or private
evaluation outputs.

See [docs/data_boundary.md](docs/data_boundary.md) for the release boundary and
[docs/reproducibility.md](docs/reproducibility.md) for the offline reproducible
workflow.

The generic release checks are also runnable locally:

```bash
python scripts/check_public_release.py
python scripts/check_git_history.py
```

## License

Software code is released under the Apache License 2.0. Original synthetic data,
documentation, figures, and research artifacts are released under CC BY 4.0;
see [NOTICE](NOTICE), [LICENSE](LICENSE), and [LICENSE-DATA](LICENSE-DATA).
