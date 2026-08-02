---
name: Bug report
about: Something in orchestrate_kit (CLI, evaluator, mentor, judge, memory) is broken
title: "[bug] "
labels: bug
---

**Command that failed:**
```
$ orchestrate ...
```

**Expected:**

**Actual (paste the real output, not a paraphrase):**

**`orchestrate_kit` version** (`pip show orchestrate-kit`, or the commit SHA
if running from a clone):

**OS / Python version:**

---
Most bugs here are reproducible offline — the evaluator, mentor, and judge
are all deterministic and make no network calls — so a command + its real
output is usually enough. See [SUPPORT.md](../../SUPPORT.md) for what else
helps.
