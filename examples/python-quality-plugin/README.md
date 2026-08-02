# `python-quality` — a second, independent evaluator plugin

Proof the plugin system generalizes beyond the first-party Orchestrate
plugin: two AST-based static checks for a well-known, unrelated Python
bug class, registered exactly the way any third-party plugin would be.

## What it checks

| Audit | Catches | Doesn't flag (verified by test) |
|---|---|---|
| `bare-except` | `except:` with no type — silently swallows `KeyboardInterrupt`/`SystemExit` | `except Exception:`, `except (A, B):`, the pattern appearing inside a string/docstring |
| `mutable-default-args` | `def f(x=[])` / `def f(x={})` / `def f(x=list())` — the object is created once at def-time and shared across every call | `x=None` + construct inside the body, a call to a user factory function, a constructor call *with* arguments |

Both use `ast.parse`, not regex — the same reason
[`leakage.py`](../../orchestrate_kit/evaluator/plugins/orchestrate/leakage.py)
does: this project's own Engineering Memory records a false BLOCKER from a
regex audit that matched inside a docstring. A string literal is an
`ast.Constant` node, not a place a real `except` clause can hide.

## Run it against a real repository

```bash
cd hackerrank-orchestrate-skills
python -c "
import sys; sys.path.insert(0, 'examples/python-quality-plugin')
from pathlib import Path
from orchestrate_kit.evaluator import Evaluator, RepoContext, render_terminal
from python_quality import PythonQualityPlugin

ev = Evaluator(RepoContext(root=Path('.')))
ev.register(PythonQualityPlugin())
print(render_terminal(ev.run()))
"
```

Run against `orchestrate_kit`'s own production code, the result is
measured, not asserted:

```
READY   score 100/100   [python-quality]

   quality          ########## 100  (2 audits, 0 findings)
```

Zero bare excepts, zero mutable default arguments, in the actual shipped
codebase — not a claim, a run.

## Building this taught the evaluator something

Writing `RepoContext(root=".")` — a plain string instead of a `Path` — is an
easy, natural mistake, and `str` has no `.rglob()`. Before this plugin
existed, that mistake failed *silently*: `detect()` raised `AttributeError`,
`Evaluator.applicable()` catches and discards detector exceptions (a broken
detector must not abort the whole run), so the plugin just never applied,
with no error anywhere. Using the API for real is what surfaced it. Fixed in
`orchestrate_kit/evaluator/plugin_api.py` with a `__post_init__` that
coerces `root` to `Path` — the exact "silent failure that looks like a clean
result" class this project warns about elsewhere.

## What this example is *not*

It is not a general-purpose Python linter — `ruff`/`flake8`/`pylint` already
do that comprehensively, and reimplementing them would be pointless. It
exists to demonstrate the plugin contract (`detect()` on shape, `audits()`
returning `SimpleAudit`s, findings that never crash the run) on a domain
that has nothing to do with HackerRank Orchestrate.
