---
name: orchestrate-edge-case-testing
description: Test a HackerRank Orchestrate agent against its failures and inconsistencies, not just its successes — deliberately inspecting where similar cases get different treatment. Use before submission when the only testing done so far was "run it and see if the output.csv looks reasonable," when comparing how the agent handled two superficially similar tickets/claims, or when preparing concrete edge-case examples to discuss in the AI judge interview.
---

# Orchestrate: Edge Case Testing

**Direct evidence**: HackerRank's guidance names this precisely — *"Incomplete testing: Don't only inspect successful cases; examine failures and edge cases"* and *"Inconsistent handling: Similar cases receiving different treatment without justification."* The interview prep guidance separately says to *"discuss edge cases explicitly: missing data, conflicting signals, distracting input instructions"* — meaning this isn't just a code-quality concern, it's rehearsed material for the 30%-weighted interview too.

## Two distinct testing disciplines this asks for

**1. Inspect failures, not just successes.** After a full run, don't just check "did most rows look plausible" — actively pull the rows where the agent escalated, marked uncertain, or hit a fallback path, and read them individually. These are disproportionately where bugs and bad judgment calls hide, and disproportionately where the golden dataset likely has deliberately hard cases (both challenge descriptions confirm curated edge cases and adversarial inputs are part of the test set).

**2. Consistency-check similar cases.** Take two tickets/claims that are similar in substance but phrased differently, or that hit the same underlying issue from different angles. Run both through the agent. If they get materially different treatment (one escalates, one doesn't; one cites evidence, one doesn't) with no substantive reason, that's a calibration bug — the kind an interviewer will find by asking "what about a case like X but slightly different?"

## A concrete practice: build a consistency test set

Before submission, hand-pick 5-10 pairs of similar-but-not-identical cases from your own understanding of the domain (not from the golden dataset, which you don't have access to). Run the agent on each pair. For every pair that diverges, either:
- Confirm the divergence is justified (the cases actually differ in a way that matters) and note *why* — this becomes interview material
- Or treat it as a bug and fix the underlying logic

## Why the June (multi-modal) challenge makes this even more explicit

The multi-modal-review challenge's evaluation criteria *require* — not suggest — comparing at least two strategies/prompts/configurations and documenting the final choice with reasoning. That requirement is this same discipline formalized as a graded deliverable: you cannot pass that bar by testing only the happy path once.

## Anti-pattern this prevents

Treating a single successful end-to-end run as "done." A run that produces a plausible-looking `output.csv` with zero individual row inspection, and zero adversarial or paired-comparison testing, is the single most common gap between "it ran" and "it's actually calibrated" — and the interview is specifically designed to surface that gap by asking about cases you may not have considered.
