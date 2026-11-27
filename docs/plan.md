# blackjack-lab build plan

> For agentic workers: use superpowers:subagent-driven-development or superpowers:executing-plans, one batch at a time, TDD inside each batch.

**Goal** is a Blackjack lab where an exact DP solver grades Jev's calibration and measures whether Jev, as a fading prior, speeds up Q-learning. **Spec** lives in `docs/design.md`, and executors read both files.

Each batch ends green on `make check`, teaches one idea, and the notebook for that idea is written in the same batch, so understanding grows with the code. Commits happen per batch when the owner asks.

## Global constraints

- Python 3.14, uv, Makefile, ruff `ALL`, pyright strict, import-linter (app > adapters > core), pytest + hypothesis.
- Core imports only stdlib and numpy. No `any`, functions of 20 lines or fewer, frozen dataclasses, no comments unless the reason is non-obvious.
- Tests never touch the network. Every random draw takes an explicit `numpy.random.Generator`.
- No Jev key is confirmed, so both teachers are built in batch 6 and whichever is available generates the committed prior. Jev replaces Qwen later by rerunning one command.

## Review focus

- A soft hand that busts its ace (A,6 then 10) must become hard 17, not bust.
- The `no_tens` deck must never deal a ten, in the env and in the DP alike.
- A prior that puts probability 0 on an action must still let Q-learning explore it, through the uniform floor.
- `POST /v1/decide` with a total outside 12 to 21 or an unknown decider returns 422 or 404, never 500.
- A prior file whose question hash or variant differs from the request is rejected on load, not silently reused.

---

### Batch 0 · Scaffold

Done. **Learn** how a layered Python project is wired and checked. **Built** `pyproject.toml` (base deps, extras `jev`/`local`/`llm`/`api`/`notebooks`, tool config, three import-linter contracts), `Makefile`, CI, `CLAUDE.md`, README, `docs/architecture.md`, three ADRs, empty `core` (`game`, `learn`, `deciders`), `adapters` and `app` packages, and five marimo notebook stubs. `tests/test_imports.py` discovers and imports every module, and `tests/test_notebooks.py` runs every notebook headless. Both were shown to fail on a planted error.

### Batch 1 · Cards and rules

**Learn** what a state is, and why an infinite deck keeps the game Markov. **Build** `core/game/cards.py` with `hand_value(cards: Sequence[int]) -> HandValue(total, usable_ace)`, `core/game/rules.py` with frozen `Variant(name, card_weights: tuple[float, ...], dealer_hits_soft_17, natural_payout)` and `VARIANTS` holding `classic`, `hits_soft_17`, `no_tens`, and `core/game/state.py` with `Action` (StrEnum `hit`/`stand`) and `Observation(player_total, dealer_card, usable_ace)`. **Done when** hypothesis shows totals are never above 21 while an ace is usable, weights sum to 1, and `no_tens` has zero weight on 10.

### Batch 2 · Environment

**Learn** how an episode, actions and rewards form an MDP. **Build** `core/game/env.py` with `BlackjackEnv(variant, rng)`, `reset() -> Step`, and `step(action) -> Step(observation | None, reward, done)`, covering naturals at the deal, auto-hit below 12, and dealer play with soft-17 handling. **Done when** the dealer always stops at 17 or more, `hits_soft_17` hits soft 17, naturals end with no decision and pay `natural_payout`, and the same seed replays the same hand.

### Batch 3 · Exact DP solver and notebook 01

**Learn** Bellman equations, and why DP is the answer key. **Build** `core/dp.py` with `solve(variant) -> Solution(q, policy, win_prob, value)`, where arrays are indexed `[total-12, dealer-1, usable_ace, action]`, plus `deal_distribution(variant)` and `evaluate(policy: PolicyTable, variant) -> float`. **Done when** the classic policy matches Sutton and Barto figure 5.2, every probability vector sums to 1, and 200k simulated hands under the optimal policy land within 3 standard errors of `solve().value`, which cross-checks the env against the DP. Notebook 01 shows the strategy grid and dealer bust odds.

### Batch 4 · Deciders and policy tables

