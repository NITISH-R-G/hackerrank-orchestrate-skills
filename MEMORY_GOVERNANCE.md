# Engineering Memory governance

Treats the `memory.json` store like a production database, because at
scale that's what it becomes: a shared source of truth many contributors
read and few should write carelessly to. This document is the operational
policy; [ADR-0003](./docs/adr/0003-engineering-memory.md) is why it exists
at all, and [`ARCHITECTURE_EVOLUTION.md`](./ARCHITECTURE_EVOLUTION.md) is
when each policy below activates.

## Schema versioning

The store is stamped `"version": 2` (`orchestrate_kit/memory/store.py`).
A schema change that only *adds* an optional field is not a version bump
— every field added since v2 (`files`, `commit`) landed without one,
because old JSON without them still loads correctly (`field(default_factory
=list)` / `= ""` defaults). A version bump is required only when a field's
*meaning* changes or a required field is added — neither has happened yet.

## Migration

No migration tooling exists yet, because no breaking schema change has
happened yet. When one does: a `orchestrate_kit/memory/migrations/`
module, one file per version transition, run via a new `orchestrate
memory migrate` command that's idempotent (safe to run twice) and dry-run
by default (`--apply` required to actually write). This is a design
commitment for when it's needed, not code that exists today —
implementing a migration framework with nothing to migrate would be
exactly the kind of premature infrastructure `ARCHITECTURE_EVOLUTION.md`
argues against elsewhere.

## Validation

Enforced today, in code:
- A rejection (`status: "rejected"`) without `reconsider_if` is refused at
  write time (`orchestrate memory add`).
- `test_keys_are_unique` and `test_depends_on_targets_exist` run in CI on
  every push — no duplicate keys, no dangling graph edges.
- `orchestrate memory verify` checks `files`/`commit` provenance against
  the actual repository, on demand.

Not yet enforced, tracked in `ARCHITECTURE_EVOLUTION.md` §3: evidence/
benchmarks required on *every* entry, not just rejections. Trigger: 150
entries or a second regular contributor.

## Required vs. optional fields

| Required | Optional |
|---|---|
| `key`, `title` | everything else |

Deliberately minimal at the schema level — `key` because it's the
identity, `title` because an untitled entry is useless in `memory list`.
Everything else is optional at the *schema* level even though specific
policies (rejections need `reconsider_if`) require more in specific
cases. This keeps the schema permissive while keeping the actual quality
bar enforced by policy, which is easier to evolve than a schema
constraint would be.

## Breaking changes

A breaking change to the schema (removing a field, changing what one
means) requires: an RFC (`docs/rfc/`), a version bump in the stamped
JSON, a migration path (see above), and a `CHANGELOG.md` entry under
`### Changed` naming exactly what moved. None has happened since v2.

## Retention

Nothing is deleted. A superseded decision keeps its entry, linked via
`supersedes` — the point of Engineering Memory is exactly this history;
deleting a superseded entry would erase the "why did we change our mind"
trail that's the whole value proposition. A truly wrong entry (fabricated,
not merely outdated) is corrected in place and the correction itself
becomes an entry — `CONTRIBUTING.md`'s "reporting a factual error" already
covers this.

## Review process

Today: the sole maintainer reviews every entry before merge — the same
review that touches any other file in this repository, no separate memory-
specific process. At the trigger defined in `ARCHITECTURE_EVOLUTION.md`
§3 (150 entries or second contributor), this becomes a real question a
CODEOWNERS-style rule can answer, not before.

## Quality gates

Currently: `reconsider_if` on rejections (enforced), unique keys
(enforced, CI), valid `depends_on` edges (enforced, CI), files/commit
provenance verifiable on demand (`orchestrate memory verify`, not yet
wired into CI as a gate — see below).

**Gap found while writing this document:** `orchestrate memory verify`
exists and works but isn't run in CI, so a future entry citing a file or
commit that gets deleted wouldn't be caught automatically. Added to CI as
part of landing this document rather than left as a known-but-silent gap
— see the `memory verify` step in `.github/workflows/ci.yml`.

## Duplicate handling

No automated detection exists yet — see `ARCHITECTURE_EVOLUTION.md` §4.
Manually: `orchestrate memory search "<topic>"` before writing a new entry
is the current, sole safeguard, and it's a convention, not an enforced
step.

## Conflict handling

No automated detection exists yet — see `ARCHITECTURE_EVOLUTION.md` §6.
Manually: single-reviewer review is today's mechanism, which is a real,
working control at current scale and a documented risk past it.

## Provenance policy

An entry describing *this repository's own code* should cite the files it
touches (`files=`) and the commit that made the change true (`commit=`),
verifiable via `orchestrate memory verify`. An entry describing a
*different* codebase (the historical Orchestrate submission this corpus
was originally seeded from) correctly has neither — `verify_files()`/
`verify_commits()` both report that split honestly rather than treating
"no citation" as a failure. Fabricating a plausible-looking file or commit
reference to satisfy this policy is worse than leaving the fields empty —
`verify` exists specifically so a false citation is caught, not laundered.
