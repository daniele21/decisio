# AI systems profile

Add when probabilistic ML/LLM components materially affect product behavior, regardless of whether models run locally or through a managed provider.

This profile specializes the universal product, operating, validation and E2E contracts for production AI systems. It does not require one model provider, prompt framework, vector database or evaluation platform.

Minimum additions:

- every material AI capability has an explicit product/system outcome, authoritative source(s) of truth and a defined boundary between probabilistic behavior and deterministic business logic;
- model/provider/configuration identity is versioned or otherwise reconstructable for evaluation and incident diagnosis;
- prompts/system instructions, tool schemas, retrieval configuration and other behavior-shaping assets are treated as versioned system inputs when they can materially change output;
- structured output is validated before crossing trusted application boundaries; malformed or unsupported model output is an expected failure mode, not an impossible state;
- model selection considers quality, latency, cost, privacy/security, availability and operational constraints rather than benchmark quality alone;
- fallbacks/degradation are explicit where required: a fallback must preserve the product's safety/trust contract, not merely produce an answer;
- representative offline evaluation exists for material AI behavior before integration/release changes are declared improved;
- evaluation sets include provenance/ownership and stable case identity; sensitive production data is not copied into test fixtures without an explicit lawful/privacy-safe process;
- AI observability captures enough metadata to diagnose model/retrieval/tool/workflow behavior without logging sensitive prompts, source documents or personal data by default;
- cost/token/latency budgets are measurable when they materially affect scale, UX or viability;
- online/user feedback is evidence, not ground truth by default; evaluation labels and production signals keep their uncertainty/provenance explicit;
- AI-generated claims that require grounding carry enough source/evidence linkage to audit why the output was accepted;
- changes to models, prompts, retrieval, tools, schemas or orchestration trigger validation based on behavioral blast radius even when application code is unchanged.

## Deterministic/probabilistic boundary

For each material AI workflow, the architecture should make it possible to answer:

1. What does the model decide or generate?
2. What remains deterministic application logic?
3. What data is authoritative and where is it owned?
4. Which model outputs are advisory versus allowed to mutate state or trigger effects?
5. Which outputs require schema/rule/policy validation or human approval?
6. What happens when the model is unavailable, slow, malformed, inconsistent or uncertain?

Prefer deterministic code for calculations, authorization, invariants, durable state transitions and irreversible side effects when probabilistic reasoning is not needed.

## Behavior identity

A reproducible AI result may depend on more than source commit. Record the smallest material behavior identity, such as:

- source/build identity;
- model/provider and model version/family;
- model parameters where material;
- prompt/system-instruction version;
- tool/schema version;
- retrieval index/corpus/configuration identity;
- evaluation dataset/version;
- workflow/orchestrator version.

Do not claim bit-for-bit reproducibility when the provider/runtime is nondeterministic. The goal is reconstructable configuration and comparable evidence.

## Evaluation contract

Separate at least three evidence layers when applicable:

```text
component evaluation
-> workflow/system evaluation
-> production outcome/operational evidence
```

Component evaluation may measure extraction/classification/structured-output/retrieval behavior. Workflow evaluation proves the assembled user/system outcome and failure paths. Production evidence observes real latency, cost, availability, distribution drift or product outcomes where needed.

Choose metrics that match the task. Examples include precision/recall/F1 for extraction/classification, Recall@K/MRR/NDCG for retrieval/ranking, schema adherence and groundedness for generated structured answers, and task success/trajectory efficiency for agents. Do not collapse heterogeneous criteria into one opaque "AI score" unless its interpretation and trade-offs are explicit.

Regression gates should compare against an established baseline/tolerance, not require every probabilistic example to be identical. Keep flaky/non-deterministic judge behavior bounded through deterministic checks, repeated sampling where justified, stable judge configuration and manual adjudication for disputed high-impact cases.

## Retrieval/grounding

When retrieval contributes to behavior:

- corpus/index ownership and refresh semantics are explicit;
- tenant/access-control filters are enforced before or during retrieval rather than delegated to the LLM;
- retrieval evaluation is independent from final answer evaluation;
- retrieved evidence is attributable enough to diagnose missing, irrelevant or stale context;
- chunking, embedding, query rewriting, hybrid search and reranking are configuration choices with evaluation evidence, not assumed improvements;
- the model must not silently convert absence of evidence into evidence of absence when the product domain requires caution.

## Observability

Prefer traces that make the AI path inspectable at the level needed for diagnosis, for example:

```text
request/workflow
├── retrieval
├── model call
├── validation
├── tool/action
└── final result
```

Useful metadata may include model identity, latency, token counts, cost estimate, retry/fallback reason, retrieval result IDs/scores, tool names/status and validation outcome. Sensitive raw prompt/document/tool payload capture must be opt-in and governed by the product's privacy/security policy.

Operational health and semantic quality are separate: HTTP 200 does not prove the AI task succeeded.

## AI change risk

Treat changes to the following as behavior changes even without broad code diffs:

- model/provider/version;
- system prompt/instruction templates;
- decoding/response parameters;
- output schemas/parsers;
- retrieval corpus/index/chunking/embedding/reranking;
- tool definitions/permissions;
- safety/policy/guardrail configuration;
- routing/fallback logic;
- evaluation rubric/judges.

Use the smallest sufficient regression/evaluation cone during iteration, then exact affected workflow evidence at integration and representative cost/latency/quality evidence at release when those claims are material.

## Relationship to local-ai

`ai-systems` covers behavioral quality, evaluation, grounding, provider/model identity and probabilistic boundaries. `local-ai` covers local model artifact/runtime/resource lifecycle, hardware fidelity, memory pressure and cleanup. Adopt both when both concerns apply; do not duplicate their rules locally.
