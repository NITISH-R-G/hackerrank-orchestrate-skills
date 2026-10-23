---
name: orchestrate-submit
description: Orchestrate phases 5 and 6 - self-score all four sections against the rubric, harden security and robustness, check cost numbers, then run the spec audit, consistency check and release gate before packaging the submission. Use once the output is stable, and in the final two hours before submitting.
---

# Score, Harden and Submit

## Part A - Score and harden

1. **Self-score each section with evidence.** Code, Output CSV, Transcript, Interview. Write one number and one proof per section. Never invent a number. Read `references/self-scoring.md`.
2. **Code evaluator pass.** Run the evaluator checks on your repo for architecture, prompts, robustness, rigor. Fix what they find. Read `references/evaluator.md`.
3. **Security pass.** Prompt injection, unicode tricks, very long input, malformed input, path traversal. Every failure must produce a valid row, never a crash, and injection must not change a decision. Read `references/security-auditor.md`.
4. **Robustness pass.** Adversarial and ambiguous inputs. Read `references/robustness.md`.
5. **Multimodal, only if images are in the challenge.** Read `references/multimodal-auditor.md`.
6. **Cost and ops.** Calls, tokens, cost per row, rate limits. Put the numbers in the README with their source. Read `references/cost-and-ops-metrics.md`.
7. **Weakest section.** Name it. Plan one fix. Do the fix in the time left.

## Part B - Submit

1. **Freeze.** No new features. Only fixes for already-found defects.
2. **Spec audit.** Check every column name, allowed value, separator, row count, and required file against the literal problem statement. Read `references/spec-auditor.md`.
3. **Consistency.** The CSV, the code, and the README come from the same commit. Re-run from clean and confirm the CSV matches. Read `references/submission-validator.md`.
4. **Open the CSV as a stranger.** Missing IDs, duplicates, similar cases treated differently, justifications that contradict the status. Read `references/submission-review.md`.
5. **Release gate.** Work through `orchestrate-reference/references/release-checklist.md`. Each line needs a command output as proof.
6. **Package.** No secrets, no absolute paths, no generated junk. Clone to an empty folder and run only the README steps. Read `references/release-engineer.md`.
7. **Transcript.** Confirm the required transcript export is complete and not truncated.

## Done when
The release checklist is fully ticked with proof, the clean-folder run reproduces the CSV, and the self-score has a named weakest section with its fix applied.

## Next
Nothing. Finish interview prep if you have not.

## Goal mode (ship a clean submission)
Run this in the session (the skill cannot set it for you):

```text
/goal orchestrate-package reports READY TO SUBMIT, the self-score has every section scored with evidence, and the release checklist in orchestrate-reference has a command output for every line. Stop after 40 turns.
```

Each turn, print the checker's PASS/FAIL lines. Creative freedom: fix any failing item in code or docs, but do not change the output contract to make a check pass.

The goal evaluator only sees what appears in the transcript, so print the evidence each turn. It clears the goal when the condition is met, or when it judges it impossible.
