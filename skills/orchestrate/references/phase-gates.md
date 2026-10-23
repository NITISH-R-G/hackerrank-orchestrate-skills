---
name: orchestrate-phase-gates
description: The master sequencing skill for HackerRank Orchestrate (or any timeboxed agent-building hackathon) — enforces an ordered set of quality gates from planning through submission, and names which companion skill owns each gate. Use this at the START of any Orchestrate-style challenge, whenever the user mentions HackerRank Orchestrate, an agent-building hackathon, a 24-hour AI agent challenge, or asks "what should I do next" mid-build. Also use when a submission deadline is approaching and you need to know what's still unchecked.
---

# Orchestrate Phase Gates

HackerRank Orchestrate scores four independent artifacts, and the published post-mortem of the May 2026 event found that **no single metric reproduced the leaderboard** — the winners were balanced across all four, not exceptional at one. That single fact should drive your entire time allocation, because the instinct under time pressure is to sink everything into code and treat the other three as afterthoughts. That is the losing strategy, mathematically: code is only 30%.

## The scored surface (from HackerRank's published breakdown)

| Artifact | Weight | What it actually measures |
|---|---|---|
| Code zip | 30% | Agent design, architecture, tool integration, prompt quality, robustness, engineering standards |
| Output CSV | 30% | Functional correctness vs. a golden dataset — **and the soundness of each decision's justification** |
| AI chat transcript | 10% | How you *directed* your AI coding tools — planning, constraints, debugging, iteration |
| AI judge interview | 30% | Technical depth, problem understanding, communication clarity, **self-awareness about limitations** |

Two implications people miss:

1. **70% of the score is not your code.** Output quality, your transcript, and a live interview dominate. Budget time accordingly — a common failure is arriving at hour 23 with elegant code, an unreviewed CSV, and no interview prep.
2. **Justifications are scored, not just actions.** The CSV isn't a pure correctness check. A right answer with incoherent reasoning loses points that a right answer with sound reasoning keeps.

## The gates

Run these in order. Each gate has an owning skill that does the actual work — this skill is the sequencer, not the executor.

```
Gate 0  Understand the rubric        → (this skill)
Gate 1  Plan & decompose             → brainstorming / writing-plans
Gate 2  Agent architecture           → orchestrate-agent-architecture
Gate 3  Robustness & adversarial     → orchestrate-robustness
Gate 4  Implement                    → tdd, implement
Gate 5  Justification quality        → orchestrate-justification-quality
Gate 6  Transcript hygiene           → orchestrate-ai-collaboration-transcript  (runs CONTINUOUSLY, not once)
Gate 7  Self-score against rubric    → orchestrate-self-scoring
Gate 8  Interview readiness          → orchestrate-interview-readiness
Gate 9  Final submission review      → orchestrate-submission-review
```

**Gate 6 is not a phase.** Transcript quality is determined by how you worked the entire time — it cannot be retrofitted at the end. Read that skill *before* Gate 1, then let it shape how you prompt throughout.

## Suggested time allocation for a 24-hour event

This is a starting point, not a prescription — adjust to the specific challenge:

| Hours | Focus | Why |
|---|---|---|
| 0–2 | Gates 0–2: read the rubric, read the data, plan, design the agent loop | Decisions made here are expensive to reverse later |
| 2–4 | Gate 3: enumerate adversarial cases before writing handling code | Knowing what you're defending against changes the architecture |
| 4–14 | Gate 4: implement, testing as you go | The bulk, but deliberately not the majority |
| 14–17 | Gate 5: review every output row's justification, not just its verdict | Half the CSV score lives here and is usually neglected |
| 17–19 | Gate 7: self-score honestly, fix the weakest dimension | Finding your own gap beats having a judge find it |
| 19–21 | Gate 8: interview prep — rehearse limitations, not just features | 30% of score, near-zero prep by most participants |
| 21–23 | Gate 9: final review, packaging, submission checks | Never leave packaging to the last 30 minutes |
| 23–24 | Buffer | Something will go wrong |

## The gate discipline

A gate is passed when its owning skill's checklist is satisfied — not when you feel done. If you're tempted to skip a gate because you're behind schedule, skip *depth within* a gate rather than skipping the gate entirely: a rushed 20-minute interview prep massively outperforms none, because it's 30% of the score either way.

**The one gate never to skip:** Gate 7 (self-scoring). It's the cheapest gate and the only one that tells you which of the other gates you under-invested in while there's still time to act on it.

## A caveat on specificity

HackerRank's published material describes the four-artifact structure and the evaluation philosophy, but per-challenge rubrics live behind the contest login. The weights and signals above come from HackerRank's own post-mortem of the May 2026 support-agent event and their published Chakra scoring methodology. **Always read the actual challenge page for the event you're in** — if it contradicts anything here, the challenge page wins.
