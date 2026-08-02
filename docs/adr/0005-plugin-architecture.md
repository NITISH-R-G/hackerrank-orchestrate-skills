# ADR-0005: Black-box-first plugin architecture

**Status:** Accepted
**Memory:** `orchestrate_kit/evaluator/plugin_api.py` module docstring

## Context

The evaluator needs to check two very different kinds of things about a
repository: portable properties any repo has (git hygiene, secrets, a
fresh clone actually running, determinism, test isolation) and
domain-specific properties (for Orchestrate: spec conformance, evidence
quality, label leakage). Coupling those together in one module means the
"generic" checks can never ship or be reused without dragging in
Orchestrate-specific assumptions, and a new domain means editing the core.

## Decision

`orchestrate_kit.evaluator.plugin_api` defines a `Plugin` protocol
(`detect(ctx) -> bool`, `audits() -> Iterable[Audit]`) and an `Audit`
protocol (`run(ctx) -> AuditResult`) that the core `Evaluator` depends on
and nothing else. A `RepoContext` is the *entire* interface an audit is
allowed to assume about the target: run a command, read a file, glob for
paths. An audit that needs to import the target's own code must declare
`requires_import = True` explicitly, so a repo that doesn't expose
importable internals degrades to the portable checks instead of crashing.

`detect()` keys on **shape**, never on a repository name — the Orchestrate
plugin checks for `dataset/messages.csv` + `problem_statement.md`, so it
applies to any future Orchestrate season (or any fork) with that shape,
not just this specific repository.

## Consequences

- **Positive:** `examples/python-quality-plugin/` — a plugin for an
  entirely unrelated domain (generic Python static analysis) — registers
  against the exact same `Evaluator` with zero core changes, which is the
  actual proof this architecture generalizes, not just a claim about it.
- **Positive:** `orchestrate plugin new` can scaffold a working plugin
  because the contract is small enough to generate correctly (see
  ADR-0004 for what the scaffold also enforces).
- **Negative:** black-box-only means an audit that genuinely needs deep
  access to a target's internals (AST of *the target's* code, not the
  audit's own) has to opt into `requires_import`, which is a narrower,
  more fragile contract than the black-box default — a deliberate
  tradeoff toward portability over audit power by default.

## Alternatives considered (and rejected, with the reason)

| Alternative | Rejected because |
|---|---|
| One monolithic `Evaluator` with all checks inline | Every new domain requires editing shared code; a change for Orchestrate risks breaking the generic checks it has no business touching |
| Plugins that import and directly call the target's internals by default | Couples the evaluator to the target's dependency versions and import graph; a target with a broken import (a very common thing to be auditing FOR) would crash the audit meant to catch it |

## Reconsider if

A plugin author repeatedly needs something the black-box `RepoContext`
genuinely cannot express (not "importing is more convenient," but "this
check is structurally impossible without it") — at which point the
contract itself, not just individual audits, would need to grow.
