---
name: orchestrate-interview
description: Orchestrate's 30-minute AI judge interview (30% of the score). Build the constants provenance sheet, prepare answers to the nine probed topics using mechanisms and measured trade-offs, and rehearse honest limits. Use from mid-build onward, and again before submission.
---

# Interview Preparation

Scored by: technical depth and ownership 40%, problem understanding and judgment 25%, communication clarity 20%, honesty and self-awareness 15%.

The judge's past criticism was about owning details: "knowing your own constants." It did not challenge architecture, methodology, AI workflow, or honesty. Depth of ownership is the bar.

## Step 1 - Constants drill (do first)
Fill `references/CONSTANTS-template.md` for every number in the code: thresholds, timeouts, regex bounds, retrieval parameters, confidence floor and ceiling, resize sizes, evidence counts. Label each MEASURED, SPEC, STANDARD, BOUND, or JUDGEMENT.

Rules:
- Never write "chosen after evaluation" for a value you did not sweep.
- For MEASURED values, have the losing alternative and its number ready.
- For STANDARD values, say plainly that you did not tune them, and why that is a deliberate choice.

## Step 2 - Nine topics, one prepared answer each
Structure each answer as: claim, evidence or mechanism, the alternative you rejected, the limit.

1. **Architecture.** One-sentence shape of the system, then where the model is called and where code decides.
2. **Deterministic vs LLM reasoning.** Which decisions are code and why. Example mechanism: the model can only escalate a high-risk case; it can never downgrade one, because the deterministic gate runs first.
3. **Arbitration.** How conflicting signals are resolved. Name the order of rules.
4. **End-to-end flow.** One input traced from load to CSV row. Use the trace you wrote in `orchestrate-test-fix`.
5. **Retrieval.** What you used and why, with one case where it mattered and one failure mode.
6. **Confidence calibration.** What confidence means in your system, its source, and how you checked it.
7. **AI-assisted workflow.** Where AI helped, what you rejected, what you checked yourself. Say "I decided" more than "the AI created".
8. **Trade-offs.** One decision you would reverse, and why.
9. **Honesty.** Three specific limits, what you did not test, and what you would improve next.

## Step 3 - Rejection story
Prepare one measured change you tried and reverted, with the numbers that killed it. This is the single strongest answer to "what did you learn?" Source: rejection log in `orchestrate-reference/references/playbook-principles.md`.

## Step 4 - Rehearsal
- Practise aloud, out loud, timed at 30 seconds per answer.
- Answer depth matters more than turn count. Short answers scored lowest. Give one concrete example per answer, then stop.
- For each answer ask: does the code actually do this? If not, change the answer, not the code, unless the code is wrong.

## Step 5 - Judge's likely follow-ups
- "Show me where that is in the code." Know the file and function.
- "Why that number?" Use the CONSTANTS sheet.
- "What happens when input is adversarial?" Use the security trace from `orchestrate-submit`.
- "How would this run in production?" Cost, rate limits, monitoring, checkpointing from `orchestrate-submit` and `orchestrate-build`.
- "What would you do with more time?" Name one specific improvement with its expected metric effect.

Model-answer examples and judge-prep notes: `references/judge-prep.md` in `orchestrate-reference`.

## References in this skill
- `references/CONSTANTS-template.md`
- `references/interview-coach.md`, `references/interview-readiness.md`, `references/mentor.md`
