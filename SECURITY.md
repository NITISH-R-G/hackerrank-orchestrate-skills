# Security Policy

## Supported versions

Only the latest commit on `master` is supported. There is no published PyPI
release yet (see [ROADMAP.md](./ROADMAP.md)), so there is no older version
line to backport fixes to.

## What's actually in scope

Be precise about what this software touches, because "security" means
different things for different kinds of tools:

- **`orchestrate_kit` runs entirely locally.** No network calls, no
  telemetry, no external services. `RepoContext.run()` explicitly clears
  known API-key environment variables before running a subprocess, so an
  audit cannot accidentally depend on (or leak into) live credentials.
- **The evaluator executes commands you configure** — a plugin's `audits()`
  can shell out (e.g. to run `python code/main.py`). Only run
  `orchestrate evaluate` / `orchestrate certify` / `orchestrate release`
  against a repository you trust, the same way you'd only run `make` or
  `pytest` against one. This is not sandboxed, and isn't intended to be —
  it's a developer tool, not a hosted service accepting untrusted input.
- **The judge and mentor accept free-text input** but never execute it, call
  a model, or reach the network. Worst case for malformed input is a wrong
  score or a crash, not code execution.
- **Skills in `skills/`** are Markdown files an external agent (Claude Code,
  Cursor, etc.) reads. This repo doesn't control what that agent does with
  them; review any skill's content the same way you'd review a shell
  snippet before running it.

## Reporting a vulnerability

If you find something that lets an untrusted input execute code, exfiltrate
data, or otherwise misbehave outside the "you're auditing a repo you trust"
model above:

1. **Do not open a public issue.**
2. Use GitHub's private vulnerability reporting: **Security → Report a
   vulnerability** on this repository, or contact the maintainer directly
   through their GitHub profile.
3. Include a reproduction: the exact command, the input, and what happened
   versus what should have happened.

Expect an acknowledgment within a few days. This is a single-maintainer
project without a formal SLA — see [SUPPORT.md](./SUPPORT.md) for what that
means in practice.

## Not a vulnerability

- A `Finding` with a wrong severity or a bad heuristic match is a bug, not a
  security issue — open a normal issue.
- `orchestrate evaluate` refusing to run, or an audit crashing, is by design
  reported as a finding (`SimpleAudit.run()` catches and reports rather than
  propagating) — that's the intended failure mode, not a vulnerability.
