# 0001 Every decider is materialised as a table

Status: accepted, 2026-11-27.

## Context

The project compares very different players, from an exact DP oracle to Jev, a local Qwen model and a frontier LLM. Calling models inside training loops or API handlers would make experiments slow, costly and impossible to replay, and each comparison would need its own glue code.

## Decision

Every player satisfies one `Decider` protocol, `decide(observation, variant) -> Decision`, where a decision always carries a probability for each action. Because Blackjack has only 200 decision states, every decider is materialised once into a `PolicyTable`, and teachers' tables are saved to `data/priors/` with metadata. Metrics, learning and the API consume tables only.

## Consequences

Experiments replay offline and cost nothing to rerun, and adding a new player means writing one adapter. The approach depends on the state space being small and finite, so a future game with a large state space would need live calls and a different design.
