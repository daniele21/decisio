# Changelog

Decisio is pre-release. Until the first stable release, this file records product-facing repository milestones rather than every experimental commit.

## Unreleased

### Added

- training-free comparative semantic scorer over runtime-defined candidates;
- independent semantic v1, direct-letter and generated JSON baselines;
- Qwen3.5 reference backend with candidate batching and selected-vocabulary projection;
- frozen paired scorer gate with order perturbation and auditable raw evidence;
- repeated balanced performance trials with CUDA synchronization, throughput and peak-memory reporting;
- constraint-first Snake, support-routing and policy-gate examples;
- repository-specific engineering, contribution, security and benchmark documentation.

### Changed

- deterministic constraints are applied before semantic scoring;
- exact score ties are resolved independently of candidate presentation order;
- request/result contracts reject silent coercion, ambiguous duplicate descriptions and non-finite values;
- documentation now separates current implementation from planned architecture.

### Pending evidence

- representative Qwen3.5-4B BF16/CUDA scorer gate;
- answerability;
- shared-prefix/cache reuse;
- stable high-level Python API;
- release-grade packaging/runtime evidence.

## 0.1.0a0

Initial experimental Decisio package version. No stable API or performance claim is implied by this version.
