# Evaluation framework

This repository evaluates a pipeline in three layers. The layers answer
different questions and must not be collapsed into one accuracy number.

## Evidence Availability

Evidence Availability asks whether every required evidence unit is present in
the final `EvidencePackage` passed to generation. `retrieval_hit_at_k` remains
a retrieval-stage indicator, while `evidence_available` is computed from the
package contents, so the two metrics can differ.

## Answer Correctness

Answer Correctness asks whether the answer substantively matches the task's
evaluation criterion. In this synthetic repository the criterion is an
explicit `gold_answer`, evaluated by `ExactMatchAnswerEvaluator` after
case-folding and whitespace normalization. This is a deterministic exact-match
reference evaluator, not a general semantic judge.

The `AnswerEvaluator` protocol allows a separately audited human or LLM
evaluator to be substituted in an application.

## Provenance Integrity

Provenance Integrity means that all model-selected citation IDs belong to the
current evidence package and deterministically resolve to software-owned source
metadata. An ID such as `E999` is invalid when it is absent from the package.
The resolver never accepts document, page, or clause strings authored by the
generator as authoritative provenance.

Therefore:

```text
retrieval success != answer correctness != provenance integrity
```

## Supporting-unit coverage

`supporting_units_cited` checks whether every expected synthetic supporting unit
ID is represented among resolved citations. It is a deterministic
supporting-unit coverage proxy for this reference corpus, not semantic
entailment, a semantic evidence-support judge, or a factual correctness judge.

## Semantic Evidence Support

Semantic Evidence Support asks whether the cited evidence actually supports the
answer. The default reference implementation does not claim to implement this
semantic judge. `EvidenceSupportEvaluator` is an interface point for an
independently audited human or LLM evaluator.

```text
provenance integrity != semantic evidence support
```

Valid provenance proves identity and resolution, not substantive support.

## End-to-End Traceability

The synthetic reference metric `end_to_end_traceability` requires:

```text
structured_output_valid
AND provenance_integrity
AND supporting_units_cited
```

This reference metric is a deterministic synthetic proxy for end-to-end
traceability. `answer_correct` is reported separately and is not part of this
metric. A production deployment may replace
supporting-unit coverage with an independently audited semantic support
evaluator.

## Illustrative synthetic cases

These cases use only the synthetic corpus:

| Case | Evidence | Answer | Citation | Supporting units | Result |
| --- | --- | --- | --- | --- | --- |
| A | available | correct | valid | covered | all reference layers pass |
| B | available | correct | invalid | not covered | provenance fails |
| C | available | incorrect | valid | covered | answer correctness fails; traceability can still pass |
| D | missed | happens to be correct | unavailable | not covered | answer correctness does not prove grounding |
| E | available | correct | valid | wrong unit cited | supporting-unit coverage fails |

The test names and assertions are in
[tests/test_failure_modes.py](../tests/test_failure_modes.py).
