"""python-quality: a SECOND, independent evaluator plugin.

Everything in `orchestrate_kit/evaluator/plugins/orchestrate/` is scoped to
one domain (HackerRank Orchestrate submissions). The scaffold
(`orchestrate plugin new`) proves a plugin CAN be generated. Neither proves
the plugin system generalizes to a genuinely different, unrelated domain --
this file is that proof: two real Python-specific static-analysis audits,
not derived from the Orchestrate plugin at all, registered exactly the same
way.

Both audits use `ast`, not regex, for the same reason `leakage.py` does:
this project's own Engineering Memory records a false BLOCKER from a
regex-based audit that matched inside a docstring. AST parsing sidesteps
that whole class of bug by construction -- a string literal is a `Constant`
node, not a place a real `except` clause or default argument can hide.

    from python_quality import PythonQualityPlugin
    evaluator.register(PythonQualityPlugin())
"""

from __future__ import annotations

import ast
from pathlib import Path

from orchestrate_kit.evaluator.plugin_api import (
    AuditResult,
    Confidence,
    Finding,
    RepoContext,
    Severity,
    SimpleAudit,
)

_SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "venv",
              "node_modules", ".pytest_cache", "site-packages"}


def _python_files(ctx: RepoContext) -> list[Path]:
    out = []
    for p in ctx.root.rglob("*.py"):
        if _SKIP_DIRS & set(p.relative_to(ctx.root).parts):
            continue
        out.append(p)
    return sorted(out)


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"),
                         filename=str(path))
    except SyntaxError:
        return None


# --------------------------------------------------------------------------
def audit_bare_except(ctx: RepoContext) -> AuditResult:
    """A bare `except:` catches EVERYTHING -- including KeyboardInterrupt and
    SystemExit, which means Ctrl-C can be silently swallowed. `except
    Exception:` is almost always what was meant; it is one keyword away and
    behaves completely differently.

    `except Exception:` and `except (ValueError, TypeError):` are both
    correctly IGNORED -- this audit fires only on the truly bare form.
    """
    res = AuditResult("bare-except", "quality", True)
    files = _python_files(ctx)
    if not files:
        res.skipped = "no .py files found"
        return res

    offenders: list[str] = []
    for path in files:
        tree = _parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                rel = path.relative_to(ctx.root)
                offenders.append(f"{rel}:{node.lineno}")

    res.metrics = {"files_scanned": len(files), "bare_excepts": len(offenders)}
    if offenders:
        res.passed = False
        res.findings.append(Finding(
            title=f"bare 'except:' clause(s): {len(offenders)}",
            severity=Severity.MEDIUM,
            confidence=Confidence.OBSERVED,
            evidence="; ".join(offenders[:8]),
            detail="A bare except also catches KeyboardInterrupt and "
                   "SystemExit -- Ctrl-C can vanish silently inside one.",
            remediation="Catch the specific exception type, or "
                        "`except Exception:` if genuinely any application "
                        "error should be handled here.",
        ))
    return res


# --------------------------------------------------------------------------
_MUTABLE_TYPES = (ast.List, ast.Dict, ast.Set)


def audit_mutable_default_args(ctx: RepoContext) -> AuditResult:
    """`def f(items=[]):` creates the list ONCE, at function-definition time --
    every call that doesn't pass `items` shares and mutates the SAME list.
    This is arguably Python's most-recreated beginner bug and has bitten
    experienced engineers too; it survives code review because it looks
    completely reasonable.

    A literal `[]`/`{}` and a no-arg call to the builtins `list()`/`dict()`/
    `set()` are the SAME bug -- both execute once, at def-time, producing one
    object shared across every call that omits the argument. An earlier draft
    of this audit treated `list()` as a safe form; it isn't, and a test
    proving that (`test_mutable_dict_and_set_defaults_are_caught`) is what
    caught the gap. A call to anything else -- a user factory function, a
    class constructor with arguments -- is out of scope: this audit can't
    know statically whether it returns a fresh object each time, and
    guessing would trade a real bug class for false positives on legitimate
    code. `field(default_factory=list)`-style dataclass patterns are
    unaffected either way, since they aren't a plain function default.
    """
    res = AuditResult("mutable-default-args", "quality", True)
    files = _python_files(ctx)
    if not files:
        res.skipped = "no .py files found"
        return res

    empty_ctor_calls = {"list", "dict", "set"}

    def is_mutable_default(node: ast.expr) -> bool:
        if isinstance(node, _MUTABLE_TYPES):
            return True
        return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in empty_ctor_calls
                and not node.args and not node.keywords)

    offenders: list[str] = []
    for path in files:
        tree = _parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            defaults = list(node.args.defaults) + list(node.args.kw_defaults)
            for d in defaults:
                if d is not None and is_mutable_default(d):
                    rel = path.relative_to(ctx.root)
                    offenders.append(f"{rel}:{node.lineno}:{node.name}")

    res.metrics = {"files_scanned": len(files),
                   "mutable_defaults": len(offenders)}
    if offenders:
        res.passed = False
        res.findings.append(Finding(
            title=f"mutable default argument(s): {len(offenders)}",
            severity=Severity.HIGH,
            confidence=Confidence.OBSERVED,
            evidence="; ".join(offenders[:8]),
            detail="A []/{}/set()-literal default is created ONCE at def-time "
                   "and shared across every call that omits the argument.",
            remediation="Default to None and construct the mutable value "
                        "inside the function body.",
        ))
    return res


class PythonQualityPlugin:
    name = "python-quality"
    description = "Two AST-based static checks: bare except, mutable defaults"

    def audits(self):
        return [
            SimpleAudit("bare-except", "quality", audit_bare_except),
            SimpleAudit("mutable-default-args", "quality",
                       audit_mutable_default_args),
        ]

    def detect(self, ctx: RepoContext) -> bool:
        """Shape, not name: any repo containing at least one .py file."""
        return next(ctx.root.rglob("*.py"), None) is not None
