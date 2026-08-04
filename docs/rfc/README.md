# RFC process

For architectural proposals — anything that would change a
[`STABILITY.md`](../../STABILITY.md) Stable-tier guarantee, the
[`MEMORY_GOVERNANCE.md`](../../MEMORY_GOVERNANCE.md) schema, or a
[`DESIGN_INVARIANTS.md`](../../DESIGN_INVARIANTS.md) principle. Not for
everything — that would be bureaucracy for its own sake, which
`DESIGN_INVARIANTS.md`'s own "single-maintainer governance" tradeoff
explicitly argues against building before there's a team to need it.

## When you need one

| Change | RFC? |
|---|---|
| A new CLI flag on an existing command | No — normal PR |
| A new evaluator plugin (Experimental/Community tier) | No — `orchestrate plugin new` + normal PR |
| Promoting a plugin to Core, or removing one | **Yes** — [`PLUGIN_GOVERNANCE.md`](../../PLUGIN_GOVERNANCE.md) |
| A breaking Engineering Memory schema change | **Yes** — [`MEMORY_GOVERNANCE.md`](../../MEMORY_GOVERNANCE.md) |
| Changing what a Stable-tier CLI command guarantees | **Yes** |
| A new memory-system capability from `ARCHITECTURE_EVOLUTION.md` whose trigger has fired | **Yes** — the trigger firing means "reconsider," not "auto-approve" |
| Fixing a bug, even a Stable-tier one, that restores documented behavior | No — that's a bug fix, not an architecture change |

## The template

Copy [`TEMPLATE.md`](./TEMPLATE.md). Every section is required — an RFC
missing "Rollback plan" or "Reconsideration trigger" isn't ready for
review, the same way a rejected Engineering Memory entry without
`reconsider_if` isn't accepted. This isn't a coincidence: an RFC and a
memory entry are the same kind of object at different points in time — a
decision with its evidence attached — and an accepted RFC should produce
an Engineering Memory entry recording the outcome, whichever way it goes.

## Process

1. Open the RFC as a PR adding `docs/rfc/NNNN-short-title.md` (numbered
   sequentially, like ADRs).
2. State: Problem, Alternatives, Measurements, Tradeoffs, Blast radius,
   Rollback plan, Success metrics, Reconsideration trigger.
3. Discussion happens on the PR. At single-maintainer scale, that's the
   entire process — no separate voting body exists to invent one for.
4. Accepted: merged, and — if it changed something documented in
   `DESIGN_INVARIANTS.md`, `STABILITY.md`, `MEMORY_GOVERNANCE.md`, or
   `PLUGIN_GOVERNANCE.md` — those documents are updated in the same PR,
   not left to drift out of sync. Also produces a Core Engineering Memory
   entry (`ARCHITECTURE_EVOLUTION.md`'s `5-orchestrate-kit` phase) if the
   RFC concerned `orchestrate_kit` itself.
5. Rejected: the PR is closed with the reason stated in the thread — and,
   the same way any other rejection in this project works, becomes a
   memory entry with a `reconsider_if`, so the next person proposing the
   same thing finds it via `orchestrate mentor` instead of re-deriving the
   rejection from scratch.

## Why this is thin on purpose

A heavier process (a voting quorum, a mandatory waiting period, a
separate approvers list) would be solving a coordination problem this
project doesn't have yet — see `DESIGN_INVARIANTS.md`'s accepted tradeoff
on single-maintainer governance. This process is designed to survive the
transition past that point without a rewrite: the Problem/Alternatives/
Measurements/Tradeoffs shape doesn't change when a second or third
maintainer needs to weigh in, only who's doing the weighing.
