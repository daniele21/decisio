# Snake

Snake turns Decisio into a repeated action selector rather than a one-shot classifier.

At every game step:

```text
board + snake body + food + current direction
                      |
                      v
             candidate moves
            UP / RIGHT / DOWN / LEFT
                      |
                      v
                   Decisio
                      |
                      v
               one next move
                      |
                      v
                 game.step()
                      |
                   repeat
```

Before Decisio is called, the game deterministically removes reverse moves and moves that would
immediately hit a wall or body segment. Decisio chooses only among the remaining safe alternatives.
If exactly one safe move remains, the controller takes it without running the model.

Snake is an **example and behavioral probe**, not evidence that Decisio is a good game-playing agent.

## Live decision-loop UI

The branded local UI makes the complete decision loop visible:

```text
OBSERVE                     DECIDE                         ACT
board/state       ->        candidate preferences    ->   selected move
safe + filtered moves       model + scorer                updated board
                             live elapsed time
                             decision latency
                             generated tokens
                             cache/reuse evidence
```

The browser is only a local example surface. The GGUF model stays in the Python process and no HTTP
server is added to the Decisio core package.

Install the llama.cpp runtime, then launch:

```bash
uv sync --extra llama --extra dev

uv run python -m examples.snake.web \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --scorer direct \
  --threads 5 \
  --threads-batch 11 \
  --trace .artifacts/snake-live.jsonl \
  --open
```

The UI opens at `http://127.0.0.1:8765/` by default.

Snake defaults to `--scorer direct`. The safe moves are rendered once as A/B/C/... options, the
model is evaluated once, and Decisio reads the corresponding option-token logits from that single
forward pass. It does **not** run one YES/NO evaluation per candidate. Semantic v2 remains available
with `--scorer semantic` for explicit comparison.

Controls:

- **Start / Pause** — continuously ask Decisio for the next move;
- **1 move** — execute one complete observe → decide → act cycle;
- **Reset** — restart the deterministic episode;
- **Pause before move** — UI-only hold after the readout; it does not change inference or choice.

The default visual hierarchy is intentionally narrow: the board and selected move are primary;
candidate preferences and deterministic filters are contextual; model/runtime details, request JSON
and response JSON are diagnostics.

The UI labels candidate values as **relative preference**, not probability of correctness. Filtered
wall/body/reversal actions remain visible so the deterministic/application boundary is explicit.

Design source of truth for this example is code-first:
`examples/snake/static/index.html`, `style.css`, `app.js`, with the existing Decisio brand
tokens/assets as the visual owner.

## Reference artifact

The Decisio v1 evidence reference is CPU-only Qwen3.5-2B Q4_K_M GGUF through llama.cpp. The exact
artifact/runtime identity belongs to the scorer gate, not to this example. Snake can also be pointed
at another compatible GGUF, including a smaller Qwen3.5-0.8B for a faster local demo; that does not
make its results equivalent to the pinned 2B evidence.

For a headless rollout:

```bash
uv run python -m examples.snake.play \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --scorer direct \
  --threads 5 \
  --threads-batch 11 \
  --max-steps 100 \
  --render
```

Thread values are local execution tuning, not the frozen CPU scorer-gate identity.

## Why the controller filters first

A prior smoke exposed an immediate-wall failure. That is not a judgment an LLM should own. Geometry
is deterministic, so the game removes impossible/deadly immediate actions before scoring.

This is the intended Decisio integration pattern:

> **Hard constraints define the valid action space; Decisio ranks the remaining semantic alternatives.**

## What Snake exercises

Snake stresses properties that a static classification fixture does not:

- sequential decisions where an early mistake changes all future states;
- dynamic candidate sets;
- spatial reasoning over structured state;
- repeated inference latency;
- deterministic constraints before probabilistic scoring;
- error accumulation;
- reproducible episodes through a fixed random seed.

## State, bounded memory and deterministic sensors

Snake sends the **current state**, not the full episode history. The state includes board, complete
current body, direction, food, score and a tiny derived memory summary. A 12-head-position window is
kept only inside the game and resets when food is eaten.

Each safe candidate is enriched before scoring with deterministic sensors:

- next position and whether it eats food;
- Manhattan distance before/after and `closer/same/farther`;
- safe next moves and reachable free cells after the move;
- recent visits to the candidate cell and `low/medium/high` loop risk.

This keeps geometry/rule facts in code while leaving the trade-off to Decisio. Full history is not
sent to the model.

