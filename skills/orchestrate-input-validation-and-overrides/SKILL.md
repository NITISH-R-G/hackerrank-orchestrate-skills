---
name: orchestrate-input-validation-and-overrides
description: Validate inputs before they reach a model call (not just outputs after), and use deterministic rule-based overrides for cases where model discretion shouldn't apply — for HackerRank Orchestrate agents or any LLM pipeline handling untrusted structured input. Use when writing the ingestion/input-loading stage of an agent, when deciding whether a decision should be left to the model or forced by a rule, or when designing confidence-based safety gates.
---

# Orchestrate: Input Validation and Deterministic Overrides

**Source**: *The Engineer's Notebook*, "Getting better at HackerRank Orchestrate" (Shloka Shah) — names input validation *before* model calls as a distinct requirement from output validation *after* generation, and separately names "rule-based overrides for cases where model discretion shouldn't apply" as part of a reliable guardrail design. Reinforced by a first-hand #1-ranked participant case study (Medium, "How I went from 122 to 1"), which describes replacing a binary safety flag with a **conditional, confidence-gated** safety gate: a hard block fires only when the model *cannot cite specific evidence*, rather than automatically downgrading every verdict whenever a low-confidence signal appears — preventing legitimate findings from being silently overridden by noisy metadata.

## Two validation layers, not one

`orchestrate-schema-guardrails` (already in this collection) covers validating model *output* against the expected schema. This skill covers the layer before that: validating *input* before it ever reaches a model call.

**What input validation catches, specifically**: empty or missing required fields, duplicate IDs across the dataset, malformed file references (an image path that doesn't resolve, a corpus document ID that doesn't exist), and — per the Orchestrate dataset's known design — prompt injection attempts embedded in ticket/claim text. Catching these before a model call means you're not spending a model call (and its cost/latency/failure surface) on an input you already know is broken, and you have a clean, deterministic place to log why a given input was rejected or routed differently.

## When to override the model rather than ask it

Not every decision should be left to model discretion. The organizer guidance names this as a deliberate design choice: some cases warrant a **rule-based override** — a deterministic check that forces an outcome regardless of what the model would have said. Candidates for this:
- A structurally invalid input (missing required evidence, per the challenge's own schema) — escalate or reject by rule, don't ask the model to guess around a data problem.
- A confirmed prompt-injection pattern — route to escalation by rule once detected, rather than trusting the model to have resisted it (defense in depth: even a well-prompted model can be talked out of its instructions; a rule doesn't get talked out of anything).
- A case explicitly outside the domain the corpus covers — deterministic "insufficient grounding" rather than a generated guess.

## Confidence-gated, not binary, safety layers

The case study's specific lesson: a binary safety flag ("any suspicious signal → override the verdict") produces false positives that silently discard correct findings. The fix that took them from rank 122 to rank 1 on this dimension was making the override **conditional on the model being unable to cite specific evidence** — i.e., the override fires on an absence of grounding, not merely on the presence of a low-confidence signal. Design your safety gates the same way: ask "can the system point to specific evidence for this decision," and gate on that answer, rather than on a fuzzy confidence score alone.

## Practical checklist

- [ ] Every required input field is checked for presence/validity before any model call is made for that input
- [ ] At least one rule-based override exists for a case type where you've deliberately decided the model shouldn't have the final say
- [ ] Safety/risk gates check for "can this be justified with cited evidence," not just a raw confidence threshold
- [ ] Both layers (input validation, output validation) are visibly separate stages you could point to in an `orchestrate-input-tracing` walkthrough
