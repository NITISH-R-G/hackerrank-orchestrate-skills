# Roadmap

Ranked by expected impact, not by ease. Updated as items land — see
[CHANGELOG.md](./CHANGELOG.md) for what's already shipped.

No dates. This is a single-maintainer project; a roadmap with fake deadlines
is worse than one that's honest about not having them.

## Now

- [x] Fix the packaging bug that dropped the memory seed corpus from a real
      wheel build (shipped, see CHANGELOG `[Unreleased] > Fixed`)
- [x] Fix the README onboarding command that failed on a stock install
- [ ] **Publish to PyPI.** `orchestrate-kit` is the package name in
      `pyproject.toml` and is unclaimed as of this writing. Everything else
      in this list is more valuable once `pip install orchestrate-kit`
      actually works — cloning a repo is real friction that a roadmap item
      can just remove.
- [x] **Coverage measurement in CI**, reported honestly (a number with no
      target attached, not a claimed threshold that hasn't been earned).
      Current measured total: **72%** (`pytest --cov=orchestrate_kit`).
      The two real weak spots, worth closing before claiming any number as a
      quality signal: `evaluator/plugins/generic/__init__.py` at 16% (the
      generic audits are exercised end-to-end but not unit-tested per
      function) and `evaluator/reporting.py` at 11% (the render functions are
      checked for "doesn't crash" via the terminal path, not for correct
      output shape). `cli.py` at 41% is less concerning — most of the gap is
      argparse wiring exercised by actually running commands (which the CI
      steps below it do), not logic worth unit-testing in isolation.

## Next

- [ ] A CI check that fails the build if README's skill count or test count
      drifts from the real `ls skills | wc -l` / pytest count. This class of
      bug (a stale "21 skills" claim, a stale "48 tests" claim) has already
      happened twice; the fix is to stop trusting a human to keep two
      numbers in sync and make CI do it.
- [ ] A second real evaluator plugin beyond the Orchestrate one and the
      scaffold template — proof the plugin system generalizes in practice,
      not just in a generated stub. (`examples/python-quality-plugin` is a
      first step toward this; a plugin for a genuinely different domain,
      e.g. a RAG evaluation harness, would be the real test.)
- [ ] A terminal-recording GIF/asciicast of `orchestrate mentor` and
      `orchestrate interview` for the README header. Currently text-only,
      which is a real first-impression cost for a CLI tool. Not done yet
      because it needs to be an actual recording of actual output, not a
      mockup.
- [ ] GitHub repository social preview image.

## Later

- [ ] A hosted, read-only demo of `mentor`/`interview` (no install). Highest
      friction removal, highest implementation cost — needs a small backend,
      not just a static page, since both tools have state (session memory,
      Engineering Memory search).
- [ ] Submit to relevant Awesome-lists once PyPI publication and the demo
      GIF land — a submission without those is weaker than it needs to be.
- [ ] Expand `orchestrate_kit`'s judge question bank and mentor proposal
      taxonomy based on real usage — both are currently sized to what one
      build's worth of Engineering Memory could populate honestly, and
      should grow from real rejected proposals, not invented ones.

## Explicitly not planned

- **A formal GOVERNANCE.md.** For a single-maintainer project at this stage,
  a governance document describing a process that doesn't exist yet (no
  other maintainers, no voting, no formal escalation path) would be ceremony
  without substance. Revisit if/when there's a second regular maintainer —
  `CONTRIBUTING.md`'s existing rules (negative-control requirement,
  `reconsider_if` requirement) already cover the actual decision criteria
  that matter today.
- **Semantic-release automation.** The project is pre-1.x-in-practice (one
  tagged release candidate, no PyPI publish yet) — automating a release
  process before there's been a single manual release to learn from would
  be solving a problem that hasn't been felt yet.
- **A plugin marketplace / registry.** Premature for a project with one
  first-party plugin and one example plugin. The scaffold
  (`orchestrate plugin new`) is the right amount of infrastructure for the
  current number of plugin authors: zero to a handful.
