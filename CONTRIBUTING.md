# Contributing

This repository has two very different kinds of content, and the bar is
different for each.

## Contributing to `orchestrate_kit` (the software)

Standard engineering process: fork, branch, PR. Before opening one:

```bash
pip install -e ".[dev]"
python -m pytest -q          # unit tests
python -m orchestrate_kit selftest   # negative control
```

Rules enforced by the codebase itself, not just convention:

- **New audits need a negative control.** An audit that has never produced a
  finding cannot be trusted to produce one when it matters. Use
  `orchestrate plugin new <name> --detect <path>` to scaffold a plugin — it
  generates the audit *and* the test proving it can fail, and starts red on
  purpose.
- **New Engineering Memory entries with `status: rejected` require a
  `reconsider_if`.** `orchestrate memory add --status rejected` without one
  is refused by the CLI: a rejection with no reconsideration condition is a
  prejudice, not a decision. See `orchestrate_kit/memory/seed.py` for the
  shape of a real entry (problem, root cause, chosen, rejected, benchmarks,
  blast radius, reconsider_if).
- **New judge questions** go in `orchestrate_kit/judge/bank.py`. Each needs
  `probes` (what a strong answer must contain), a `trap` (the common weak
  answer), and `strong` (the *shape* of a good answer — never a script to
  memorise).
- **Every `Finding` needs literal evidence** — command output or a file
  excerpt, never a paraphrase. A finding without evidence is an opinion, and
  the reporter should say so, not present it as fact.

Good first issues: a new proposal class in `mentor/taxonomy.py`, a new
diagram in `viz/render.py`, a new generic (domain-independent) audit in
`evaluator/plugins/generic/`.

## Contributing a skill

1. Check it's not already covered — browse `skills/` or the README's category
   tables.
2. Open a PR adding `skills/<name>/SKILL.md`, following the frontmatter +
   evidence-tier structure of an existing skill.

**Orchestrate-specific skills carry a higher bar: every claim needs a
traceable source.**

1. Find the specific official source — a HackerRank blog post, the official
   starter repo, an organizer advice post — not a forum post repeating a
   rumor.
2. Quote it directly in the skill's evidence section, with a link.
3. If you're inferring rather than quoting, label it `[inference]` explicitly
   — see [SCORING-HEURISTIC.md](./SCORING-HEURISTIC.md) for the pattern.
4. Proposing a new challenge-specific skill for a new Orchestrate event?
   Link that event's official starter repo or challenge page.

PRs that dress up generic "AI engineering best practices" as
Orchestrate-specific insight, with no traceable HackerRank source, won't be
merged as an `orchestrate-*` skill. General engineering skills belong in
[skills-i-use](https://github.com/NITISH-R-G/skills-i-use) instead — this
repo's skill set stays scoped to Orchestrate.

Every skill and every line of `orchestrate_kit` in this repository is
original work, released under the [MIT license](./LICENSE) — see the
[README's License section](./README.md#license) for what that does and
doesn't cover (public HackerRank material is quoted with attribution, never
reproduced wholesale).

## Reporting a factual error

If something here misrepresents what HackerRank has actually published, or a
memory entry misstates a measurement, that's a priority fix — open an issue
with the correct source, or a PR with the correction. Accuracy is this
repo's entire value proposition; a wrong number left standing is worse than
an admitted gap.

## Code of conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md). Short version: be direct, be
kind, cite your sources.
