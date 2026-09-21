# Data and confidentiality boundary

This repository is an independent public reference implementation. Its data
boundary is intentionally narrow.

## Included

- original synthetic knowledge units;
- original synthetic questions and deterministic labels;
- generic retrieval, evidence-package, generation-contract, resolver, and
  evaluation code;
- documentation that explains the generic mechanism;
- tests and an offline demo.

The synthetic corpus is marked in its file header:

> SYNTHETIC DATA — NOT DERIVED FROM ANY TECHNICAL STANDARD.

## Excluded

The repository does not distribute or depend on proprietary engineering
corpora, technical-standard text, parsed source material, private benchmarks,
model outputs, prompts, adapter files, model weights, customer information,
organization information, or confidential reports.

The paper directory contains a pointer only. A manuscript is not copied into
this repository by the reference implementation.

## Release rule

All examples must remain independently authored synthetic material. If a future
contributor cannot establish that a proposed file is original and publishable,
the file must remain outside this repository until its status is resolved.
