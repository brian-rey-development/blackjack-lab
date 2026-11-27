# blackjack-lab design

Status: approved 2026-11-27. Scope of the first delivery is scaffolding only (tooling, structure, empty modules, docs); game and learning code come in later milestones.

## Intent

Jev is TypeSafe AI's System One decision model, which returns calibrated probabilities over typed answers instead of generating text. This project tests two claims about it in a setting where the right answer is known exactly. Blackjack fits because its decision space is tiny (about 200 states, two actions), dynamic programming gives the exact optimal action and the true win probability for every state, and published research (arXiv 2610.11692) found Jev weak as a standalone long-horizon controller but useful as a teacher for reinforcement learning. The first claim is that Jev's probabilities are calibrated, and the second is that Jev's judgment, used as a fading prior, lets a Q-learning agent reach optimal play in fewer episodes without biasing where it converges.

The project is also a learning instrument for its owner, who wants to understand MDPs, dynamic programming, Q-learning, exploration and calibration from first principles. The notebooks therefore read as a sequence of lessons, and every number they show comes from the package, never from logic written inside a notebook.

## Goals

- A pure, fully tested Blackjack core with rule variants, an exact DP solver, tabular Q-learning with an optional prior, and metrics (expected value, regret, Brier score, ECE).
- One `Decider` contract that the DP oracle, a random baseline, Jev, a local open model and a trained Q-learning policy all satisfy, so any of them can be compared on equal terms.
- Reproducible experiments, meaning Jev's answers are cached on disk and committed, so every result replays without an API key or network access.
- A small HTTP API and CLI that expose the same capabilities, and five marimo notebooks that tell the story.
- A senior-grade codebase, with strict typing, enforced layer boundaries, CI and concise architecture docs.

## Non-goals

No web UI, database, Docker image, authentication, documentation site, experiment tracker, or Gymnasium dependency. Card counting, splitting, doubling, insurance and finite-shoe effects are out of v1. Neural function approximation is out, because the state space is small enough for tables.

## Anti-goals

The project fails even if it runs when any of these hold. Logic lives in notebooks or in the API layer rather than the core. A result depends on a live Jev call that cannot be replayed. The guided agent converges to something other than the DP optimum, which would mean the prior biased learning instead of accelerating it. The structure grows layers or abstractions that no current feature uses.

## Constraints

Python 3.14, uv for everything, Makefile as the task runner, consistent with the sibling Scibiom project. ruff with every rule enabled, pyright strict, import-linter contracts, pytest with hypothesis. The owner's global standards apply, which means no `any`, functions of 20 lines or fewer, immutability by default, no comments except where the reason is non-obvious, and docstrings only on public contracts (the `Decider` protocol and the API). Jev is in early access and the owner has not confirmed a key, so nothing except the `prior` CLI command may require one. Development happens on Apple Silicon without CUDA.

## Approaches considered

For the game, Snake was rejected because it punishes long-horizon planning, which is Jev's documented weakness, and because code solves it perfectly. Wikiracing and an instruction-driven text dungeon were good fits for Jev but lack an exact answer key. Blackjack was chosen because DP provides ground truth for both actions and probabilities.

For combining Jev with RL, the paper describes three roles, namely reference policy, exploration judge and replay rater. Replay rating adds little in a tabular setting with short episodes, so v1 uses the first two, Jev's probabilities initialise the Q-table and steer exploration, and both influences decay to zero so Q-learning keeps its convergence guarantee.

For notebooks, marimo was chosen over Jupyter because marimo notebooks are plain Python files that ruff, pyright and git diffs handle cleanly, and reactive execution prevents stale state. The cost is less familiarity and no Colab support.

## Decided design

### Game and rules

The game follows Sutton and Barto example 5.1 with an infinite deck (cards drawn with replacement), which keeps the state Markov and the DP exact. The decision state is the player total (12 to 21), the dealer's up card (ace to ten) and whether the player holds a usable ace, giving 200 states. Totals below 12 always hit and are not decision states. Actions are hit and stand. Rewards are +1, 0 and -1, and a natural pays `natural_payout`.

