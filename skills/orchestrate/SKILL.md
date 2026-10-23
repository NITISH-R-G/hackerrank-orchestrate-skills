---
name: orchestrate
description: START HERE for HackerRank Orchestrate. Master plan for the 24-hour challenge - scoring targets, the phase order, which orchestrate-* skill to run next, what to do when a step fails, and the transcript discipline that applies all day. Use at the start of the challenge, whenever you are unsure what to do next, or when anything fails.
---

# Orchestrate: Master Plan

Goal: maximise the final score in every section. Final = 0.30 Code + 0.30 Output CSV + 0.30 AI Interview + 0.10 Transcript. Ties break in the order Interview, Code, Output CSV, Transcript.

Balance wins. Past winners were strong in all four. A huge score in one section does not carry the rank.

## The six skills and when to use each

| Skill | Use it when | Ends when |
|---|---|---|
| `orchestrate` (this) | Start, lost, or anything failed | You know the next skill |
| `orchestrate-build` | Problem statement and sample data are read | Pipeline runs end to end on sample, DESIGN.md written |
| `orchestrate-test-fix` | Pipeline runs on sample | Wrong rows are classified and fixed, output is stable |
| `orchestrate-submit` | Output is stable | Self-score done, hardening done, packaging checked |
| `orchestrate-interview` | Output is stable (start prep earlier) | You can defend every number and decision |
| `orchestrate-package` | Output is final. Check submission readiness against the statement and build `submission/` | — |
| `orchestrate-score` | Before submit, or to pick the next fix. Estimated score with published weights | — |
| `orchestrate-reference` | You need a ready-to-paste prompt, a principle, a checklist, or past-winner patterns | Never. Read on demand |

Order: this -> build -> test-fix -> submit (with interview prep running in parallel from hour 14) -> final freeze.

## Clock for 24 hours (adjust once the problem is known)

| Hours | Do | Skill |
|---|---|---|
| 0-1 | Read problem statement, sample data, rubric. Write output contract | orchestrate, build |
| 1-3 | DESIGN.md, decision rules, escalation rules, failure table | build |
| 3-8 | Build pipeline. Run on sample. First CSV | build |
| 8-14 | Test edge cases and overfitting. Fix wrong rows in one-change loops | test-fix |
| 14-17 | Review every justification. Second strategy comparison | test-fix |
| 17-19 | Self-score, security pass, cost numbers | submit |
| 14-20 | Interview prep in parallel: CONSTANTS.md, nine topics, rehearsal | interview |
| 21-23 | Clean run from empty folder, spec audit, release checklist | submit |
| 23-24 | Buffer. No new features | - |

## Failure routing (what to run when)

| Symptom | Next step |
|---|---|
| Whole run crashes | build: failure-handling, checkpoint-resilience |
| Invalid label or JSON | build: schema-guardrails |
| Same input, different output | test-fix: determinism-auditor |
| Sample looks great, unsure it generalises | test-fix: dataset-coupling-auditor |
| Wrong row, cause unknown | test-fix: input-tracing, then diagnosing-bugs skill |
| Correct label, weak justification | test-fix: justification-quality |
| Image or document misread | test-fix: multimodal-evidence-grounding |
| Escalation rate wrong | test-fix: confidence-calibrator, build: escalation-design |
| Retrieval returns wrong document | build: evidence-retrieval-expert |
| Injection got through | submit: security-auditor, robustness |
| Cannot defend a number | interview: CONSTANTS.md |
| Stuck on score | submit: self-scoring, then fix the weakest section |

## Improvement loop (to get the best possible output)
1. Freeze the current CSV as baseline. Commit it.
2. Write the change record first: metric, expected gain, rows it could break, cost.
3. Make one change.
4. Re-run. Diff the WHOLE output, not only the target row.
5. SHIP only if the target improves and no previously correct row breaks. Otherwise revert.
6. Run twice to measure noise. Stop when the next change is within noise.

Prompt templates for this loop: `orchestrate-reference/references/prompt-templates.md`.

## Winning principles
1. A change is not an improvement until a named metric moves.
2. Measure blast radius: how many outputs changed.
3. Prove the counterfactual: disable the component and check that behaviour stops.
4. Compute the ceiling before optimising. If zero headroom, do not build it.
5. Keep a rejection log with the number that killed each rejected idea.
6. Every audit needs a negative control. A green check you have not tried to break proves nothing.
7. Audits are read-only.
8. The model describes, code decides. Decisions use booleans and enums, never free text.
9. Balance all four sections.
10. Own every constant (provenance labels in `orchestrate-interview`).

Source: `orchestrate-reference/references/playbook-principles.md`.

## Transcript discipline (apply to every prompt you send)
The transcript is graded: direction and ownership 35%, specificity 25%, iteration and verification 25%, safety awareness 15%.

- Before building: state the plan. What to read, produce, where the model reasons, where code enforces.
- Each prompt: name the file or function, the constraint (model, schema, threshold), and how you will check it.
- After each run: paste the real error or real wrong row. Say what you think caused it, then decide the fix.
- Push back out loud when the AI over-builds: "reject this, here is why."
- Never paste a log whose only content is "processed ticket N". That scores lowest.

Details: `references/transcript-engineering.md` and `references/ai-collaboration-transcript.md`.

## Hard rules
- Never tune against sample rows until one number matches. That is overfitting, and the interview exposes it.
- Do not overwrite the starter CLAUDE.md or AGENTS.md. Append to it.
- Every claim in docs must match code or a run. Never invent numbers.
- Keep a safe fallback output banked before any experiment.
- Never say "chosen after evaluation" for a value you did not sweep.

## Reference files in this skill
- `references/phase-gates.md` - the gate sequence from past rounds
- `references/scoring-rubric.md` - sub-weights for each section and judge probe order
- `references/transcript-engineering.md`, `references/ai-collaboration-transcript.md` - transcript scoring detail

## Goal mode (run the whole challenge)
Run this in the session (the skill cannot set it for you):

```text
/goal the challenge repo has output.csv for every input row, it passes skills/orchestrate-package/scripts/package_submission.py with no FAIL, the self-score in orchestrate-score has a named weakest section with its fix applied, and the interview CONSTANTS.md covers every number in the code. Stop after 150 turns.
```

Each turn, print the current checker result and the weakest section. Creative freedom: you may change the design, prompts, or rules to raise the score, but each change needs a change record (CHANGE, rows it should fix, rows it could break, VERDICT) and is kept only if no previously correct row breaks.

The goal evaluator only sees what appears in the transcript, so print the evidence each turn. It clears the goal when the condition is met, or when it judges it impossible.
