---
name: orchestrate-escalation-design
description: Design escalation and uncertainty-marking as a first-class, calibrated decision in a HackerRank Orchestrate agent — not a fallback bolted on after the main logic. Directly addresses the published finding that both escalate-everything and respond-to-everything fail. Use when designing the decision boundary between automated response and human escalation, or when reviewing whether escalation logic was designed deliberately or added reactively.
---

# Orchestrate: Escalation Design

**Direct evidence**: the support-agent challenge's starter repo states the hard requirement — *"Must escalate high-risk, sensitive, or unsupported cases"* instead of guessing. HackerRank's own description of the dataset confirms it's built with edge cases, prompt injection attempts, and jailbreaking tests specifically so that **escalating everything and replying to everything both result in failure** — meaning the graded signal lives almost entirely in a calibrated middle ground, not at either extreme.

## Why this can't be an afterthought

If escalation is implemented as "if confidence < threshold, escalate" bolted onto an otherwise-complete classify-and-respond pipeline, the threshold gets tuned by guesswork against however the demo happens to run — not against a considered model of *what kinds of cases actually warrant escalation*. The published dataset is specifically designed to punish that approach from both directions: too eager to escalate loses points for cases that should have been resolved automatically; too eager to respond loses points (and, in the adversarial cases, potentially demonstrates a real safety failure) for cases that needed a human.

## What "escalate deliberately" looks like as a design

Treat escalation as a genuine decision with named categories, not a catch-all:

- **High-risk**: cases where an incorrect automated response has real consequences (security, financial, legal-adjacent content)
- **Sensitive**: cases touching topics where automated handling is inappropriate regardless of confidence (this is where prompt-injection and jailbreak attempts should generally land — recognizing an adversarial pattern *is itself* a valid basis for escalation, not a failure to answer)
- **Unsupported**: the corpus genuinely doesn't contain grounding for a confident answer — this connects directly to `orchestrate-failure-handling`'s "mark uncertainty" discipline, applied specifically to knowledge-grounding gaps

Each category should have its own detection logic, not one shared confidence score covering all three — a case can be low-risk-but-unsupported (escalate for one reason) or high-risk-but-well-supported (escalate for a different reason entirely, regardless of confidence).

## Testing this specifically

This is where `orchestrate-edge-case-testing`'s consistency-check practice matters most: build a small adversarial test set yourself — a prompt injection attempt, a jailbreak attempt, a genuinely ambiguous ticket, a clearly-answerable ticket — and confirm the agent's escalation decisions are each individually defensible, not just that the aggregate escalation rate looks reasonable.

## Interview readiness

This is near-certain interview material given how explicitly the organizers describe the dataset's adversarial design. Be ready to name specific examples: "here's a case my agent escalated and why," "here's a case it resolved automatically and why that was the right call," and — most importantly — "here's a case I got wrong in testing and what I changed." That last one demonstrates the self-awareness the interview rubric explicitly rewards.

## Anti-pattern this prevents

A single global confidence threshold as the entire escalation policy. It's simple to implement, plausible-looking in a demo, and almost certainly wrong on the specific adversarial cases the dataset was built to include — because "confident" and "should be escalated regardless of confidence" are different questions a single number can't answer.
