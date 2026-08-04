# Stability guarantees

What you can build against without your code breaking on an update, and
what you can't. See [`DESIGN_INVARIANTS.md`](./DESIGN_INVARIANTS.md) for
the philosophy this implements; this document is the concrete boundary.

## Tiers

| Tier | Meaning | Change policy |
|---|---|---|
| **Stable** | Breaking it requires a major version bump and a `CHANGELOG.md` entry under `### Removed`/`### Changed`, with a migration note | Additive changes only within a major version |
| **Experimental** | Working, tested, but the shape may still change | Breaking changes allowed, must be called out in `CHANGELOG.md` |
| **Internal** | Implementation detail | Changes freely, no notice required |

## Stable

- **CLI commands and exit codes** — `evaluate`/`certify`/`release`/
  `mentor`/`interview`/`memory`/`graph`/`viz`/`selftest`/`plugin` and their
  documented exit-code contract (`0` clean, `1` usage error, `2` blocker,
  `3` non-blocking findings on `certify`). A script piping `orchestrate`
  output today keeps working across minor/patch releases.
- **`MemoryEntry` schema fields** that exist today (`key`, `kind`, `title`,
  `problem`, `root_cause`, `chosen`, `rejected`, `evidence`, `benchmarks`,
  `blast_radius`, `impact`, `reconsider_if`, `commit`, `files`, `tags`,
  `status`, `supersedes`, `depends_on`, `phase`, `lesson`) — a field may be
  *added*, never removed or repurposed, within a major version. `version:
  2` is already stamped in the JSON store precisely so a future breaking
  schema change has somewhere to signal from.
- **`Finding` / `AuditResult` / `RepoContext` / `Plugin` / `Audit`** in
  `orchestrate_kit.evaluator.plugin_api` — the plugin contract. A
  third-party plugin written against this today should not need changes
  to keep working, short of a documented major-version migration.
- **The GitHub Action's inputs/outputs** (`path`, `fail-on-blocker`,
  `comment-on-pr`, `python-version` → `score`, `verdict`, `blockers`,
  `report-path`) — see [`action/README.md`](./action/README.md).

## Experimental

- **The Mentor's proposal-classification taxonomy**
  (`orchestrate_kit/mentor/taxonomy.py`) — classes and their risk registers
  will keep growing; a class's exact `key` string is not yet guaranteed
  stable across versions.
- **The Judge's question bank and scoring dimensions**
  (`orchestrate_kit/judge/bank.py`, `scoring.py`) — question keys, the
  5-dimension scoring model, and persona weights are all expected to be
  tuned as real usage accumulates.
- **`orchestrate memory verify`'s output format** — the command and its
  exit-code contract (0 clean, 1 something missing) are stable; the exact
  printed report layout is not yet.
- **`.devcontainer/`, `.vscode/`** — convenience, not contract.

## Internal (no guarantee, changes freely)

- Everything under `orchestrate_kit.cli` beyond the documented commands
  themselves (argument parsing internals, private `_helper` functions).
- `orchestrate_kit.viz.render`'s exact Mermaid output text (the diagrams
  it produces are guaranteed to exist and be valid Mermaid, not to be
  byte-stable across versions).
- `orchestrate_kit.bench` — a development tool, not a library surface.

## Versioning policy

[SemVer](https://semver.org/). `orchestrate_kit.__version__` and
`pyproject.toml`'s `version` are required to match — checked by
`test_versions_match`, not left to discipline. A **major** bump means a
Stable-tier guarantee changed; **minor** means an addition (a new field, a
new CLI subcommand, a new Experimental feature); **patch** means a fix
with no interface change at all.

## Deprecation policy

1. A deprecation is announced in `CHANGELOG.md` under `### Deprecated`,
   naming the replacement and the version it will be removed in.
2. It stays functional, with a printed warning where practical, for at
   least one full minor version cycle before removal.
3. Removal happens in a major version bump, documented in `CHANGELOG.md`
   under `### Removed`, with a migration note — not silently.

## Migration policy

A **major** version bump ships a `MIGRATING.md` (created the first time
one is needed — none exists yet, because there has been no breaking
change yet) naming every Stable-tier guarantee that changed and the exact
steps to update calling code. `docs/PUBLISHING.md`'s release checklist
requires this before a major-version tag, once that checklist itself is
extended to check for it — tracked in `ROADMAP.md`.

## Backward compatibility policy

Within a major version: a script that worked against version `X.Y.0`
keeps working against `X.Y.*` and `X.(Y+1).0` for every Stable-tier
guarantee above. Experimental and Internal tiers carry no such promise —
that's precisely the distinction the tiers exist to make explicit, instead
of leaving every surface implicitly "maybe stable, maybe not."
