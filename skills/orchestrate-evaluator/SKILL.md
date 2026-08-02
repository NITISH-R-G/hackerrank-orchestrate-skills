---
name: orchestrate-evaluator
description: Score a whole Orchestrate repository across specification, evidence, generalization, determinism, security, and release readiness — and decide whether it is moving toward the top of the leaderboard. Use at each phase gate and before submission.
---

# Orchestrate: Orchestrate Evaluator

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## What this answers

> **If I ship this today, what evidence says I am actually better?**

Not "does the code look good."

## The categories, and what a top submission looks like

| Category | Check | Strong signal |
|---|---|---|
| **Specification** | literal conformance to every clause | 0 violations, checked against transcribed constants |
| **Evidence** | cited ids exist, belong, don't self-reference | 0 hallucinated |
| **Generalization** | coupling probes, hardcoded ids | 0 ids in executable code; coupling probes pass |
| **Determinism** | processes × hash seeds | one hash, boundary stated |
| **Security** | injection, ReDoS, traversal, malformed media | every hostile input yields a valid row |
| **Multimodal** | counterfactual per modality | disabling the modality changes decisions |
| **Release** | fresh clone, artifact freshness, packaging | clone runs from README alone |
| **Evaluation** | output distribution sanity | no near-constant predictor |

## Scoring rules that matter

**Blockers cap everything.** A score that lets fourteen passes outvote one release
blocker is worse than no score. Any blocker → `DO NOT SHIP`, regardless of the average.

**Label your confidence.** `measured` (a number was produced) / `observed` (read from
a file) / `inferred` (reasoning) / `unknown`. Discount inferred findings. **Report
unknown; never guess it either way.**

**Evidence before score.** Print blockers *above* the number. If a reader takes the
score and ignores the findings, the report failed.

## Distribution sanity — the cheap tell for a degenerate solution

- one action covering **>80%** of rows → a near-constant predictor can score well on an
  imbalanced set while learning nothing
- **≤2** distinct `message_type` values → the type column is not being reasoned about
- **1** distinct `reason` string → a scored dimension is being wasted

## Run a negative control before trusting a green result

A framework that only ever says READY is decoration. Inject known defects into a copy
and confirm it goes red.

*Real example:* five injected defect classes — illegal action, illegal type, wrong
separator, hallucinated id, out-of-range confidence — all five caught, plus the artifact
staleness they induced. **Run this before you trust your own tooling**, including this
skill's checklist.

## Am I moving toward Rank 1?

Ask these, in order:

1. Are there **zero blockers**? If not, nothing else matters yet.
2. Can I state a **measured** number for each scored dimension?
3. Can I name **three things I rejected**, with the number that killed each?
4. Does my multimodal claim survive the **counterfactual**?
5. Do my **coupling probes** pass?
6. Can I state the **boundary** of every guarantee?
7. Do I know **every constant** in my code and its provenance?

Seven yeses is a strong submission. Fewer than five, and the gap is evidence, not code.
