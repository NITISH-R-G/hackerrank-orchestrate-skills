"""Code ZIP scorer -- maps directly to the published rubric:

    Agent architecture       30%   real agent loop, model-driven routing,
                                   multi-agent handoffs -- vs. a hardcoded
                                   workflow with LLM calls sprinkled in
    Prompt and tool craft    30%   role assignment, constraints, structured
                                   output, refusal conditions
    Agent robustness         25%   retries, iteration caps, output validation
    Engineering rigor        15%   modularity, type hints, secrets via env

HackerRank's own writeup states plainly: "we reward only what is
observable in the source code. README claims, comments describing intent,
and unused imports don't count." This scorer follows the identical rule --
it parses code via AST, never reads README/docstring prose as evidence,
and treats an import with no corresponding call as noise, not signal.

Heuristic, not semantic. It cannot tell a genuinely well-designed agent
loop from a superficially similar one; it detects the SHAPE the rubric
asks for, the same honesty boundary every other analyzer in this project
states explicitly.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path

from .signals import Confidence, Finding, SignalScore

_SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "venv",
              "node_modules", "site-packages"}

# A real API key never belongs in source -- HackerRank's own starter repo
# guidance (quoted in skills/orchestrate-secrets-and-determinism) says
# secrets must come from env vars. This is a cheap, high-precision check:
# a 20+ char alnum literal assigned to something named like a key.
_HARDCODED_SECRET = re.compile(
    r"""(api[_-]?key|secret|token|password)\s*=\s*['"][A-Za-z0-9_\-]{16,}['"]""",
    re.I)
_ENV_SECRET = re.compile(r"\bos\.(?:environ|getenv)\b")


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py")
                 if not (_SKIP_DIRS & set(p.relative_to(root).parts)))


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None


def _code_only(source: str) -> str:
    """Source with every STRING and COMMENT token blanked out.

    Behavioral-evidence checks (retry, validation, refusal, structured
    output, iteration caps) must never fire on keyword soup stuffed into a
    docstring, a comment, or an unrelated string literal -- only on
    identifiers/calls that actually appear in executable code. Fails
    closed: if the file can't be tokenized, behavioral checks see nothing
    rather than falling back to the unsafe raw-text scan.
    """
    out: list[str] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type in (tokenize.STRING, tokenize.COMMENT):
                out.append(" ")
            elif tok.type in (tokenize.NEWLINE, tokenize.NL):
                out.append("\n")
            else:
                out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return ""
    return " ".join(out)


def _trivial_body(body: list[ast.stmt]) -> bool:
    """True if a class/function body is just `pass` and/or a docstring --
    i.e. a stub that exists only to make a name match a keyword regex."""
    real = [n for n in body if not (isinstance(n, ast.Pass) or
                                    (isinstance(n, ast.Expr) and
                                     isinstance(n.value, ast.Constant) and
                                     isinstance(n.value.value, str)))]
    return len(real) == 0


@dataclass
class _Signals:
    files: int = 0
    functions: int = 0
    typed_functions: int = 0
    loops_with_calls: int = 0
    routing_branches: int = 0
    role_classes: int = 0
    system_prompt_strings: int = 0
    tool_schema_dicts: int = 0
    structured_output: int = 0
    refusal_conditions: int = 0
    retry_patterns: int = 0
    bounded_iteration_caps: int = 0
    output_validation: int = 0
    hardcoded_secrets: int = 0
    env_secret_usage: int = 0
    long_functions: int = 0


_CALL_NAMES_LLM = re.compile(
    r"\b(chat|completions?|generate|invoke|complete|messages)\b", re.I)
_TOOL_LIKE = re.compile(r"\b(tool|function|dispatch|route|handler)\b", re.I)
_ROLE_LIKE = re.compile(r"\b(agent|role|persona)\b", re.I)
_STRUCTURED_OUTPUT = re.compile(
    r"\bBaseModel\b|response_format|json\.loads|json_schema|pydantic", re.I)
_REFUSAL = re.compile(
    r"\brefuse\w*\b|\bcannot\b|\breject\w*\b|raise\s+\w*Error", re.I)
_RETRY = re.compile(
    r"\bmax_retries\b|\bretry\w*\b|\btenacity\b|for\s+\w+\s+in\s+range\("
    r"\s*(?:MAX_RETR|RETRY)", re.I)
_MAX_ITER = re.compile(r"\bmax_iter\w*\b|\bmax_step\w*\b|\bMAX_TURNS\b", re.I)
_VALIDATION = re.compile(
    r"\bassert\b|\bvalidat\w*\b|\.dict\(\)|model_validate|schema\.validate",
    re.I)


