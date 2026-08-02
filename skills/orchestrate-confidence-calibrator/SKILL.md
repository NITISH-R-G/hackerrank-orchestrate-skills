---
name: orchestrate-confidence-calibrator
description: Set and defend the confidence column. Use when choosing confidence values, and before any recalibration. The counter-intuitive rule: calibrate to the labeling policy, not to correctness.
---

# Orchestrate: Confidence Calibrator

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Match the target, not your intuition about the target.**

Confidence is an explicitly scored dimension. It is graded against *the labels*, not
against an abstract notion of good calibration.

## What this caught in a real build

**Dynamic confidence lost to a constant.** "More matched signals should mean higher
confidence" is obviously right. Measured: **MAE 0.0287 dynamic vs 0.0263 static** —
worse overall and worse on *every* action subset. It also emitted values outside the
observed band on 3/30 rows, masked only by a clamp. Deleted, not disabled.

**The ECE trap.** The system showed Expected Calibration Error of **0.138** —
systematically under-confident. The textbook fix is obvious. Before applying it, one
question: *what is the ground truth's own ECE?*

Answer: **0.1597 — worse.** The labels are deliberately under-confident. Every
ECE-improving shift made error against the actual target **strictly worse**
(0.0263 → 0.1467).

Optimising a textbook metric would have moved the system *away* from the thing being
scored.

## How to set values

1. Read the confidence column of the labeled samples. Note the **observed band**.
2. Clamp your output to that band. A value outside it is provably unlike any label.
3. Assign a value per decision class, then measure MAE against the labeled rows.
4. Only adopt a dynamic scheme if it **beats** the constant. Measure; do not assume.

## The checklist

- [ ] Observed confidence band extracted from the labeled data
- [ ] Output clamped to that band
- [ ] MAE measured against ground-truth confidence values
- [ ] Any dynamic scheme benchmarked against a static baseline before adoption
- [ ] Ground truth's **own** ECE computed before "fixing" your calibration
- [ ] Rejected schemes recorded with the number that killed them

## Failure modes

- **Optimising ECE blindly.** Check what the labels do first.
- **Disabling instead of deleting.** Disabled code is a future accident.
- **A clamp hiding a bug.** If a clamp is load-bearing, the thing it clamps is wrong.