**Learn** why a contract plus a finite state space lets every player become a table. **Build** `core/deciders/protocol.py` with `Decision(action, probabilities, win_probability)` and `Decider` (`name`, `decide(observation, variant) -> Decision`), `core/deciders/table.py` with `PolicyTable(probs, win_prob)` and `materialise(decider, variant) -> PolicyTable`, and `oracle.py` and `uniform.py`. **Done when** one contract test, parametrised over every decider, checks that probabilities sum to 1 and both actions are present, and the oracle table evaluates to exactly `solve().value`.

### Batch 5 · Metrics

**Learn** what calibration means, through Brier score, ECE and reliability diagrams. **Build** `core/metrics.py` with `brier(p, y)`, `ece(p, y, bins=10)`, `reliability(p, y, bins=10)` and `regret(table, variant)`. **Done when** a perfect predictor scores 0 on Brier and ECE, a constant 0.5 on balanced labels scores Brier 0.25, and the oracle's regret is 0.

### Batch 6 · Teachers, prior cache and notebook 02

**Learn** how to question a decision model, why position bias exists, and why caching makes results reproducible. **Build** `adapters/store.py` with `save_prior` and `load_prior -> (PolicyTable, PriorMeta)`, which parses the file into a Pydantic model and validates the variant and question hash. Build `adapters/jev.py`, an injected async client making one `system_one` call per state (a `Choice` for the action and a `Noul` for the win) with bounded concurrency, and `adapters/local_llm.py`, which scores Qwen3 logits through mlx-lm averaged over both option orders. Then add `app/settings.py`, the `prior` CLI command and its `[project.scripts]` entry point. The Jev adapter needs the `jev` extra. **Done when** the Jev adapter passes against a fake client, a store round trip is lossless, and a mismatched hash is rejected. Run `prior` with whichever teacher is available to commit `data/priors/*--classic.json`. Notebook 02 scores that teacher's zero-shot play and calibration against DP.

### Batch 7 · Q-learning baseline and notebook 03

**Learn** temporal-difference learning, exploration, and why learning in Blackjack is so noisy. **Build** `core/learn/schedules.py` (step-size and epsilon decay) and `core/learn/q_learning.py` with `train(variant, config: TrainConfig, prior: PolicyTable | None, rng) -> TrainResult(q, curve)`, where the curve records exact EV at checkpoints, and add the `train --prior none` CLI command. **Done when** a fixed seed reaches regret below 0.005 on classic within the configured budget. Notebook 03 plots the learning curve with its 95% band over 20 seeds.

### Batch 8 · Jev-guided learning, controls, notebooks 04 and 05

**Learn** priors, reward shaping in disguise, and why a decaying influence keeps convergence. **Build** `core/learn/prior.py` with `initial_q(prior, beta0)`, `explore_dist(prior, w) -> mixture with uniform`, `shuffled(prior, rng)` and `inverted(prior)`, wire `train --prior jev|shuffled|inverted`, and add an experiment runner that saves results to `artifacts/`. **Done when** the oracle used as a prior reaches the threshold in fewer episodes than no prior, which proves the mechanism works, and the inverted prior still converges to the optimum, which guards the anti-goal. Notebook 04 compares the curves and episodes to threshold, and notebook 05 repeats the comparison on `no_tens` to separate recall from reasoning.

### Batch 9 · Serving and finish

**Learn** how a thin API sits on a pure core. **Build** `app/api.py` with `GET /health`, `GET /v1/deciders`, `POST /v1/decide` and `GET /v1/policy/{decider}`, all reading only tables, then polish the CLI with `solve`, `evaluate` and `serve`, add `make serve`, fill the README results table, and finish the ADRs and `docs/architecture.md`. **Done when** httpx tests cover every route plus the 422 and 404 cases, and `make check` and `make serve` both work from a clean `make setup`.

### Batch 10 · LLM decider (optional)

**Learn** the difference between System 1 and System 2 decisions, and why verbalised confidence is usually overconfident. **Build** `adapters/llm.py`, a Pydantic AI agent whose structured output model is `LlmDecision(action, p_hit, p_win)` with probabilities constrained to [0, 1], wired into `prior --decider llm` through `LLM_MODEL`. Add an `llm` column to notebook 02 and the README. **Done when** the adapter passes against Pydantic AI's `TestModel` with no network, and its prior file loads through the same `store.py` path as the other teachers.
