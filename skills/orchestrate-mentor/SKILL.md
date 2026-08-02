---
name: orchestrate-mentor
description: Evaluate a change BEFORE you make it: expected gain, risk, blast radius, what to measure, and whether it was already tried and rejected. Use whenever you are about to optimise something in the final hours.
---

# Orchestrate: Orchestrate Mentor

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## What this is for

Every other audit tells you what you *did*. This one runs **before** the change, when
the decision is still cheap.

## The five questions, in order

**1. What is the ceiling?**
Is a gain even possible? Measure the maximum achievable improvement before building
anything.

*Real example:* before building a vision model, three checks — labeled image rows were
already **5/5** (headroom: zero); **13 of 15** graded image rows were decided by rules
that never read media; and an exhaustively-tuned pixel classifier reached 19/20 while
**failing on the one image it existed to serve**. Three independent proofs of "no", in
an afternoon.

**2. Has this been tried?**
Check your rejection log. Re-proposing a measured failure is a regression, not an idea.

**3. What is the blast radius?**
Not "does it help" but "how many outputs change".

*Real example:* a ranker swap gained **+1 row** on one metric while changing **23 of
110 output cells** — 21% of the submission, for a gain whose confidence interval spanned
±0.17. Rejected. A later ranker change *was* accepted because it had a **diagnosed
mechanism**, not just an aggregate wiggle.

**4. What will I measure, and what would falsify it?**
Name the metric *before* writing the change. Otherwise you will run five and report the
one that moved.

**5. What does it cost?**
Every change has a cost column. Runtime, memory, a new dependency, a lost guarantee.

*Real example:* enabling a local OCR engine changed **0 of 110 rows** while taking
runtime from 0.25s to ~45s and heap from 7 MB to 500 MB. That was still the right call —
the spec requires reading images — but it is a *trade*, and the README says so.

## The decision rule

Ship only if **all** hold:

- a named metric improves, measured
- no other measured metric regresses beyond noise
- the blast radius is proportionate to the gain
- every existing test passes
- it does not remove a stated guarantee

Otherwise revert. In a real build, **9 of the proposed optimisations failed this test**
and were rejected with the number that killed each one.

## Late-stage triage

With hours left, rank by *risk-adjusted* value:

| | ship it | think hard | do not |
|---|---|---|---|
| **Blocker** (spec violation, stale artifact, crash) | ✅ always | | |
| **Measured gain, small blast radius** | ✅ | | |
| **Measured gain, large blast radius** | | ⚠️ only with a diagnosed mechanism | |
| **Unmeasured "improvement"** | | | ❌ |
| **Refactor for elegance** | | | ❌ |

## The output to write down

```
CHANGE:      one line
CEILING:     max possible gain, measured
PRIOR ART:   tried before? outcome?
GAIN:        metric, before -> after
COST:        what regresses
BLAST:       N of M outputs change
VERDICT:     SHIP / REJECT + the number
```
