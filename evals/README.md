# Agent guidance evaluation

Use these five scenarios when the template changes materially. This folder is reference-template maintenance, not a copied per-PR gate for adopting repositories.

## Decision smoke review

Give an independent evaluator a scenario's request/evidence, the candidate's local guide/Skills/configuration and access to relevant sources. Ask for the next actions, necessary evidence and completion claim. Do not supply the rubric or previous answers. Restrict the exercise to read-only decisions; it does not authorize live repository mutations or external dispatch.

Review observable decisions against these criteria:

| Scenario | Required behavior |
| --- | --- |
| README | Bounded source/link checks and proportional integration review; no runtime suite or physical test solely for a typo. |
| Local bug | Distinguish observed connection state from unproven result delivery; change diagnostic strategy and gather discriminating evidence before a third production repair. |
| Shared contract | Preserve STRONG owner/consumer/serialization/journey gates; use remote automation without making the user a deterministic test runner. |
| UI integration | Missing video blocks the material UI integration claim; capture/verify FULL_MEDIA automatically. Physical acceptance stays deferred to release. |
| Resume | Recheck H2/B2, use excluded hypotheses as evidence pointers, reject reuse on moved base, preserve the physical release obligation before deleting the integration plan. |

Score each as PASS/FAIL with a short evidence pointer. Record model/settings if available, snapshot, evaluator input and outputs. Unknown telemetry stays unknown. A decision smoke PASS does not establish correct code changes, end-to-end performance or measured token savings.

## Comparing effectiveness

For claims about improvement, replay representative implementation tasks in isolated, comparable repository snapshots with the same model/settings/tools/environment. Use independently checkable acceptance tests and review; repeat enough to expose variability. Do not run agents against production as a benchmark.

Record correct completions and regressions first. Then compare actual input/output/cached tokens when observable, repair attempts, first useful feedback time, duplicate reads and redundant gate runs. Keep raw evidence references and distinguish runtime token counts from `verify_agent_context.py` character estimates. Report cost per correct outcome along with failure rate; do not hide unsuccessful attempts.

The route verifier and its regression tests validate accounting/source integrity only. They do not execute an LLM or certify semantic correctness of the guidance. Static CI remains cheap; behavioral evaluations run at significant template checkpoints.
