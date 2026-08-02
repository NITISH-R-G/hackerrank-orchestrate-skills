# ADR-0001: Deterministic rule engine over an LLM classifier

**Status:** Accepted
**Memory:** `orchestrate memory recall D-rule-engine`

## Context

A message router has to assign an action, a message type, and a reason.
An LLM classifier over raw message text is the default choice in 2026 —
it's less code, and "just ask the model" generalizes to cases a rule
author didn't anticipate.

## Decision

A three-tier deterministic rule engine — SAFETY → RELATIONSHIP/URGENCY →
ENGAGEMENT → DEFAULT — with first-match-wins semantics, evaluated over
structured features extracted from the message.

## Why (three measured properties of the data, not a style preference)

1. **The labeled reasons were templated.** 24 distinct strings across 30
   labeled rows. Ground truth states which *rule* fired, not what the
   message said in free text — the label format itself tells you what's
   being scored.
2. **One labeled row was a prompt-injection attack** whose correct label
   was `mute/scam`. A rule engine is structurally immune to it: message
   text never enters a decision-making prompt, so there is nothing to
   inject *into*.
3. **Every safety-critical signal was a structured field**, not prose
   requiring semantic understanding to extract.

## Consequences

- **Positive:** one output hash across 5 processes × 5 `PYTHONHASHSEED`
  values — full determinism, for free. Every decision is attributable to
  a named rule. Reachability and shadowing are provable (see ADR-0004),
  not merely tested by sampling.
- **Negative:** the rule set only expresses what its author anticipated.
  A genuinely novel phrasing of a known category can miss, where a
  classifier might generalize.
- **Boundary:** this decision is about the *decision path*. Model output
  (OCR, ASR) still feeds structured features into the rules — see
  ADR-0002 for where a model IS allowed to act, and how tightly boxed in.

## Alternatives considered (and rejected, with the reason)

| Alternative | Rejected because |
|---|---|
| LLM classifier over raw message text | Fails all three properties above — no injection immunity, no determinism, and the ground truth wasn't scoring free-text understanding in the first place |
| Hybrid: LLM with rule fallback | Same injection surface as a pure classifier, on the rows where it's consulted |

## Reconsider if

The type taxonomy grows past what ~40 rules can express without
collisions, or a future dataset's labeled reasons turn out to be
free-form prose rather than templates — either would mean the property
this decision rests on no longer holds.
