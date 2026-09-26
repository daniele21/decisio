# Changelog

Decisio is pre-release. Until the first stable release, this file records product-facing repository
milestones rather than every experimental commit.

## Unreleased

### Added

- local GGUF + llama.cpp reference runtime with exact artifact/runtime provenance;
- reusable single-sequence model-state snapshot/restore with a bounded repeated-state cache;
- stateful direct A/B/C action readout with zero generated answer tokens;
- comparative semantic v2, semantic v1, direct-letter and generated JSON evidence paths;
- frozen short/fresh and repeated-state benchmark contracts with retained machine-readable evidence;
- constraint-first Snake, support-routing and policy-gate examples;
- Snake controller-quality benchmark with a bounded moving-body planner and append-only ledger;
- branded Snake UI, trace/video evidence and explanatory repository graphics;
- optional Apple Metal execution as a distinct runtime identity;
- repository-specific engineering, contribution, security and benchmark documentation;
- supported high-level `DecisionSession` for direct stateful choices, same-prompt fresh oracle,
  runtime reuse metrics and deterministic model lifecycle.

### Changed

- the product thesis is now stable-context reuse over changing state rather than generic semantic
  scoring;
- deterministic constraints are applied before model scoring;
- exact score ties are resolved independently of candidate presentation order;
- request/result contracts reject silent coercion, ambiguous duplicate descriptions and non-finite
  values;
- direct logits are documented as an internal readout primitive rather than the product
  differentiator;
- documentation separates implemented, experimental and planned behavior.

### Evidence status

- the pinned 2B short/fresh semantic-v2 gate remains **FAIL** on its unchanged criteria;
- 0.8B real-model smoke proves fresh/reused correctness and physical-token reduction directionally;
- repeated-state gate v3 on the pinned 2B CPU identity remains the scoped semantic promotion gate;
- representative 2B Snake controller screening and a later holdout remain pending.

### Still planned

- answerability/abstention;
- calibration artifacts;
- release-grade promotion and package publication.

## 0.1.0a0

Initial experimental Decisio package version. No stable API or performance claim is implied by this
version.
