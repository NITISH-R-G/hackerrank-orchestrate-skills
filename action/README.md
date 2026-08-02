# `orchestrate evaluate` — GitHub Action

Runs the black-box evaluator against your repository on every push or PR,
uploads the report as a build artifact, comments the result on the PR
(updated in place on re-runs, not spammed), and fails the build on a
release blocker.

## Usage

```yaml
name: orchestrate

on:
  push:
  pull_request:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write   # only needed if comment-on-pr is true
    steps:
      - uses: actions/checkout@v4
      - uses: NITISH-R-G/hackerrank-orchestrate-skills/action@master
        with:
          path: "."
```

This exact syntax is what `.github/workflows/action-selftest.yml` in this
repository runs against itself, on every push — the [Actions
tab](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/actions/workflows/action-selftest.yml)
shows a real, current run using it, not a claim it works.

**A note on the ref.** `@master` tracks the branch, which is convenient but
means a breaking change to the action would affect you immediately. Once
this repo has a tagged release, pin to that instead (`@v1.0.0`) the way
you'd pin any other action — see [`../CHANGELOG.md`](../CHANGELOG.md) for
what's released.

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `path` | `.` | Repository path to evaluate, relative to the workspace |
| `fail-on-blocker` | `true` | Fail the build if any release blocker is found. Set `false` to only report |
| `comment-on-pr` | `true` | Post/update a PR comment with the result. No-op outside `pull_request` events |
| `python-version` | `3.12` | Python version the evaluator runs under |

## Outputs

| Output | Example |
|---|---|
| `score` | `100` |
| `verdict` | `READY`, `READY WITH RESERVATIONS`, `NOT READY`, `DO NOT SHIP` |
| `blockers` | `0` |
| `report-path` | `orchestrate-report.md` |

```yaml
- uses: NITISH-R-G/hackerrank-orchestrate-skills/action@master
  id: evaluate
  with:
    path: "."
- run: echo "Score was ${{ steps.evaluate.outputs.score }}"
```

## How it actually works (not terminal-scraping)

`orchestrate evaluate` prints human-readable text meant for a terminal.
Parsing that with grep inside a composite action's bash step would be
exactly the fragile regex-over-formatted-output pattern this project's own
audits exist to catch. [`run_evaluate.py`](./run_evaluate.py) instead calls
the same `Evaluator` class the CLI calls, gets back the real `Evaluation`
object, and writes GitHub Actions outputs directly from its structured
fields — `score`, `verdict`, and `blockers` are read off `Evaluation`
attributes, not scraped from a string.

## Why this installs from source, not PyPI

`orchestrate-kit` isn't published to PyPI yet (see
[`../ROADMAP.md`](../ROADMAP.md) and
[`../docs/PUBLISHING.md`](../docs/PUBLISHING.md)). The action installs
itself from `github.action_path` — the exact checkout of *this* action's
repo, at whatever ref you pinned in `uses:` — which has a real advantage
over a PyPI install even after publishing: the evaluator version is
guaranteed to match the action version you pinned, with zero drift.

## Verifying it yourself

Don't take the green checkmark on faith — the self-test workflow explicitly
checks that every output is non-empty and the report file was actually
written, the same negative-control habit this project applies to its own
evaluator (`orchestrate selftest`) applied to the action wrapping it.
