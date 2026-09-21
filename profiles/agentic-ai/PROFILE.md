# Agentic AI profile

Add when an LLM/model can dynamically select tools, plan steps, maintain execution state/memory or delegate to other agents.

This profile specializes `ai-systems`; adopt `ai-systems` together with this profile unless an equivalent stronger local standard already owns those semantics.

The governing rule is:

> Give probabilistic agents only the autonomy that materially improves the outcome; keep authorization, invariants and irreversible state transitions behind deterministic boundaries.

Minimum additions:

- the agent's goal, allowed autonomy and termination conditions are explicit;
- every tool is a bounded capability with typed/validated input and output, explicit owner and known side effects;
- the model does not receive arbitrary database, shell, cloud or admin authority when a narrower tool contract can express the required action;
- authentication/authorization is enforced by deterministic infrastructure/application policy, not by prompt instructions;
- agent/session state, long-term memory and authoritative application data have distinct owners and retention semantics;
- source-of-truth facts are re-read from authoritative systems when required; memory is not silently promoted into authoritative business state;
- maximum steps/time/tokens/concurrency and cancellation behavior are bounded for every production trajectory;
- retries distinguish model/tool/transient transport failures from business rejection and non-idempotent side effects;
- external side effects are idempotent or protected against duplicate execution; high-impact actions use approval/policy boundaries proportional to risk;
- tool calls, model calls, policy decisions and terminal outcomes are traceable enough to reconstruct the trajectory without exposing sensitive payloads by default;
- agent evaluation measures end-task success and trajectory behavior, not only final-answer fluency;
- multi-agent designs require a concrete decomposition benefit and explicit ownership/handoff contracts; do not introduce agents solely to mirror team/org boundaries;
- deterministic workflows remain preferred when the valid execution path is known in advance.

## Agent versus workflow decision

Before adding agentic control, classify the problem:

```text
known required sequence / fixed business state machine
-> deterministic workflow

dynamic information gathering or action selection where the useful path depends on observations
-> bounded agentic loop

mixed process
-> deterministic shell with bounded agentic step(s)
```

Examples of deterministic owners include authorization, approvals, billing, persistence transitions, deployment, deletion and compliance gates. An agent may recommend or prepare these actions without owning the final state transition.

## Tool contract

A production tool should declare enough to answer:

1. What capability does it expose and who owns it?
2. What typed input/output schema is accepted?
3. Is it read-only, reversible or side-effecting?
4. What identity/tenant/authorization context is required?
5. Is invocation idempotent? If not, what prevents duplicate effects?
6. What timeout/retry semantics apply?
7. What errors are safe to surface to the model versus mapped to bounded domain failures?
8. What audit/evidence is retained?

Prefer narrow semantic tools such as `get_employee_skills(employee_id)` or `submit_assessment_result(...)` over generic SQL, shell or unrestricted HTTP tools.

Tool descriptions are part of behavior identity when they materially influence selection/routing. Validate schemas at the deterministic boundary before execution and validate results before returning them to the model when external data is untrusted.

## State and memory

Keep these concepts separate:

- **context** — material supplied to the current model call;
- **execution/session state** — durable or ephemeral state needed to continue one workflow/trajectory;
- **long-term memory** — derived interaction knowledge reused across sessions;
- **authoritative domain state** — system-of-record data owned by application/business services.

Memory writes should have explicit eligibility, retention and deletion semantics. Sensitive or tenant-scoped memory must preserve the same access boundaries as the source data. Derived memory should carry provenance/recency when stale recollection can affect decisions.

## Authorization and policy

Use defense in depth:

```text
user/service identity
-> deterministic authorization
-> allowed tool surface
-> policy/approval checks
-> side-effecting service
```

Prompt rules such as "never access salaries" are not authorization controls. Least privilege must be real at the tool/service/cloud boundary.

For high-impact actions, distinguish:

- `can` — technical permission;
- `may` — current policy/business permission;
- `approved` — required human or system approval is present.

The agent must not infer an approval token from natural-language context.

## Bounded execution and recovery

Every agent loop should define material limits such as:

- maximum model/tool steps;
- wall-clock timeout;
- model/token/cost budget where relevant;
- maximum parallel tool calls;
- cancellation propagation;
- loop/no-progress detection;
- fallback/terminal behavior when required information or a dependency is unavailable.

Do not retry a side-effecting tool blindly after an ambiguous timeout. Recover from a stable operation/idempotency key or reconcile authoritative state before deciding whether to repeat the action.

## Agent evaluation

Evaluate both outcome and trajectory. Useful dimensions include:

- end-task success/correctness;
- evidence/grounding quality;
- tool-selection and argument correctness;
- policy/authorization compliance;
- unnecessary tool calls/steps;
- loop/no-progress rate;
- recovery from tool/model failure;
- latency, token usage and cost per successful task;
- human escalation/approval correctness where applicable.

Expected tool order should be asserted only when order itself is a product/system invariant. Otherwise evaluate allowed/forbidden actions, required evidence and terminal outcome so tests do not overfit one valid reasoning path.

Maintain adversarial cases for prompt/tool-result injection, cross-tenant access attempts, stale/malicious external content, ambiguous side-effect completion and attempts to bypass approval/policy gates when those risks are material.

## Multi-agent systems

Use multiple agents only when the decomposition creates a real boundary such as separate context/tool sets, independently evaluable responsibilities, security domains or parallelizable specialist work.

Each handoff should define:

- sender/receiver responsibility;
- state/evidence transferred;
- authorization context preserved;
- success/failure contract;
- termination/escalation behavior.

More agents increase token/cost/latency/failure/observability complexity. Prefer one agent with well-designed tools when specialization does not provide measurable value.

## Orchestration and E2E

Complete E2E should cross the public boundary and prove the meaningful trajectory, including deterministic boundaries around the agent. For mixed workflows, a useful shape is:

```text
request
-> deterministic validation/auth
-> bounded agent reasoning/tool use
-> deterministic result validation
-> approval/policy when required
-> controlled persistence/side effect
-> externally visible outcome
```

At integration, prove the cheapest automated environment that exercises the changed trajectory and material tool contracts. At release, close residual provider/identity/network/real-service fidelity gaps only when those dimensions materially affect the claim.

Do not make production credentials or high-impact real side effects part of ordinary agent E2E merely because the agent is designed to use them in production.

## AWS mapping when `aws-cloud` also applies

Common mappings may include Bedrock for model access, AgentCore or another established runtime for agent hosting, Gateway/MCP or project-native service adapters for tools, Step Functions for deterministic shells, Lambda/ECS for bounded tool services, IAM/identity/policy services for authorization and CloudWatch/OpenTelemetry for traces.

These are mappings, not requirements. Preserve an established LangGraph/Strands/custom runtime, Temporal workflow engine, container platform or service architecture when it already satisfies the invariants.
