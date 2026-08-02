---
name: orchestrate-rule-engine-architect
description: Design a deterministic routing engine that is auditable and injection-immune. Use when choosing between rules and an LLM classifier, and when ordering rule tiers. Includes how to prove no rule is dead or shadowed.
---

# Orchestrate: Rule Engine Architect

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## When a rule engine beats an LLM classifier

Three conditions, all measurable before you commit:

1. **The targets are templated.** In the real build, 30 labeled rows contained only
   **24 distinct reason strings**, several repeating verbatim. Ground-truth reasons
   state *which rule fired*. A rule engine reproduces that exactly; a generative model
   approximates it.
2. **The dataset attacks LLM routers.** One labeled row was a prompt-injection attack
   whose correct label was `mute/scam`. A rule engine is **structurally immune** —
   message text never enters a decision-making prompt.
3. **The safety-critical signals are structured data**, not prose: verification flags,
   opt-out state, sender role, dismissal history.

The model layer earns its place only where structured data genuinely cannot reach —
reading a poster, hearing a voice note.

## Tier ordering is a policy statement

```
SAFETY  ▶  RELATIONSHIP / URGENCY  ▶  ENGAGEMENT  ▶  DEFAULT
```

Safety sits above engagement because the spec says risk is muted *"regardless of the
user's usual engagement."* Ordering encodes that sentence. Write the reason in a
comment next to the tier.

## Two rule-level failures worth knowing

**Shadowing.** A rule whose condition is *implied by* an earlier rule's condition can
never fire. Real example: a rule requiring `A and B and not C` sat below a rule
requiring only `B`. Strictly unreachable — proven by implication, not sampling. It was
deleted; the output hash was unchanged, which is the proof it was dead.

**Contradiction.** Two rules encoding opposite policies for the same situation. Real
example: one rule routed a distress message from a known contact to `notify`, while
another correctly excluded distress-plus-payment-request as a scam pattern. Patching
the first would have made it dead code, so it was deleted.

## Proving no rule is dead

Search the **full** feature space, and require the rule *itself* to win — not merely
to have a satisfiable condition.

A prober that got this wrong reported **3 dead rules and 7 shadowed**, all false: it
randomised only fields matching a naming prefix, and returned the first condition match
rather than checking who won. After correction: **1 genuinely unreachable rule, 0
shadowed.**

## The checklist

- [ ] Every rule fires on real data, **or** is proven reachable on a synthetic input
- [ ] No rule's condition is implied by an earlier rule's
- [ ] Tier order justified by a quoted line of the spec
- [ ] Reason strings drawn from observed ground-truth templates
- [ ] The engine never raises — a failed row degrades to a safe default
- [ ] Rule count, tier distribution, and firing counts reported
