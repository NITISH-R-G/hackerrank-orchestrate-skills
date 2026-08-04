# Plugin governance

`orchestrate_kit`'s evaluator was built plugin-first from
[ADR-0005](./docs/adr/0005-plugin-architecture.md) — the core knows
nothing about any specific domain. This document defines the lifecycle a
plugin moves through and the criteria for each stage, so "is this plugin
trustworthy" has an answer that doesn't depend on reading its source.

## Stages

| Stage | Meaning | Where it lives |
|---|---|---|
| **Experimental** | Scaffolded, runs, has a negative control — nothing more claimed | Anywhere: a fork, `examples/`, a separate repo |
| **Community** | Adopted by real users outside the maintainer, negative control verified by someone other than its author | A separate, linked repository |
| **Maintained** | A named maintainer responds to issues; passes the full plugin checklist below | Linked from `README.md`'s ecosystem section |
| **Core** | Ships inside `orchestrate_kit/evaluator/plugins/` | This repository |
| **Deprecated** | Superseded or unmaintained; still works, says so | Wherever it already lived, with a warning |
| **Archived** | Removed from active distribution | Git history only |

Today, exactly two plugins exist: `OrchestratePlugin` (**Core** — ships in
this repo, detects by dataset shape) and
[`examples/python-quality-plugin`](./examples/python-quality-plugin)
(**Experimental** — proves the contract generalizes, not yet adopted by
anyone else). Nothing is Community, Maintained, Deprecated, or Archived
yet. This document defines the path for when that changes, not a claim
that it already has.

## The plugin checklist (Experimental → everything above it)

Every plugin, at every stage above Experimental, must satisfy all of:

1. `detect()` keys on shape, not on a repository name (DESIGN_INVARIANTS.md).
2. Every `audits()` entry has a **negative control** — a test proving it
   can produce a finding on deliberately broken input, not only that it
   stays quiet on healthy input. `orchestrate plugin new` scaffolds this
   automatically; a hand-written plugin must add it manually.
3. No audit mutates the repository it's auditing (`F-audit-mutates`).
4. Every `Finding` carries literal evidence — command output or a file
   excerpt — never a paraphrase.
5. An audit that cannot run sets `res.skipped` with a reason. It never
   silently returns `passed=True` because it couldn't look.

A plugin failing any of these is Experimental at best, regardless of how
long it's existed or how many people use it.

## Promotion criteria

- **Experimental → Community**: the plugin checklist passes, verified by
  someone other than the author (a second pair of eyes on the negative
  control specifically — the exact class of bug this project's own audits
  have shipped and caught before, `F-leakage-false-blocker` chief among
  them).
- **Community → Maintained**: a named person or team commits to
  responding to issues; the plugin has been in real use (not just
  written) for at least one release cycle with no unresolved false
  positive or false negative reported against it.
- **Maintained → Core**: the plugin is either (a) generic enough to apply
  to *any* repository (matching the Generic plugin's bar), or (b) so
  central to this project's own stated mission (HackerRank Orchestrate
  submissions) that shipping it separately would fragment the primary
  use case. Promotion to Core requires an RFC (see
  [`docs/rfc/`](./docs/rfc/)) — it's the one promotion step that changes
  what ships inside this repository's own releases, so it gets the same
  process any other architectural change does.

## Removal criteria

- **Maintained → Deprecated**: the named maintainer stops responding for
  one full release cycle, or the plugin's checks are superseded by a
  Core capability that does the same job with a negative control this
  project can verify directly.
- **Deprecated → Archived**: no adoption reported for two release cycles
  after deprecation, or a security/correctness issue is found with no fix
  forthcoming.
- Removal from Core specifically requires the same RFC process promotion
  to Core does — a Core plugin is part of the Stable surface
  (`STABILITY.md`), and removing it is a breaking change under this
  project's versioning policy.

## Compatibility guarantees by stage

| Stage | Guarantee |
|---|---|
| Experimental | None. May break, move, or disappear without notice. |
| Community | The plugin author's own guarantee, not this project's — read their repo. |
| Maintained | Tracked against `orchestrate_kit`'s `Plugin`/`Audit` protocol version; a breaking protocol change is announced with enough lead time to update. |
| Core | Full `STABILITY.md` Stable-tier guarantee — a Core plugin's `detect()` behavior and audit names don't change without a major version bump. |

## Writing one

`orchestrate plugin new <name> --detect <path>` scaffolds a plugin whose
generated audit fails on purpose, with the negative control and the
false-positive guard both pre-written as tests — see
[`orchestrate_kit/scaffold.py`](./orchestrate_kit/scaffold.py) and
[`examples/python-quality-plugin/README.md`](./examples/python-quality-plugin/README.md)
for a complete, real example built the same way.
