# Design Invariants

The permanent engineering philosophy of this repository. Not a style guide
— a set of things that **do not change** as the project grows, because
changing them would break a promise made to someone relying on this
project, or would undo the reason it's trustworthy in the first place.

If a proposal (see [`docs/rfc/`](./docs/rfc/)) would violate one of these,
that's not a detail to negotiate — the invariant wins, or the invariant
itself needs an RFC of its own, explicitly, with the blast radius of
breaking a promise already made.

## What must never change

1. **Nothing states a number it did not measure.** A `Finding` without
   evidence is reported as an opinion, never presented as fact. A `Mentor`
   with no prior art says `UNKNOWN`, never estimates. This is the single
   rule everything else in this document exists to protect.
2. **A rejection without a `reconsider_if` is refused, not merely
   discouraged.** `orchestrate memory add --status rejected` errors out
   without one. Enforced in code
   (`orchestrate_kit/cli.py::cmd_memory`), not just written down.
3. **An audit is not trusted until it has a negative control.** Something
   it must catch, proven by a test that breaks the target on purpose. See
   [`docs/adr/0004`](./docs/adr/0004-negative-controls.md).
4. **The core package (`orchestrate_kit` with no extras) has zero runtime
   dependencies.** It must run on a plane, in a locked-down CI container,
   with no network and no API key. Optional capability (e.g. a future
   vector-search backend, per
   [`ARCHITECTURE_EVOLUTION.md`](./ARCHITECTURE_EVOLUTION.md)) is an
   install extra, never a default.
5. **The Engineering Memory JSON store is git-diffable.** No mechanism may
   mutate `memory.json` as a side effect of a read (a `search`, a
   `recall`, a `mentor` query). Every write is a deliberate, reviewed
   action. This is why usage-count tracking is permanently rejected — see
   `ARCHITECTURE_EVOLUTION.md` §5.
6. **`detect()` keys on shape, never on a repository name.** A plugin that
   only works for one specific repo isn't a plugin, it's a script with
   extra ceremony. See
   [`docs/adr/0005`](./docs/adr/0005-plugin-architecture.md).
7. **An audit must never mutate what it audits.** Recorded the hard way —
   `F-audit-mutates` in Engineering Memory — and now a standing rule, not
   just a fixed bug.

## What is part of the public contract

See [`STABILITY.md`](./STABILITY.md) for the full breakdown of stable vs.
experimental vs. internal. The short version: the `orchestrate` CLI's exit
codes, the `MemoryEntry`/`Finding`/`AuditResult` schemas, and the `Plugin`
protocol are contracts other people's code can depend on. Everything under
`orchestrate_kit._*` or explicitly marked internal is not.

## Principles that override optimization

- **Correctness and honesty over performance.** `evaluate .`'s fresh-clone
  audit costs real seconds because it does a real `git clone` — that's the
  right trade; a faster audit that skips the check isn't actually cheaper,
  it's wrong.
- **A false negative in an audit is worse than a slow one.** Speed is a
  roadmap item; a clean result from a broken harness is the standing
  nightmare this whole project's audit philosophy exists to prevent
  (`F-ablation-harness`, `F-prober-artifacts`, `F-leakage-false-blocker`
  are all this exact failure, independently rediscovered three times).
- **A documented boundary beats an unqualified guarantee.** "Offline,
  deterministic; with the hosted provider enabled, not, and here's the
  row where it varied" is the shape every guarantee in this project should
  take.

## Tradeoffs intentionally accepted

- **Term-overlap search instead of BM25/vector retrieval**, at current
  corpus size — not because vector search is worse in general, but because
  this project's own measurement (`D-dense-retrieval`) tested a comparable
  small corpus and lexical won. See `ARCHITECTURE_EVOLUTION.md` §7 for
  exactly when this gets re-measured, and why the old number doesn't
  transfer indefinitely.
- **No access control**, because there is no second party yet to protect
  data from. Accepted explicitly, not by omission — see
  `ARCHITECTURE_EVOLUTION.md` §2.
- **Single-maintainer governance** instead of a formal multi-party process.
  Revisit at the second regular maintainer, not before — process built for
  a team that doesn't exist yet is ceremony, not governance.
- **A markdown-frontmatter skill format**, not a richer schema, because the
  Agent Skills standard this project targets is external and the whole
  point of a skill is that any compliant agent can read it without
  `orchestrate_kit` installed at all.

## What counts as a bug vs. accepted debt

**A bug:** any claim in documentation that the implementation doesn't
back up; any audit that can't be proven to fail (no negative control);
any silently-mutating read path; any exception swallowed without a
finding or a log line explaining why.

**Accepted debt, tracked not hidden:** items in
[`ROADMAP.md`](./ROADMAP.md) and `ARCHITECTURE_EVOLUTION.md` with a
stated trigger that hasn't fired yet. The difference between debt and a
bug is whether the gap is *written down with a condition for closing it*
— an undocumented gap is a bug regardless of how small it is.

## Assumptions this project makes, stated so they can be checked

- One maintainer, reviewing every change, for the foreseeable near term.
- The Engineering Memory corpus fits in a human's working memory (roughly
  hundreds, not tens of thousands, of entries) for the foreseeable near
  term.
- Consumers run `orchestrate_kit` as a CLI or library inside their own
  process — not as a hosted, multi-tenant service. If that assumption
  breaks, most of the invariants above still hold; the deployment and
  access-control model around them does not, and gets its own ADR when it
  happens (`ARCHITECTURE_EVOLUTION.md` Stage 4).

## Enforcement map

Every invariant above is enforced somewhere, not only stated. A principle
with no enforcement mechanism is a hope, not an invariant.

| Invariant | Enforced by |
|---|---|
| Findings need evidence | `Finding` dataclass requires `evidence`; `Confidence.UNKNOWN` exists precisely so a tool never has to guess |
| `reconsider_if` required on rejection | `orchestrate_kit/cli.py::cmd_memory` refuses to save without one |
| Audits need a negative control | `orchestrate selftest` (10 injected defects, 3 benign controls); `orchestrate plugin new` scaffolds a template that starts red |
| Zero runtime dependencies (core) | `pyproject.toml`'s `dependencies = []`, checked by the fact that CI runs the full suite with no extras installed |
| No silent mutation on read | `test_scaffolded_audit_skips_rather_than_passing_blind` and the whole class of `verify_files`/`verify_commits` tests — read paths return reports, never write |
| `detect()` by shape | `test_does_not_detect_a_non_python_repo` (example plugin), the Orchestrate plugin's own shape-based `detect()` |
| Audits don't mutate targets | `F-audit-mutates` is now a named finding in Engineering Memory that `orchestrate mentor` will surface if anyone proposes something shaped like it again |
| Version consistency (`pyproject.toml` vs `__init__.py`) | See `test_versions_match` (added alongside this document — previously manual, now checked) |

The last row is the one gap this document's own writing surfaced —
version numbers were consistent by discipline, not by a check. Fixed as
part of landing this file rather than left as a documented-but-unenforced
claim.
