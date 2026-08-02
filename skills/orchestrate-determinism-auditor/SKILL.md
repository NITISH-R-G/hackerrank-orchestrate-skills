---
name: orchestrate-determinism-auditor
description: Prove output is reproducible, and state precisely where that guarantee stops. Use before submission and whenever output changes between identical runs. Unqualified determinism claims are almost always false.
---

# Orchestrate: Determinism Auditor

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Same inputs, different processes, different hash seeds — one hash. And state exactly
where the guarantee ends.**

## Why processes and seeds, not just repeated calls

Python randomises string hashing per process. Set and dict iteration order can differ
**between runs** while looking perfectly stable **within** one. Two calls in the same
interpreter prove almost nothing.

```bash
for seed in 0 1 42 12345 random; do
  PYTHONHASHSEED=$seed python code/main.py --out /tmp/r_$seed.csv
done
sha256sum /tmp/r_*.csv    # expect ONE distinct hash
```

## What this caught in a real build

A determinism test called the pipeline twice and asserted the results matched. With an
API key present it made **two live network calls** and asserted a hosted speech model
is bit-stable. It is not — it failed on one row.

The test was not measuring the system's determinism. It was measuring someone else's
uptime. Fixed with an autouse fixture clearing every credential; suite time dropped
**47s → 4s** because a dozen other tests had been quietly making live calls too.

## State the boundary

Unqualified guarantees are false. Compare:

> ❌ "The system is deterministic."

> ✅ "Offline it is byte-identical across 5 processes and 5 hash seeds. With the hosted
> speech provider it is not, because that model is not bit-stable — I know the exact
> row where it varied. The submitted artifact is generated once, so this does not
> affect it."

The second survives cross-examination. The first invites one counterexample.

## The checklist

- [ ] Multiple processes, multiple `PYTHONHASHSEED` values → one hash
- [ ] Static scan for `random`, `uuid`, `time`, `hash()`, `glob`, `listdir` on the
      output path; adjudicated exceptions written **into the scanner**, not remembered
- [ ] No set or dict iteration reaching an output field
- [ ] Sorts use an explicit key and rely on stability, not luck
- [ ] Tests hermetic — credentials cleared, so results do not depend on your machine
- [ ] The boundary written down in the README

## Failure modes

- **Faking it.** If a hosted call makes you non-deterministic, say so. Do not stub it
  and claim determinism.
- **Testing within one process.** Misses hash-seed effects entirely.
