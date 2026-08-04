# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/) for `orchestrate_kit`
(the `skills/` directory is not versioned independently — a skill addition
is not a breaking change to anything).

## [Unreleased]

### Added
- `orchestrate memory verify` — checks that the files AND the commit a
  memory entry cites still exist / are reachable in this repository's
  history. Reports coverage honestly (most entries correctly have neither,
  because they describe the historical Orchestrate submission's codebase,
  not `orchestrate_kit`'s own) rather than treating "nothing cited" as
  either pass or fail.
- `EngineeringMemory.centrality()` / `.referenced_by()` — how many other
  entries a given entry is depended-on or superseded-by, surfaced as
  `<-N` in `orchestrate memory list`. A cheap, honest substitute for
  "importance" that doesn't require guessing at a weighting scheme this
  corpus is too small to tune meaningfully — mined from a comparative
  review of TencentDB Agent Memory's "memory importance/scoring" concept,
  scaled down to something this project can actually justify. See
  [`docs/adr/0006`](./docs/adr/0006-agent-memory-comparative-review.md),
  updated with a full concept-by-concept mining pass (memory hierarchy,
  lifecycle, evolution, compression, importance, relationships/graph,
  provenance, retrieval planning, quality, scoring, consolidation, aging,
  conflict resolution, indexing, summarization, structured metadata) —
  most explicitly rejected with a stated reason, three adopted.
- 5 new Engineering Memory entries under phase `5-orchestrate-kit`,
  documenting real, already-fixed defects in `orchestrate_kit`'s *own*
  development this session (a packaging bug, a `RepoContext` robustness
  gap, a memory-search substring-matching bug, a benchmark-script stdout
  leak, and a static-analysis audit that shipped a wrong scope claim) —
  the first entries in this corpus to describe this repository's own code
  rather than the historical submission it was seeded from, and the first
  to carry accurate `files` references.
- Mentor reports now cap benchmarks shown per prior-art entry to 4
  (`MAX_BENCHMARKS_SHOWN`), with an honest "+N more" pointer to the full
  record via `orchestrate memory recall <key>`.
- [`docs/adr/0006-agent-memory-comparative-review.md`](./docs/adr/0006-agent-memory-comparative-review.md)
  — a full subsystem-by-subsystem comparison against
  [TencentDB Agent Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory)
  (MIT), reviewed as a candidate to replace this project's Engineering
  Memory. Conclusion: they solve different problems (a multi-tenant,
  DB-backed runtime memory service for live conversational agents, vs. a
  curated, human-authored decision log for one codebase's own history) —
  most of the storage/retrieval/access-control architecture was kept as
  correctly scoped to this project's actual size and deployment model, and
  two genuinely portable ideas (context-budget capping, relating memory
  records to real code) were adopted in original form. See
  [`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md) for what is and
  isn't attributed.

### Fixed
- `pyproject.toml` declared package-data as `../data/memory.json` — a path
  reaching outside the package directory, unsupported by setuptools. It
  worked locally only by accident (an editable install's directory layout
  happened to coincide with where the resulting wheel placed the file).
  Verified by building a real wheel and installing it into a clean venv with
  no local checkout present; the bundled Engineering Memory seed corpus was
  silently missing. Fixed by moving it to `orchestrate_kit/data/memory.json`
  — inside the package — and re-verified the same way.
- README's Quick Start led with `pip install -e .` followed immediately by
  a bare `orchestrate ...` command. On a stock (non-venv) install, pip's
  console-script directory is commonly not on `PATH`, so the second command
  in the README failed with `command not found`. Reproduced by literally
  following the README. Every example now leads with
  `python -m orchestrate_kit`, which works unconditionally.
- `LICENSE` and `README.md`'s License section contradicted each other:
  `LICENSE` claimed some skills were third-party content tracked in a
  `LICENSE-AND-ATTRIBUTION.md` file that never existed; the README said
  every skill was written from scratch. Reduced `LICENSE` to standard MIT
  text, which also fixed GitHub's license detector (previously reported
  "Other").
- `FAQ.md` linked to `ORCHESTRATE.md` four times — a file renamed to
  `README.md` in an earlier version, with the FAQ never updated. One of the
  four broken links backed an answer ("no runtime orchestration engine")
  that was also factually stale as of `orchestrate_kit`'s introduction.
- `RESEARCH.md` reported "21 skills"; actual count is 34.
- `RepoContext(root=...)` silently misbehaved when `root` was passed as a
  plain string instead of a `Path` — an easy, natural mistake, since Python
  doesn't enforce dataclass type hints. `detect()` then raised
  `AttributeError` (`str` has no `.rglob`), which `Evaluator.applicable()`
  catches and discards by design (a broken detector must not abort the
  whole run) — so a plugin just silently never applied, with no error
  anywhere. Found while building `examples/python-quality-plugin` and
  actually using the API rather than only reading it. Fixed with a
  `__post_init__` that coerces `root` to `Path`.
- `orchestrate_kit/bench.py`'s in-process memory measurement called a CLI
  handler directly, whose normal `print()` output leaked straight into
  `bench.py`'s own stdout — polluting `bench.py > BENCHMARKS.md` with a
  random command's raw output in the middle of a markdown table. Found by
  actually piping the output. Fixed by redirecting stdout during that call.

### Added
- `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `ROADMAP.md`.
- GitHub repository description and topics updated to reflect
  `orchestrate_kit` (previously described the v1 8-skill collection);
  GitHub Discussions enabled.
- README badges: CI status, license, Python version, zero-runtime-deps —
  each backed by a fact already true in the repo, not aspirational.
- Coverage measurement in CI (`pytest-cov`), reported honestly with no
  target attached. Current measured total: 72%.
- `examples/python-quality-plugin/` — a second, fully independent evaluator
  plugin (two AST-based Python static checks: bare `except:`, mutable
  default arguments), proving the plugin system generalizes beyond the
  first-party Orchestrate plugin. Run against `orchestrate_kit`'s own
  production code: 0 findings, measured, not asserted. 16 tests including
  false-positive guards (`except Exception:` must not fire; `x=None` must
  not fire) and a self-audit test that runs the plugin against this very
  repository.
- `.devcontainer/devcontainer.json` and `.vscode/{settings,launch}.json` —
  every launch config verified to run the exact command it claims to.
- `.github/workflows/release.yml` — on a version tag: re-runs the full test
  suite + selftest on the tagged commit, builds sdist + wheel, verifies with
  `twine check`, verifies the wheel actually contains the packaged seed
  data (regression check for the packaging bug above), verifies install
  from a clean venv with no repo context, attaches artifacts to a GitHub
  Release. Does **not** publish to PyPI — gated behind a `PYPI_API_TOKEN`
  secret that does not exist yet; skips cleanly rather than failing or
  pretending to publish. See `ROADMAP.md`.
- `BENCHMARKS.md` — measured wall-clock (mean/min/max/stdev over 5 cold
  subprocess runs) and peak Python memory for every CLI command,
  regenerable via `python -m orchestrate_kit.bench > BENCHMARKS.md`.

## [1.0.0] — 2026-08-02

Full rebuild from a documentation-and-skills collection into installable
software (`orchestrate_kit`), per the project's own standard: nothing states
a number it did not measure.

### Added
- **Engineering Memory** (`orchestrate memory`) — schema v2 with
  `Benchmark` records, `blast_radius`, `depends_on`, `phase`, and an
  enforced `reconsider_if` on every rejection. 40 entries seeded from a real
  build, 9 of them measured rejections.
- **Mentor** (`orchestrate mentor`) — accepts a proposal in English, returns
  classification, prior art, risk register, blast radius, evaluation plan,
  and a release recommendation. Refuses to predict gain with no prior art
  (`UNKNOWN`, not a guess).
- **Judge** (`orchestrate interview`) — adaptive interview simulator: 4
  personas, 4 difficulty levels, 40 questions across 12 topics,
  cross-examination, session memory, weakness detection. Deterministic and
  offline.
- **Evaluator** (`orchestrate evaluate | certify | release`) — black-box
  plugin-based repo auditor, migrated and extended from the earlier `aiev`
  tool.
- **`orchestrate selftest`** — negative control: builds a healthy fixture
  repo, injects 10 defect classes, requires each to be caught, requires 3
  benign cases to stay quiet.
- **`orchestrate plugin new`** — scaffolds a plugin and its negative control
  together; the generated audit starts red on purpose.
- **`orchestrate viz` / `orchestrate graph`** — 9 generated Mermaid diagrams,
  including a decision graph rendering rejected branches as first-class
  nodes.
- CI matrix (ubuntu/windows × Python 3.10/3.13), each test file also run in
  isolation.
- 53 tests, including negative controls on the negative controls (e.g. a
  test proving `selftest` itself goes red if the evaluator is blinded).

## [0.4.0] — v4, "audit tier"

- 13 new skills built from auditing a complete Orchestrate submission to
  destruction: 48 logged defects (F-1…F-48), 9 measured-and-rejected
  optimisations, 17 certification scripts, one completed AI-judge interview.
- `PLAYBOOK.md` (20 rules), `TIMELINE.md`, `JUDGE-PREP.md`,
  `RELEASE-CHECKLIST.md`.
- First version of the repo evaluator (`tools/aiev`, later migrated into
  `orchestrate_kit/evaluator`).

## [0.3.0] — v3

- Expanded 18 → 21 skills using *The Engineer's Notebook* and a first-hand
  #1-ranked participant's writeup as secondary evidence, clearly labeled as
  such — distinct from the primary-source tiers used elsewhere.

## [0.2.0] — v2

- Expanded to 18 skills using the official public starter repositories for
  the May and June 2026 events as primary evidence.

## [0.1.0] — Initial release

- 8 Orchestrate-focused Agent Skills grounded in HackerRank's published
  4-signal scoring methodology.

[Unreleased]: https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/compare/d87004d...HEAD
[1.0.0]: https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/compare/f3b87b3...d87004d
