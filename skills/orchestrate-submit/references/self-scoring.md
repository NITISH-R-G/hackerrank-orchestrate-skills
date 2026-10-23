---
name: orchestrate-self-scoring
description: Honestly estimating how a HackerRank Orchestrate submission (or similar multi-signal AI evaluation) would score across every rubric dimension before submitting, to find the weakest area while there's still time to fix it. Use before final submission of any Orchestrate-style challenge, or whenever the user asks "how would this score" / "is this ready to submit" / wants a pre-submission quality estimate.
---

# Orchestrate Self-Scoring

The single highest-leverage activity in the last few hours of a timeboxed challenge is finding your own weakest dimension before a judge does — because at that point you can still act on it. This skill is a structured, honest self-audit against the four published signals, not a confidence-boosting exercise.

## Ground rule: score against evidence, not effort

The instinct under deadline pressure is to score generously because you *worked hard* on something. Don't. Score against **what a reviewer would actually see**, the same evidence-anchored discipline the real scoring uses. Time spent is not evidence of quality.

## The four-signal self-audit

### 1. Code zip (30%) — score 0–5 per row, be specific about why

| Check | Evidence required |
|---|---|
| Is there a genuine agent loop, or a decision tree with LLM calls in it? | Point to the actual function. If you can't point to one place where the model decides what happens next, this is a decision tree. |
| Are tools well-named, well-described, individually testable? | Open the tool definitions file. Would a stranger know when to use each tool from its description alone? |
| Are prompts extracted, readable, and deliberate? | Are they in named files/constants, or inline f-strings? |
| Are failure paths (malformed output, tool error, step cap) handled explicitly? | Find the code for each. If it's absent, that's a 0 on this row, not an assumption of graceful degradation. |
| Does the README explain design decisions, not just usage? | Read it as a stranger would. Does it justify choices or only describe commands? |

Run `orchestrate-agent-architecture`'s checklist directly against your actual code, not from memory.

### 2. Output CSV (30%) — sample and grade, don't eyeball

Pull 5–8 rows at random (not your favorites) and grade each on the Chakra-style 4-point scale:
- **3**: specific evidence cited, KB reference is real, reasoning connects evidence to verdict
- **2**: right verdict, generic or thin justification
- **1**: wrong reasoning, or reasoning that doesn't match the verdict
- **0**: no real justification present

If your sample average is below 2.5, this is your highest-leverage fix — `orchestrate-justification-quality` is the companion skill, and improving justifications is almost always faster than it looks because it's a prompt/schema change, not a rewrite.

Also check: does your output actually parse and load as valid CSV? A malformed export is a correctness failure independent of everything else, and it's the single dumbest way to lose points.

### 3. AI chat transcript (10%) — this one you can't fix retroactively, only assess

Skim your actual transcript with fresh eyes:
- Is there visible planning before major decisions, or does it read as request-accept-request-accept?
- Is there at least one visible moment of rejecting or substantially revising AI output with stated reasoning?
- Is there visible debugging dialogue (hypothesis → test → conclusion), or paste-error-get-fix?

If the answer is mostly no and you still have build time left, this is the one signal where **your remaining behavior can still improve the score** — start narrating decisions from this point forward. It won't retroactively fix earlier messages, but a transcript that improves partway through is honest and still better than one that never does.

### 4. AI judge interview (30%) — you haven't taken it yet, so audit readiness, not performance

- Do you have a specific, concrete answer ready for "walk me through your architecture"?
- Do you have a specific, concrete answer ready for "what's the hardest problem you solved"?
- Do you have 2–3 **real, specific** limitations ready to disclose?
- Can you defend your key design tradeoffs with a stated cost of the choice you made, not just its benefit?

If any of these is "I'd wing it," that's unfinished work, not a soft skill you either have or don't. Run `orchestrate-interview-readiness` before the interview, not during it.

## Producing the estimate

Weight your per-signal assessment by the published weights (30/30/10/30) to get a single number, but **the number is not the point — the gap is.** A submission at an even 3.5/5 across all four signals is in a stronger position than one at 4.5 on code and 2 on everything else, because of the stated finding that *no single metric reproduces the leaderboard* — balance beats peaks.

State the result as:
1. A per-signal score with the specific evidence behind each
2. The single lowest-scoring signal, named explicitly
3. The cheapest fix available for that signal given remaining time
4. Whether that fix is worth doing versus polishing elsewhere

## The honesty check

Before finalizing, ask one question: *if I handed this exact self-assessment to someone else and asked them to grade my code/output/transcript independently, would they land within one point of me on each signal?* If you're not confident they would, you're grading generously. Go back and find the specific evidence for each score, the same discipline `orchestrate-justification-quality` demands of the agent's own output — apply it to yourself.
