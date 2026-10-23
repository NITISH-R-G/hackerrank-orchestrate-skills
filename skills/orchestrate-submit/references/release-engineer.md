---
name: orchestrate-release-engineer
description: Run the final release gate: fresh-clone simulation, artifact freshness, packaging hygiene, documentation accuracy. Use in the final hour. Catches the defects that make a working submission fail on someone else's machine.
---

# Orchestrate: Release Engineer

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Clone to an empty directory, install nothing, and follow only your own README. Every
deviation you have to make is a defect.**

## What this caught in a real build

**The clone had almost no source.** Locally everything worked; `pytest` was green;
the submission was "ready". The clone contained **2 files** under `code/` — essentially
nothing had been committed. `git status` had been reporting untracked files for hours.

**`pytest` aborted the entire suite.** A stale exploratory script named `test_*.py` at
the repo root executed API calls at import time during collection. 63 passing tests
reported as a **red, interrupted run** — and `pytest` is the first thing a reviewer
types.

**A benchmark was overwriting the submission artifact.** It invoked the CLI without an
output flag, three times per run, silently reverting a correct classification to a
degraded one.

**Documentation was off by 180×.** A dependency change had made the pipeline slower;
the README still claimed the old runtime. It also recommended a flag that disabled a
required capability.

## The gate, in order

Cheapest checks that catch the most catastrophic defects go first.

- [ ] `git status --porcelain` empty for tracked files
- [ ] Clone to a temp dir; run using **only** the README
- [ ] Bare `pytest` from the repo root is green
- [ ] Each test file passes **in isolation**
- [ ] Artifact regenerated to a temp path and hash-compared
- [ ] Package rebuilt **after** the last commit
- [ ] Package contents byte-match the working tree
- [ ] No caches, no secrets, no absolute paths, no archive-traversal entries
- [ ] Every number in the README verified today
- [ ] Run the full verification suite, then **diff every artifact** — anything that
      changed, a verifier wrote to it

## The order that matters

```
code change → regenerate artifact → rerun verification → rebuild package → commit
```

Rebuilding the package before the final commit ships the previous version.

## Failure modes

- **Trusting local success.** Your machine has state a grader's does not.
- **Verifying by reading.** Hash it.
- **Assuming docs are prose.** They are assertions a reviewer will test.
