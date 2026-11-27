# Architecture

The codebase is three layers, and dependencies point only downward, because the part worth trusting (the game, the solver, the learning and the metrics) should be testable without a network, a model or a server.

```
app        settings, cli, api              wires everything together
  |
adapters   jev, local_llm, llm, store      models, files, third-party SDKs
  |
core       game, dp, learn,                stdlib + numpy only
           deciders, metrics
```

import-linter enforces three contracts on every `make check`. The layers run app, then adapters, then core. Core may not import `typesafe_sdk`, `pydantic`, `pydantic_ai`, `fastapi`, `uvicorn` or `mlx`. Adapters may not import HTTP serving libraries, so the API stays a thin shell in `app`.

## Data flow

```
Variant ──> DP solver ──> exact Q-values, optimal policy, win probabilities
   |                                   |
   |                              answer key
   v                                   v
teacher (Jev / Qwen / LLM) ──> PolicyTable ──> data/priors/*.json ──> metrics
                                    |
                                    v
                        Q-learning with fading prior ──> artifacts/ ──> notebooks, API
```

A teacher is asked about each of the 200 decision states once, and the answers are stored as a `PolicyTable` on disk. Everything downstream reads tables, so experiments replay offline, cost nothing to rerun, and never depend on a model being reachable.

## Where things live

| Concern | Module |
|---|---|
| Cards, hand values, rule variants | `core/game` |
| Episodes, rewards, dealer play | `core/game/env.py` |
| Exact solution and policy evaluation | `core/dp.py` |
| `Decider` contract, `PolicyTable`, baselines | `core/deciders` |
| Q-learning, schedules, prior mixing | `core/learn` |
| Brier, ECE, reliability, regret | `core/metrics.py` |
| Model calls and the prior cache | `adapters` |
| Settings, CLI, HTTP API | `app` |

Decisions behind this shape are recorded in `docs/decisions/`.
