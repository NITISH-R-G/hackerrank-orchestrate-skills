# Support

## Before you ask

Three things resolve most questions faster than waiting for a reply:

- `orchestrate --help` / `orchestrate <command> --help` — every command's
  full option list.
- [FAQ.md](./FAQ.md) — covers install issues, scope questions, and "does
  this guarantee a better score."
- `python -m orchestrate_kit selftest` — if something in the evaluator
  seems wrong, this tells you whether the tool itself is behaving as
  designed (10 known defects caught, 3 known-benign cases quiet).

## Where to go

| Need | Where |
|---|---|
| Something is broken | [Open an issue](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/issues/new) with the exact command and output |
| A skill or scoring claim is wrong or outdated | Issue tagged as a factual correction — see [CONTRIBUTING.md](./CONTRIBUTING.md#reporting-a-factual-error) |
| "How do I..." / general usage | [GitHub Discussions](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/discussions) |
| A security issue | **Not** a public issue — see [SECURITY.md](./SECURITY.md) |
| You want to contribute | [CONTRIBUTING.md](./CONTRIBUTING.md) |

## What to include in a bug report

The evaluator, mentor, and judge are all deterministic and offline, so most
bugs are reproducible from three things:

1. The exact command you ran.
2. What you expected versus what happened.
3. `python -m orchestrate_kit --help` output if the issue looks like a CLI
   parsing problem, or the relevant `Finding`/report block if it's an audit
   or mentor issue.

## Response expectations

This is a single-maintainer open source project, not a supported product —
there's no SLA. Issues with a clear repro get looked at fastest; "it doesn't
work" with no command or output attached will likely just get a request for
more detail.