Naturals are resolved at the deal, before any decision. A player natural pays `natural_payout` unless the dealer also has one, which is a push. The dealer does not peek, so a dealer two-card 21 against a player without a natural is just a dealer total of 21 reached at the end of the hand, and the dealer's hole card is never conditioned on. An episode starts from a real deal drawn from the variant's card weights, totals below 12 auto-hit, and a hand that ends at the deal produces no decision. The "win probability" for both Jev's `Noul` and the DP is P(player wins the hand), with draws counted as not winning, from that decision state under optimal play. These rules were settled during design review and follow Sutton and Barto except for the explicit natural payout.

A `Variant` is a frozen dataclass holding the card weights, whether the dealer hits soft 17, and the natural payout. Three presets ship in v1. `classic` is the Sutton and Barto game. `hits_soft_17` changes the dealer rule. `no_tens` removes ten-valued cards from the deck, which makes memorised basic strategy wrong and so separates reasoning from recall.

### Layers

```
app        settings.py, cli.py, api.py        composition root
adapters   jev.py, local_llm.py, store.py     I/O and third-party SDKs
core       game, dp, learn, deciders, metrics      pure Python + numpy
```

import-linter enforces app above adapters above core, and forbids core from importing `typesafe_sdk`, `fastapi`, `pydantic`, `mlx` and `mlx_lm`.

### Decider contract

`core/deciders/protocol.py` defines `Observation` (player total, dealer up card, usable ace), `Decision` (chosen action, a probability for each action summing to one, and an optional win probability) and the `Decider` protocol with a `name` and `decide(observation, variant) -> Decision`. Because the state space is finite, any decider can be materialised as a `PolicyTable` covering all 200 states, and the rest of the system (metrics, learning, the API) works on tables. Only `adapters/jev.py` and `adapters/local_llm.py` ever call a model, and only when building a table.

### Jev adapter

The SDK is `typesafe-sdk` on PyPI (0.7.6 at time of writing, Python 3.11 or newer), imported as `typesafe_sdk` and installed through the `jev` extra. It offers `TypeSafeClient` and `AsyncTypeSafeClient`, which read `TYPESAFE_API_KEY`, and `client.system_one(state=..., questions=...)` with question types `Choice(instructions, criteria)`, `Noul(instructions)` and `Score(instructions, criteria)`. Answers come back as `response.choices[key]` (with `.choice`, `.confidence`, `.probabilities`) and `response.nouls[key]`. The adapter receives its client by injection, so tests use a fake client and never touch the network.

Each state becomes one `system_one` call whose `state` holds the hand, the dealer card and the rules of the variant written in plain words. The call asks two questions in parallel, a `Choice` over hit and stand, and a `Noul` asking whether the player will win the hand with good play from here. The adapter uses the async client with bounded concurrency to build all 200 answers. The result is stored by `store.py` as `data/priors/{decider}--{variant}.json` with metadata recording the model id, SDK version, date and a hash of the question wording.

### Local model adapter

`adapters/local_llm.py` is the fallback teacher when no Jev key exists, installed through the `local` extra. It scores the hit and stand answers of a small Qwen3 model through `mlx-lm` by their next-token logits, averaging over both option orderings to cancel position bias, which is the training-free method from AnyJev. It produces the same prior file format.

### LLM adapter

`adapters/llm.py` lets a frontier LLM play as one more decider through Pydantic AI structured output, returning the action and a stated probability for each action and for winning. It contrasts slow reasoning with Jev's fast typed decisions, and verbalised confidence with RLCD-trained probabilities, on the same 200 states and metrics. The model is configurable through `LLM_MODEL`, it writes the same prior file format, and it ships in the optional `llm` extra.

### DP solver

`core/dp.py` computes the dealer's exact final-total distribution for each up card and variant, then the exact action values, optimal policy and win, draw and loss probabilities for every state. It also evaluates any `PolicyTable` exactly, which gives noise-free expected value for learning curves.

### Learning

