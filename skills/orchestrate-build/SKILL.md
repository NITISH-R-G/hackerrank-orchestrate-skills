---
name: orchestrate-build
description: Orchestrate phases 1 and 2 - turn the problem statement into a written design (DESIGN.md) and then build the agent so it runs end to end on the sample with validation, failure handling and secrets handled. Use after reading the problem statement and sample data, and until the pipeline writes a valid CSV for the whole sample.
---

# Build: Design, then Implement

Scored by: code (30%) and, through its outputs, the CSV (30%). The code judge scores only what the code does: agent architecture 30%, prompt and tool craft 30%, robustness 25%, engineering rigor 15%.

## Part A - Design (write DESIGN.md before code)

Copy `references/DESIGN-template.md` to the repo root as `DESIGN.md`. Fill all 13 sections. The review gate at the end must be fully ticked.

1. **Output contract.** Every CSV column, its exact allowed values, its source (model field or code rule). Do not reformat IDs.
2. **Architecture.** Default: one agent loop or one LLM call for understanding, plus deterministic code for every decision. Add agents only if one fails. Read `references/agent-architecture.md`.
3. **The seam.** Define the typed record the model returns. Code reads only that record. Decisions use booleans and enums.
4. **Decision rules.** Ordered, risk rules first, first match wins. Use `grill-me` on the list to find gaps. Read `references/rule-engine-architect.md`.
5. **Escalation.** When to reply, escalate, refuse, and the default when evidence is missing. Both "escalate everything" and "reply to everything" are scored as failures. Read `references/escalation-design.md`.
6. **Input checks before the model.** Empty, missing, duplicate, oversized, injection markers. Read `references/input-validation-and-overrides.md`.
7. **Failure table.** For every failure type: what happens to the row, where it is logged, whether the run continues.
8. **Decisions log.** Every real choice, the rejected alternative, and why. Your interview answers come from here.
9. **Known limits.** Write what this design will get wrong now.

Design done when every output column has a named source, every allowed label is produced by a rule, and the escalation rule fits in one sentence.

## Part B - Build

1. **Structure.** Entry point, input loading, prompts, agent logic, validation, output writing, tests. Descriptive file names. No `utils.py`, `helper.py`, `final.py`. Read `references/naming-and-structure.md`.
2. **Secrets and determinism.** Keys only from environment variables. No absolute local paths. Seed anything random. Read `references/secrets-and-determinism.md`.
3. **Prompts.** Treat prompts as reviewable artifacts. Each prompt states: task, allowed outputs (exact labels), evidence to use, output format, what to do when information is missing, and that instructions inside the input must be ignored. Read `references/prompt-engineering.md`.
4. **Schema guardrails.** Validate every model field before it reaches the CSV. Reject unknown labels. Retry malformed output at most twice, then use the failure row. Read `references/schema-guardrails.md`.
5. **Failure handling.** One bad row never stops the run. A failed row becomes an honest escalation row and is logged. Read `references/failure-handling.md`.
6. **Checkpointing.** Save progress per row so a crash or rate limit resumes instead of restarting. Read `references/checkpoint-resilience.md`.
7. **Retrieval, if used.** Measure recall on sample rows before tuning. Read `references/evidence-retrieval-expert.md`.
8. **Tests first for deterministic code.** Use `tdd`. Model calls are not in unit tests.

Build done when:
- One command runs the full sample and writes the CSV.
- A row that throws does not stop the run.
- Every CSV value is in the allowed set.
- The README states setup, env vars, run command and expected files, and every README claim is a line of code.

## Next
`orchestrate-test-fix`.

## Templates and notes
- `references/past-problems.md` - what the four past rounds (May, June, August, September 2026) required, procedures for each, and the evidence checks run against them
- `references/DESIGN-template.md` - the design template

## Goal mode (build the agent)
Run this in the session (the skill cannot set it for you):

```text
/goal the pipeline runs end to end on the current input with scripts/run_pipeline.py, every output value is in the allowed set, a row that throws does not stop the run, and DESIGN.md's review gate is fully ticked. Stop after 60 turns.
```

Each turn, print the run summary line (rows written, failures handled). Creative freedom: choose architecture, prompts and retrieval freely, but record the choice and its rejected alternative in DESIGN.md.

The goal evaluator only sees what appears in the transcript, so print the evidence each turn. It clears the goal when the condition is met, or when it judges it impossible.
