---
name: orchestrate-multi-strategy-evaluation
description: Compare at least two distinct strategies, prompts, or configurations against HackerRank Orchestrate's sample dataset, and document the reasoning behind the final choice — a graded requirement in the multi-modal-review challenge and strong practice for any Orchestrate challenge. Use when deciding between two implementation approaches (e.g. two prompt versions, single-pass vs. multi-pass classification, different retrieval strategies), or when writing the final approach documentation a submission requires.
---

# Orchestrate: Multi-Strategy Evaluation

**Direct evidence**: the multi-modal-review (June) challenge's evaluation criteria explicitly require *"comparison of ≥2 strategies/prompts/configurations"* and *"final approach documentation"* as mandatory analysis — not optional polish. This is a formalized, graded version of ordinary good engineering practice: don't ship your first idea without checking whether a second one does better.

## What this looks like in practice

1. **Build against the sample/dev dataset, not the golden dataset you don't have.** Every Orchestrate challenge ships a `sample_*.csv` with known expected outputs specifically for this purpose.
2. **Implement at least two genuinely different approaches** to some meaningful part of the system — not two trivial variations. Examples: a single-call classification prompt vs. a two-step "extract evidence, then classify" pipeline; keyword-based corpus retrieval vs. embedding-based retrieval; a strict rule-based escalation policy vs. a model-judged one.
3. **Score both against the sample set** using the same metric (accuracy against known labels, or a proxy metric if labels are qualitative) and record the numbers, not just an impression.
4. **Document why you chose what you chose** — including what the losing approach got wrong, specifically. "Approach B mis-classified 3 of 20 sample tickets because it conflated `bug` and `product_issue` when a ticket mentioned an error message without describing a workflow" is evidence. "Approach A seemed to work better" is not.

## Why this matters even for challenges that don't explicitly require it

The interview is designed to probe exactly this kind of comparative reasoning — HackerRank's own interview-prep guidance says to be ready to discuss *"what you tested and what limitations remain."* An answer of "I tried the first thing that came to mind and it worked" is a materially weaker interview answer than "I tried two approaches, here's what the sample data showed about each, here's why I picked the one I did, and here's the specific failure mode the other one had that mine still shares." The second answer demonstrates process — the exact thing HackerRank's stated philosophy says it's now measuring instead of "did you get the right answer."

## This connects directly to your chat transcript score

Working through two approaches, comparing them, and picking one with stated reasoning *in front of your AI coding tool* is precisely the kind of visible planning-and-evaluation process `orchestrate-ai-collaboration-transcript` asks you to make legible in the AGENTS.md-format log — this skill produces the substance; that one makes sure it's captured.

## Anti-pattern this prevents

Retrofitting a comparison after the fact, for the documentation, without having actually run it. An interviewer probing specifics ("what was the accuracy difference between the two approaches on the sample set?") will surface a fabricated comparison quickly — and per `orchestrate-interview-readiness`, an evidence-anchored interview scorer treats vague or unverifiable claims as unmet expectations regardless of whether the underlying work was real.