`learn/q_learning.py` implements tabular Q-learning over the 200 states with step-size and exploration schedules from `learn/schedules.py`. `learn/prior.py` turns a prior table into two influences. The first is the initial Q-values, set to `beta0 * (pi(a|s) - 0.5)`. The second is exploration, where an exploring step samples from a mixture `w_t * pi + (1 - w_t) * uniform`. Both `beta` and `w_t` decay to zero on configurable schedules, and the uniform floor keeps every action explored, so convergence to the optimum is preserved. The controls are a shuffled prior (the prior's rows permuted across states, with a fresh permutation per seed) and an inverted prior.

### Metrics and experiments

At fixed checkpoints the greedy policy is evaluated exactly with the DP evaluator, weighting states by the real deal distribution (the same one episodes start from), so a learning curve is exact expected value per hand against episodes, reported as a mean with a 95% interval over seeds (default 20). The headline number is episodes until regret against the optimum stays under 0.005. Calibration is measured two ways. The action probabilities are scored against the DP label "hit is optimal" with Brier score and ten-bin ECE, and the win probability is compared with DP's true win probability through a reliability diagram and mean absolute error.

### Interfaces

The CLI (`uv run blackjack-lab ...`) has `solve`, `prior --decider jev|local --variant`, `train --prior none|jev|shuffled|inverted`, `evaluate` and `serve`. The API (FastAPI, `api` extra) serves `GET /health`, `GET /v1/deciders`, `POST /v1/decide` and `GET /v1/policy/{decider}`, and reads only tables from `data/` and `artifacts/`, so serving never calls a model. Settings come from the environment through pydantic-settings (`TYPESAFE_API_KEY`, `JEV_MODEL` defaulting to `jev-latest`, `DATA_DIR`, `ARTIFACTS_DIR`).

### Notebooks

`01_rules_and_optimal_play`, `02_teacher_zero_shot_and_calibration`, `03_q_learning_baseline`, `04_teacher_guided_learning` and `05_rule_variants`. Each opens with the question it answers and the theory behind it, and imports everything it computes.

### Packaging and tooling

A single package with src layout. Base dependencies are `numpy`, `pydantic` and `pydantic-settings`, where Pydantic validates everything crossing a boundary (prior files, settings, API payloads) and stays out of `core`. Every teacher is an optional extra, `jev` (typesafe-sdk), `local` (mlx-lm, macOS only) and `llm` (pydantic-ai), because the three are interchangeable adapters and nobody should install an SDK they cannot use. The other extras are `api` (fastapi, uvicorn) and `notebooks` (marimo, matplotlib). `requires-python` is `>=3.14` with no upper cap. LangChain was considered and rejected, because Jev generates no text and the `Decider` protocol already covers the only abstraction needed. Dev group holds ruff, pyright, pytest, hypothesis, import-linter and httpx. The Makefile exposes `setup`, `lint`, `format`, `typecheck`, `arch`, `test`, `check` and `notebooks`, and `serve` arrives with the API. GitHub Actions runs `make check` on Linux, where a platform marker skips `mlx-lm` because `mlx` ships wheels only for macOS. Notebooks are validated by `marimo check` and executed in-process by pytest. A dry resolve confirmed every dependency, `mlx-lm` included, has Python 3.14 wheels for Apple Silicon. `artifacts/` is gitignored, and `data/priors/` is committed.

### Documentation

`README.md` covers what, why, quickstart and a results table filled in later. `docs/architecture.md` explains the layers and data flow. `docs/decisions/` holds short ADRs for the decider contract and table materialisation, marimo, and the decaying prior. `CLAUDE.md` records conventions for coding agents.

## Left to the builder

Exact schedule shapes and default hyperparameters (step size, epsilon, decay rates, `beta0`), the precise question wording sent to Jev, concurrency limits, the Qwen3 model size, CLI output formatting, and internal module helpers, provided the layer rules hold.

## Milestones

M0 is this delivery, the scaffold with tooling, structure, empty modules, notebook stubs, docs and a green `make check`, including a test that discovers and imports every module, so broken imports fail fast as the package grows. M1 is the core game, DP and metrics. M2 is the deciders and prior building. M3 is learning and experiments. M4 is the API, CLI polish and finished notebooks. M5, optional, is the LLM decider.