Sensors are included in the candidate descriptions sent to the scorer, alongside the coordinate
state and ASCII board. Manhattan distance ignores obstacles; reachable-cell counts treat the
projected body as static. These are local signals, not a path planner or a guarantee of reaching
food. Improved gameplay must be checked with fixed-state comparisons and episode traces.

## Readable model I/O

The live UI keeps every move in the decision log. Selecting a move shows a structured **Model input**
(question, current state, body path and A/B/C option text with sensors) next to the **Model readout**
(selected option, raw logit, relative preference, latency and generated-token count). The common
path does not expose raw JSON.

## Compare scoring strategies

Run the same deterministic episode with the same model and seed:

```bash
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer direct --max-steps 50
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer semantic --max-steps 50
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer semantic-independent --max-steps 50
```

Full rollouts can diverge after the first differing action, so Snake remains a behavioral probe rather
than the scorer promotion benchmark.

## Record every decision

Both the headless and live UI paths can write the same trace shape.

```bash
uv run python -m examples.snake.play \
  --model /path/model.gguf \
  --seed 42 \
  --max-steps 50 \
  --trace .artifacts/snake-direct.jsonl
```

Each JSONL row stores the exact state, candidates, Decisio distribution, model provenance, runtime
evidence and game outcome.

## Visual reference

The information hierarchy takes
[Rizzo Flow Snake](https://github.com/Rizzo-AI-Academy/rizzo-flow/blob/main/src/rizzo_flow/snake.html)
as a useful reference without copying its implementation.

Decisio-specific choices are deliberate:

- the decision cycle is explicitly shown as **OBSERVE → DECIDE → ACT**;
- deterministic invalid actions are filtered before model scoring and stay visible as filtered;
- the selected move is the primary visual event;
- candidate relative preferences remain close to the board and readable as bars;
- model, scorer and per-decision latency are always visible;
- zero generated answer tokens and cache/reuse evidence are visible;
- raw request/response JSON is progressively disclosed instead of dominating the common path;
- reduced-motion settings disable non-essential animation.

## CI video artifact

The real-model smoke can still render a trace-backed MP4. The video is generated from the actual
states and decisions used by the test; it is not a scripted animation.

To render a recorded trace locally:

```bash
uv sync --extra video
# ffmpeg must also be available on PATH

uv run python -m examples.snake.video \
  --trace .artifacts/snake-direct.jsonl \
  --output .artifacts/snake-direct.mp4 \
  --frames-dir .artifacts/snake-direct-frames
```

## Opt-in inference experiments

Both the web and headless commands accept these independently selectable experiments:

- `--input-format compact`: omit the duplicate ASCII board from model input (the game still renders
  it) and encode candidate sensors in short fields. Full body coordinates remain available.
- `--reuse-prefix`: direct/letters scoring only; place the question before changing state, mark its
  exact token prefix, and use the existing bounded sequence-state cache. This has a distinct
  `letter_question_prefix_v1` scorer identity. It changes prompt order, so compare quality as well
  as latency. Fresh backends evaluate the same prompt without reuse.
- `--controller adjacent-food`: bypass the model when a safe action eats food and leaves at least one
  immediately safe next action. This is an application heuristic, not proof of long-term safety;
  traces identify it as `deterministic_adjacent_food_policy`. The default remains `model`.

Default input remains verbose and prefix reuse remains off pending broader gameplay evidence.
Reuse checkpoints must align with native batch boundaries. A short fixed prefix may not be reusable
at `--n-batch 512`; smaller batches can enable reuse but also slow fresh processing. Do not assume
that cache hits imply a net speedup. CPU thread/batch tuning remains explicit via `--threads`,
`--threads-batch`, `--n-batch` and `--n-ubatch`.

Run a local diagnostic comparison (six easy food positions, both option orders, fresh/cache oracle):

```bash
uv run python -m examples.snake.benchmark_inputs \
  --model /path/model.gguf --output .artifacts/snake-inputs-b128.jsonl \
  --batch 128 --threads 5 --threads-batch 11 --rounds 2
```

Repeat in separate processes with `--batch 512` and with fewer batch threads. Rows retain exact
requests, prompt hashes, model/runtime identity, scores, latency, physical/logical tokens, cache
metrics and process peak RSS (platform units). Warmup is excluded; cache cold/warm rows are marked by
runtime metrics. Pair `prefix_shared` with `prefix_fresh` at the same round/state/order, and report
all changed argmaxes across formats, prompt order and runtime configurations. This tiny diagnostic
is neither representative episode quality nor a replacement for the frozen scorer gates.

Initial local results and the decision to retain defaults are recorded in
[Snake input efficiency diagnostic](../../benchmarks/snake-input-efficiency.md).