def _has_system_prompt(tree: ast.Module) -> bool:
    """AST-based, not a substring search: a real assignment whose target
    name says 'system prompt', or a chat-message-shaped dict literal with
    a 'system' key -- never a comment or unrelated string mentioning the
    word."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and "system_prompt" in t.id.lower():
                    return True
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                        and k.value.lower() == "system"):
                    return True
    return False


def _collect(tree: ast.Module, source: str, sig: _Signals) -> None:
    sig.files += 1
    code = _code_only(source)

    if _has_system_prompt(tree):
        sig.system_prompt_strings += 1
    if _STRUCTURED_OUTPUT.search(code):
        sig.structured_output += 1
    if _REFUSAL.search(code):
        sig.refusal_conditions += 1
    if _RETRY.search(code):
        sig.retry_patterns += 1
    if _MAX_ITER.search(code):
        sig.bounded_iteration_caps += 1
    if _VALIDATION.search(code):
        sig.output_validation += 1
    if _HARDCODED_SECRET.search(source):
        sig.hardcoded_secrets += 1
    if _ENV_SECRET.search(code):
        sig.env_secret_usage += 1

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if _ROLE_LIKE.search(node.name) and not _trivial_body(node.body):
                sig.role_classes += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig.functions += 1
            args = node.args.args
            typed = sum(1 for a in args if a.annotation is not None)
            if node.returns is not None or (args and typed == len(args)):
                sig.typed_functions += 1
            body_len = (node.body[-1].end_lineno or node.lineno) - node.lineno
            if body_len > 80:
                sig.long_functions += 1
            if _TOOL_LIKE.search(node.name) and not _trivial_body(node.body):
                sig.tool_schema_dicts += 1
        elif isinstance(node, (ast.For, ast.While)):
            calls_inside = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
            for c in calls_inside:
                fname = ""
                if isinstance(c.func, ast.Attribute):
                    fname = c.func.attr
                elif isinstance(c.func, ast.Name):
                    fname = c.func.id
                if _CALL_NAMES_LLM.search(fname):
                    sig.loops_with_calls += 1
                    break
        elif isinstance(node, ast.If):
            # A branch dispatching on a classification/type field, not a
            # trivial guard clause -- heuristic: compares an attribute or
            # subscript (e.g. `action_type ==`, `row["type"] ==`) rather
            # than a bare name or constant.
            test = node.test
            if isinstance(test, ast.Compare) and any(
                    isinstance(c, (ast.Attribute, ast.Subscript))
                    for c in [test.left, *test.comparators]):
                sig.routing_branches += 1


def _score(count: int, per_hit: float, cap: float = 100.0) -> float:
    return min(cap, count * per_hit)


def score_code(repo_root: Path) -> SignalScore:
    files = _python_files(repo_root)
    if not files:
        return SignalScore("code", "Code ZIP", None, 0.30, Confidence.UNKNOWN,
                           notes=["no .py files found under this path"])

    sig = _Signals()
    for f in files:
        tree = _parse(f)
        if tree is None:
            continue
        _collect(tree, f.read_text(encoding="utf-8", errors="replace"), sig)

    # ---- Agent architecture (30%) -------------------------------------
    architecture = (
        _score(sig.loops_with_calls, 25)
        + _score(sig.routing_branches, 8, cap=50)
        + _score(sig.role_classes, 20, cap=40)
    ) / 1.0
    architecture = min(100.0, architecture)

    # ---- Prompt and tool craft (30%) -----------------------------------
    craft = (
        _score(min(sig.system_prompt_strings, 5), 15)
        + _score(min(sig.tool_schema_dicts, 5), 8)
        + _score(min(sig.structured_output, 5), 12)
        + _score(min(sig.refusal_conditions, 5), 10)
    )
    craft = min(100.0, craft)

    # ---- Agent robustness (25%) ----------------------------------------
    robustness = (
        _score(min(sig.retry_patterns, 5), 20)
        + _score(min(sig.bounded_iteration_caps, 5), 20)
        + _score(min(sig.output_validation, 10), 6)
    )
    robustness = min(100.0, robustness)

    # ---- Engineering rigor (15%) ---------------------------------------
    type_ratio = (sig.typed_functions / sig.functions) if sig.functions else 0.0
    modularity = min(1.0, sig.files / 4) * 40
    rigor = modularity + type_ratio * 40
    if sig.env_secret_usage:
        rigor += 20
    if sig.hardcoded_secrets:
        rigor -= 40   # a real defect, not a missing bonus
    if sig.long_functions:
        rigor -= min(20, sig.long_functions * 4)
    rigor = max(0.0, min(100.0, rigor))

    weighted = 0.30 * architecture + 0.30 * craft + 0.25 * robustness + 0.15 * rigor

    findings = []
    if sig.hardcoded_secrets:
        findings.append(Finding(
            "hardcoded secret pattern found",
            f"{sig.hardcoded_secrets} file(s) -- real defect, not a heuristic miss"))
    if not sig.loops_with_calls:
        findings.append(Finding(
            "no detected agent loop",
            "no for/while loop containing a chat/completion-shaped call -- "
            "HackerRank's rubric explicitly distinguishes a real agent loop "
            "from 'hardcoded workflow with LLM calls'"))
    if not sig.retry_patterns and not sig.bounded_iteration_caps:
        findings.append(Finding(
            "no retry or iteration-cap pattern found",
            "Agent Robustness (25%) rewards exactly this"))
    if type_ratio < 0.3 and sig.functions > 3:
        findings.append(Finding(
            f"low type-hint coverage ({type_ratio:.0%})",
            "Engineering Rigor (15%) component"))

    notes = [f"sub-scores -- architecture {architecture:.0f}, "
            f"craft {craft:.0f}, robustness {robustness:.0f}, "
            f"rigor {rigor:.0f} (published weights 30/30/25/15)",
            f"{len(files)} .py file(s) scanned, {sig.functions} function(s)"]

    return SignalScore("code", "Code ZIP", weighted, 0.30, Confidence.HEURISTIC,
                       findings, notes)
