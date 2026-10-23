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

## Step 3b - Depth targets (from the July HackerRank post)
Judge scores correlate with answer depth: total words r = 0.615, share of longer answers r = 0.631, concrete mechanisms and tradeoffs r = 0.583, very short answers r = -0.568. So every answer needs at least one mechanism, one number, and one limit, and should not be a one-liner.

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

## Goal mode (prepare the interview)
Run this in the session (the skill cannot set it for you):

```text
/goal CONSTANTS.md has a provenance label for every numeric constant in code, each of the nine topics has a prepared answer with one mechanism, one number and one limit, and the rejection story is written. Stop after 40 turns.
```

Each turn, print how many constants are unlabelled and which topic is still thin. Creative freedom: rewrite answers freely, but every claim must match what the code actually does; check the code before writing it.

The goal evaluator only sees what appears in the transcript, so print the evidence each turn. It clears the goal when the condition is met, or when it judges it impossible.
