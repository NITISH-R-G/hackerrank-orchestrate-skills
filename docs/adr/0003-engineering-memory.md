# ADR-0003: Engineering Memory as a first-class artifact

**Status:** Accepted
**Memory:** the memory system's own seed corpus, `orchestrate_kit/memory/seed.py`

## Context

`git log` records *what changed*. It does not record *what was
considered and rejected*, *why*, *what was measured*, or *under what
condition the rejection should be revisited*. That information normally
lives in a Slack thread, a closed PR discussion, or one engineer's head —
which means the same rejected idea gets re-proposed, re-built, and
re-measured by someone who didn't know it had already lost.

## Decision

A structured, versioned JSON store (`orchestrate_kit/memory/store.py`) of
`MemoryEntry` records — `finding`s (defects found and fixed) and
`decision`s (choices made, including choices to reject) — each carrying:
`problem`, `root_cause`, `chosen`, `rejected` (the alternatives), measured
`benchmarks`, `blast_radius`, and — for any rejection — a mandatory
`reconsider_if`.

## Why `reconsider_if` is enforced, not just conventional

`orchestrate memory add --status rejected` **refuses to save** without one.
A rejection with no stated reconsideration condition is a prejudice, not an
engineering decision — it tells the next person "no" without telling them
what would change the answer. Making this a refusal instead of a
style-guide line means it can't be skipped under deadline pressure.

## Consequences

- **Positive:** `orchestrate mentor "<proposal>"` can search this store and
  block a re-proposal of something already measured and rejected — see
  ADR-0002's mention of the `llm-decision` taxonomy class for a concrete
  example of the mentor using this.
- **Positive:** `orchestrate graph` renders rejected branches as
  first-class nodes beside the chosen path — a decision graph, not a
  commit log, showing what was *considered*.
- **Negative:** the store only knows what was explicitly recorded. It is
  not a substitute for actually reading the code, and a search hit is
  prior art to weigh, not an automatic veto — see ADR-0002 and
  `orchestrate_kit/mentor/engine.py`'s deliberately narrow blocking logic
  (an *adjacent* rejection is shown, not enforced).

## Alternatives considered (and rejected, with the reason)

| Alternative | Rejected because |
|---|---|
| Rely on git commit messages | Squashed history is common and loses the "what was tried and rejected" information entirely — this repository's own history is a single-commit example |
| A markdown "lessons learned" doc | Not queryable, not diffable in a structured way, and nothing enforces that a rejection states its own reconsideration condition |
| A wiki / external tracker | Lives outside the repo, drifts out of sync with the code it describes, and isn't available offline |

## Reconsider if

The store grows large enough that keyword search (`orchestrate memory
recall`) stops surfacing genuinely relevant prior art — at that point a
smarter ranking than the current term-overlap scorer would be worth
measuring against it, the same way any other change here would be.
