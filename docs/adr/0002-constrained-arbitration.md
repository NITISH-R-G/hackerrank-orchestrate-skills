# ADR-0002: LLM arbitration is opt-in and structurally boxed in

**Status:** Accepted
**Memory:** `orchestrate memory recall F-25-silent-arbitration`

## Context

ADR-0001 keeps the decision path deterministic. But a deterministic engine
can genuinely tie — two tiers matching with no clear precedence — and an
LLM arbitration step was built to break ties like that.

The first version of this feature shipped with a real defect: it was
**silently ON whenever an API key happened to be present**, because it was
feature-gated on credential presence rather than on explicit intent. That
put a network call and raw message text into a prompt on 6 of 110 rows with
no visible switch anywhere.

## Decision

Arbitration is:
1. **Off by default**, enabled only via an explicit `ARBITRATION=on`
   environment variable — never inferred from whether a credential exists.
2. **Scoped to escalation only** — its only possible action on the rows
   where it's eligible is to escalate, never to downgrade a safety
   decision.
3. **Measured before being trusted**, every time: on the labeled rows
   where it was eligible, the deterministic verdict was *already correct*,
   which meant every intervention it could make there was, by
   construction, a guaranteed regression.

## Consequences

- **Positive:** the capability exists for the case it's genuinely needed
  (an unresolvable tie), without becoming a standing security surface or a
  determinism hole by default.
- **Positive:** "gated on credential presence" is now a named anti-pattern
  this codebase checks for — see the `llm-decision` proposal class in
  `orchestrate_kit/mentor/taxonomy.py`, which flags exactly this risk for
  any future feature shaped like it.
- **Negative:** a genuinely ambiguous row that a model *could* resolve
  correctly stays unresolved unless a human explicitly opts in per run.
  That's treated as the safer default, not a limitation to hide.

## Alternatives considered (and rejected, with the reason)

| Alternative | Rejected because |
|---|---|
| Gate on credential presence (the original shipped behavior) | Silently on, no visible switch — the actual defect this ADR exists to prevent recurring |
| Remove arbitration entirely | Throws away a real capability for the rare genuine tie, to fix a gating bug that has a narrower fix |
| Let arbitration downgrade as well as escalate | Turns a bounded blast radius into an unbounded one — an arbitration mistake could then suppress a real safety signal |

## Reconsider if

A row class appears where the deterministic tiers genuinely tie *and* the
tie is resolvable from prose that a rule can't structurally reach — the
condition this feature was built for, which the labeled data hasn't
produced yet.
