# 0003 The teacher's influence decays to zero

Status: accepted, 2026-11-27.

## Context

A teacher such as Jev can speed up Q-learning, but published results (arXiv 2610.11692) show it is not a reliable standalone controller, so a learner that trusts it permanently would inherit its mistakes. The project's anti-goal is a guided agent that converges to anything other than the DP optimum.

## Decision

The teacher influences learning in two ways, both of which fade. Its probabilities set the initial Q-values with weight `beta`, and exploring steps sample from a mixture of the teacher and a uniform distribution with weight `w_t`. Both weights decay to zero, and the uniform part guarantees every action keeps being explored.

## Consequences

Q-learning keeps its convergence guarantee, so a good teacher can only change how fast the agent learns, not where it ends up. Shuffled and inverted priors act as controls that measure what a misleading teacher costs. The decay schedules become hyperparameters that the experiments must report.
