---
name: orchestrate-dataset-coupling-auditor
description: Find every place a solution accidentally depends on an incidental property of the sample data — id format, timestamp format, row order, filenames, exact wording. Use before submission, because the graded set differs from your sample in every way the spec does not explicitly fix.
---

# Orchestrate: Dataset Coupling Auditor

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Assume the hidden data differs from your sample in every way the specification does
not explicitly fix. Then go looking.**

## The taxonomy — and the test for each

| Coupling | Test |
|---|---|
| ID **format** | rename every id to a different scheme; do decisions survive? |
| Timestamp format | rewrite dates day-first; does ordering survive? |
| Row order | shuffle every context file; does output survive? |
| Directory layout | rename the media folder; does resolution survive? |
| Filename ↔ content | verify by magic bytes, never extension |
| Exact wording | which lexicon terms fire on exactly **one** sample row? |

## What this caught in a real build — three real couplings, all found late

**1. ID shape.** Mention detection harvested tokens matching a regex for the sample's
id convention (`@u_<digits>`), then compared them to the recipient. The comparison was
principled; the *harvest pattern* was not. Renaming ids broke **4 of 110 decisions** —
two rules went silently dead. Fixed by searching for `@` + *the actual recipient id*,
assuming no format at all.

**2. Timestamp format.** History was sorted with a raw **string** sort — chronological
only for zero-padded, most-significant-first dates. The spec fixes no format. Day-first
dates produced different output.

**3. Copied wording.** A lexicon contained `price is` — a copula fragment transcribed
from one sentence, firing on **1 of 537** texts. Replaced with the underlying category,
which is broader *and* correctly rejects a colliding domain the copied version wrongly
matched.

## The tell for an overfitted lexicon

Count how many corpus rows each term matches:

- fires on **exactly one row** → suspect. Copied, or a real category that is rare?
- fires on **zero rows** → usually fine. Generalisation cover cannot overfit data it
  never touches.

In the real build: 25 single-row terms, of which **one** was a genuine copy.

## The checklist

- [ ] Automated probe that perturbs each coupling and asserts output is unchanged
- [ ] Every hardcoded identifier in *executable* code removed (comments are fine)
- [ ] Every format assumption replaced with detection or with the actual value
- [ ] Single-row lexicon terms reviewed one by one
- [ ] The probe committed as a standing test, not run once

## Failure modes

- **Encoding the SHAPE of an identifier you were handed.** Use the value, not a pattern.
- **Sorting formatted strings.** Works until the format changes.
- **Confusing "rare" with "copied".** Judge each term; do not delete on count alone.
