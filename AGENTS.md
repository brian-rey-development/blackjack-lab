# AGENTS.md

Intent lives in `docs/design.md`, build order in `docs/plan.md`, layers in `docs/architecture.md`, and past decisions in `docs/decisions/`. Read the batch you are on before writing code.

## Workflow

- One batch per session. Stop at the end of each batch and summarise what was built, how it was verified and every call you made, so the owner can review.
- Test first and watch it fail, then make it pass. A new check or guard must be shown failing on a planted error before it counts.
- Commit only when asked, with conventional commits in English.

## Commands

```bash
make setup   # uv sync --all-extras --locked
make check   # ruff, format, marimo check, pyright strict, import-linter, pytest with 100% branch coverage on core
make format  # fix and format in place
```

Use `uv run` and `uv add`, never pip. A new dependency needs a reason, and teachers (`jev`, `local`, `llm`) stay optional extras.

## Architecture

- `app` imports `adapters` imports `core`, never the reverse.
- `core` uses only the standard library and numpy. Networks, models, files and HTTP live in `adapters` or `app`.
- Every player is a `Decider` materialised as a `PolicyTable`, and nothing downstream calls a model.
- A broken import-linter contract is a design problem to fix, never a rule to relax.

## Code

- Strict typing, no `Any`, no `cast` or `type: ignore` without a reason on the same line.
- Frozen dataclasses in `core`, Pydantic only at boundaries.
- Functions of 20 lines or fewer, early returns, named constants instead of magic values.
- Every random draw takes an explicit `numpy.random.Generator`.
- Absolute imports only. No modules named `utils`, `helpers`, `common`, `misc`, `shared` or `types`, and no names that shadow the standard library.
- No comments unless the reason is non-obvious, docstrings only on public contracts.
- No em dashes anywhere.

## Tests and notebooks

- Tests never touch the network, use hypothesis for game rules, and assert behaviour rather than mocks.
- Notebooks import from the package and hold no logic of their own.
