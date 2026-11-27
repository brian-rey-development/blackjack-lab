# 0002 Notebooks are marimo files

Status: accepted, 2026-11-27.

## Context

The notebooks are the project's lessons, so they must stay correct as the package changes. Jupyter stores notebooks as JSON with outputs embedded, which makes diffs noisy, keeps them out of ruff and pyright, and allows hidden state when cells run out of order.

## Decision

Notebooks are marimo files, which are plain Python. They are linted by ruff, type-checked by pyright with relaxed rules for cell signatures, and executed headless as a smoke check. They import everything they compute from the package.

## Consequences

Notebooks show up in reviews as readable diffs, and a breaking change in the package fails `make check` instead of a lesson. The cost is a tool that is less familiar than Jupyter and has no Colab support.
