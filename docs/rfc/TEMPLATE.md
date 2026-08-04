# RFC NNNN: Title

**Status:** Draft
**Author:**
**Date:**

## Problem

What's actually wrong, with evidence — not "this could be better" but the
specific, observed cost of not changing it. If you can't point to a
concrete instance (a bug, a benchmark, a repeated support question), the
RFC likely isn't ready to write yet.

## Alternatives considered

At least two, including "do nothing." For each: what it costs, what it
gains, why it was or wasn't chosen. A proposal with no rejected
alternative wasn't actually designed — see
[ADR-0001](../adr/0001-deterministic-rule-engine.md) for the shape this
should take.

## Measurements

Numbers, not impressions. If the change can't be measured before writing
it, say so explicitly and describe the measurement plan instead of
skipping the section.

## Tradeoffs

What gets worse, not just what gets better. Every real engineering
decision has a cost; naming it here is what separates this from marketing
copy for the proposal.

## Blast radius

What breaks if this is wrong. Which `STABILITY.md` tier does it touch?
Which existing tests would need to change? Which downstream consumers
(plugin authors, CI users of the GitHub Action) are affected?

## Rollback plan

How to undo this if it ships and turns out wrong. "We'll figure it out"
is not a rollback plan.

## Success metrics

The specific number or observation that would tell you, after shipping,
whether this worked. Defined *before* shipping, not retrofitted after.

## Reconsideration trigger

If rejected: the specific condition that would justify revisiting this —
required the same way `orchestrate memory add --status rejected` refuses
to save without a `reconsider_if`. "Never" is an acceptable answer if
genuinely true, but it must be stated, not implied by silence.
