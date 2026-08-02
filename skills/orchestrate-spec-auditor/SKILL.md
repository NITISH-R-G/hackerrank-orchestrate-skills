---
name: orchestrate-spec-auditor
description: Verify a submission against the literal text of problem_statement.md rather than your memory of it — every column, every allowed value, every separator, every required artifact. Use before any release, and immediately after any change to output formatting. Catches the class of defect that costs points mechanically, with no judgment call involved.
---

# Orchestrate: Spec Auditor

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Transcribe the spec's constants into your checker. Never import them from your own code.**

If your validator does `from router.schema import OUTPUT_COLUMNS`, it proves only
that your code agrees with itself. A checker built from constants typed out of
`problem_statement.md` is an independent witness.

## What this caught in a real build

The spec says evidence ids are **semicolon**-separated. Ground truth showed
`message_0013;message_0014`. An early audit script joined with commas for *display*
and the discrepancy was briefly mistaken for a defect in the submission. Reading the
spec line rather than the code settled it in one command.

Separately: `message_type` has **exactly 11 legal values**. A checker built from the
spec confirms all 11 were used and none illegal. A checker built from the code cannot
tell you that.

## The checklist

- [ ] Column **names and order** match the spec exactly — compare against a literal list
- [ ] One output row per input row, **same ids, same order**, no duplicates
- [ ] Every `action` value is in the spec's allowed set
- [ ] Every `message_type` value is in the spec's allowed set — and log how many of
      the legal values you actually use
- [ ] Numeric fields parse and sit inside the stated range
- [ ] Separators are exactly what the spec says (semicolon is not a comma)
- [ ] The "no evidence" sentinel is the exact string the spec names
- [ ] Every cited id **exists** in the history file
- [ ] Every required submission artifact is present — including the transcript

## Failure modes

- **Checking against your schema module.** Circular; proves nothing.
- **Assuming a separator.** Read the line. It costs ten seconds.
- **Forgetting the third artifact.** Most participants remember code and CSV and
  forget the chat transcript is explicitly listed as a must-have.

## Verification

Write it as a script that exits non-zero, not a document you read. A spec audit that
requires a human to remember to run it will be skipped at 3am.
