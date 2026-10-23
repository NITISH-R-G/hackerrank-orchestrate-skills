---
name: orchestrate-test-fix
description: Orchestrate phases 3 and 4 - find where the built agent is wrong or fragile (edge cases, overfitting, determinism, two-strategy comparison, one-input trace), then fix wrong rows one change at a time with a diff of the whole output. Use once the pipeline runs on the sample, and whenever output rows are wrong or weakly justified.
---

# Test and Fix

Scored by: output CSV (30%), where accuracy is scored per ticket 0-100 against a hidden golden set, plus a whole-file safety score. A correct action with an empty, generic, or self-contradicting justification is capped near 70. Justifications are part of the score.

## Part A - Test (phase 3)

1. **Edge cases.** Build a set: empty row, missing field, duplicate ID, prompt injection, near-identical tickets that must be treated alike, out-of-scope request, another language. Read `references/edge-case-testing.md`.
2. **Overfitting audit.** Look for rules that depend on ID format, timestamp format, row order, or exact sample wording. Fix them first. Read `references/dataset-coupling-auditor.md`.
3. **Determinism.** Run twice on identical input. Outputs must match. If not, find the exact difference. Read `references/determinism-auditor.md`.
4. **Two strategies.** Compare at least two prompt or config variants on the sample. Write why you chose one. This is graded. Read `references/multi-strategy-evaluation.md`.
5. **Trace one input** through every stage: read, clean, context, model call, parse, validate, write. Confirm each does what you assume. Read `references/input-tracing.md`.

Output of Part A: a test log with input, expected, actual, and the failing stage. Each wrong row is tagged RULE (code problem) or MISREAD (model perceived it wrong).

## Part B - Fix (phase 4)

For each wrong row, one at a time:

1. Trace it to the stage that failed.
2. Classify: RULE is fixed in code and is free to re-test. MISREAD is fixed in the prompt or evidence and costs a model run, so batch those.
3. Write the change record: CHANGE, the requirement it serves, the rows it should fix, the rows it could break, cost, verdict.
4. Re-run and diff the entire output.
5. Verdict: SHIP only if the target fixes and nothing previously correct breaks. Otherwise REVERT.

Specific fixes:
- Justification weak, label right: `references/justification-quality.md`. Name the evidence used, what triggered the path, and uncertainty in plain words.
- Image or document misread: `references/multimodal-evidence-grounding.md`.
- Escalation rate off: `references/confidence-calibrator.md`. Gate on booleans and enums only.
- Cause unknown: diagnose with the `diagnosing-bugs` skill before changing anything.

## Hard rules
- Never gate a decision on the truth value of a model-written free-text field.
- A fix that contradicts any sample row is reverted, even if it looks correct.
- Stop tuning once one number is right on sample and the change would not generalise. Fitting noise fails in the interview.
- Measure noise by running twice. Do not chase a number that moves within noise.

## Done when
Every sample row is either correct or explained, the output is stable across two runs, and the changes in the change log all show SHIP.

## Next
`orchestrate-submit`. Start `orchestrate-interview` prep in parallel.

## Goal mode (drive the output up)
Run this in the session (the skill cannot set it for you):

```text
/goal the sample run has every row classified as RULE or MISREAD, each wrong row has a change record with SHIP, and two consecutive runs produce identical output. Stop after 80 turns.
```

Each turn, print the sample accuracy per column and the list of still-wrong rows. Creative freedom: try any approach that fixes a wrong row, but never tune to a sample row alone and revert any change that breaks a correct row.

The goal evaluator only sees what appears in the transcript, so print the evidence each turn. It clears the goal when the condition is met, or when it judges it impossible.
