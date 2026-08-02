"""Label-leakage audit — corrected after a false positive on real code.

FIRST VERSION WAS WRONG, in three ways at once. It reported a BLOCKER on a
healthy repository:

  1. It scanned every .py file in the tree, including exploratory scripts at the
     repo root that are not production code and ship nowhere.
  2. It matched `msg_998` / `msg_999` -- synthetic probe variables constructed
     BY a test, not dataset ids consumed by decision logic.
  3. It treated docstrings as code, so a comment block explaining a fix
     ("measured on sample_msg_001: ...") counted as leakage.

This is PLAYBOOK P6 landing on the framework itself: the audit produced a
confident, clean-looking BLOCKER that was entirely an artifact of the audit.

The corrected version:
  * scans only paths the caller declares as production
  * strips docstrings and comments via the AST before matching
  * ignores ids that are ASSIGNED (a fixture being built) rather than COMPARED
  * reports what it skipped, so silence is never mistaken for coverage
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from ...plugin_api import AuditResult, Confidence, Finding, RepoContext, Severity

ID_PATTERN = re.compile(r"\b(msg_\d+|sample_msg_\d+|message_\d{2,})\b")

# Directories that are never production, regardless of language.
NON_PRODUCTION = ("audit", "audits", "tests", "test", "scripts", "tools",
                  "benchmarks", "notebooks", "examples")


def _is_production(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & set(NON_PRODUCTION):
        return False
    if rel.name.startswith(("test_", "verify_", "check_", "investigate")):
        return False
    # Numbered exploratory scripts at the repo root: 01_foo.py, 02_bar.py
    if len(rel.parts) == 1 and re.match(r"^\d{2}[_-]", rel.name):
        return False
    return rel.suffix == ".py"


def _code_only(source: str) -> str:
    """Return source with docstrings removed. Comments are already excluded by
    ast.unparse, which reconstructs from the syntax tree."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fall back to a line filter rather than skipping the file silently.
        return "\n".join(l for l in source.splitlines()
                         if not l.strip().startswith("#"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body.pop(0)
    try:
        return ast.unparse(tree)
    except Exception:  # noqa: BLE001
        return source


def audit_label_leakage(ctx: RepoContext,
                        production_globs: tuple[str, ...] = ("code/router/**/*.py",
                                                             "code/main.py")) -> AuditResult:
    """A dataset id inside decision logic is a hardcoded answer.

    An id inside a comment is documentation and is explicitly allowed -- citing
    the row that motivated a rule is good practice, not leakage.
    """
    res = AuditResult("label-leakage", "generalization", True)

    files: list[Path] = []
    for pattern in production_globs:
        files.extend(p for p in ctx.root.glob(pattern) if p.is_file())
    files = [p for p in sorted(set(files)) if _is_production(p.relative_to(ctx.root))]

    if not files:
        res.skipped = (f"no production files matched {production_globs}; "
                       "declare production_globs for this repository")
        res.findings.append(Finding(
            "label-leakage coverage UNKNOWN", Severity.MEDIUM, Confidence.UNKNOWN,
            evidence=f"globs={production_globs} matched 0 files",
            detail="Reported as unknown rather than passing silently."))
        return res

    offenders: list[str] = []
    for p in files:
        rel = p.relative_to(ctx.root)
        code = _code_only(p.read_text(encoding="utf-8", errors="replace"))
        for i, line in enumerate(code.splitlines(), 1):
            if not ID_PATTERN.search(line):
                continue
            # An id being ASSIGNED is usually a fixture under construction; an
            # id being COMPARED or looked up is decision logic keyed to the
            # sample.
            #
            # But the exclusion was too broad, and `orchestrate selftest` is
            # what found it: `SPECIAL = {"msg_002": ("notify", "urgent")}` is
            # an assignment AND a hardcoded answer table. Two forms survive the
            # exclusion, because neither can be a single fixture value:
            #   - an id used as a MAPPING KEY  ("msg_002":  /  "msg_002" =>)
            #   - two or more DISTINCT ids on one line (a lookup table)
            if re.search(r"^\s*[A-Za-z_][\w\.\[\]'\"]*\s*=\s*[^=]", line):
                keyed = re.search(r"""['"](?:sample_)?(?:msg|message)_\d+['"]\s*:""",
                                  line)
                if not keyed and len(set(ID_PATTERN.findall(line))) < 2:
                    continue
            offenders.append(f"{rel}:{i}: {line.strip()[:90]}")

    res.metrics = {"production_files_scanned": len(files),
                   "id_references_in_logic": len(offenders)}
    if offenders:
        res.passed = False
        res.findings.append(Finding(
            "dataset ids used in production decision logic", Severity.BLOCKER,
            Confidence.OBSERVED, evidence="\n".join(offenders[:6]),
            detail="Ids in comments are documentation and are fine. Ids compared "
                   "in logic are hardcoded answers and cannot generalise.",
            remediation="Replace the id with the property that made that row "
                        "special.",
        ))
    return res
