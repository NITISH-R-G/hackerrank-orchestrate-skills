"""Negative control for the python-quality example plugin.

Same standard `orchestrate plugin new` enforces on a generated plugin,
applied here by hand: every audit needs a case where it MUST fire, a case
where it must NOT fire (the false-positive guard), and a check that it
degrades to `skipped`, not a silent pass, on a repo with no Python at all.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrate_kit.evaluator.plugin_api import RepoContext          # noqa: E402
from python_quality import (                                          # noqa: E402
    PythonQualityPlugin,
    audit_bare_except,
    audit_mutable_default_args,
)


def _repo(tmp_path: Path, code: str) -> RepoContext:
    (tmp_path / "app.py").write_text(code, encoding="utf-8")
    return RepoContext(root=tmp_path)


# --------------------------------------------------------------- bare except
def test_bare_except_is_caught(tmp_path):
    ctx = _repo(tmp_path, "try:\n    risky()\nexcept:\n    pass\n")
    res = audit_bare_except(ctx)
    assert not res.passed
    assert res.findings[0].severity.value == "medium"


def test_except_exception_is_not_flagged(tmp_path):
    """The false-positive guard. `except Exception:` is the FIX for a bare
    except -- an audit that can't tell them apart is worse than useless."""
    ctx = _repo(tmp_path, "try:\n    risky()\nexcept Exception:\n    pass\n")
    assert audit_bare_except(ctx).passed


def test_except_tuple_is_not_flagged(tmp_path):
    ctx = _repo(tmp_path,
               "try:\n    risky()\nexcept (ValueError, TypeError):\n    pass\n")
    assert audit_bare_except(ctx).passed


def test_bare_except_inside_a_string_is_not_flagged(tmp_path):
    """The exact class of bug this project's own leakage audit had: matching
    inside a string/docstring instead of real code. AST parsing sidesteps it
    by construction -- confirm that's actually true here."""
    ctx = _repo(tmp_path, 'DOC = """\ntry:\n    x()\nexcept:\n    pass\n"""\n')
    assert audit_bare_except(ctx).passed


# --------------------------------------------------------- mutable defaults
def test_mutable_list_default_is_caught(tmp_path):
    ctx = _repo(tmp_path, "def add(item, items=[]):\n    items.append(item)\n"
                          "    return items\n")
    res = audit_mutable_default_args(ctx)
    assert not res.passed
    assert "add" in res.findings[0].evidence


def test_mutable_dict_and_set_defaults_are_caught(tmp_path):
    ctx = _repo(tmp_path, "def f(cache={}):\n    pass\n\n\ndef g(seen=set()):\n"
                          "    pass\n")
    res = audit_mutable_default_args(ctx)
    assert res.metrics["mutable_defaults"] == 2


def test_none_default_is_not_flagged(tmp_path):
    """The idiomatic FIX -- must not itself be flagged."""
    ctx = _repo(tmp_path, "def add(item, items=None):\n"
                          "    items = items if items is not None else []\n"
                          "    items.append(item)\n    return items\n")
    assert audit_mutable_default_args(ctx).passed


def test_noarg_list_dict_set_calls_are_caught_same_as_literals(tmp_path):
    """`list()`/`dict()`/`set()` execute once at def-time, exactly like `[]`
    and `{}` -- same bug, different spelling. An earlier draft of this audit
    treated these as safe; this test is what caught that gap."""
    ctx = _repo(tmp_path, "def f(items=list()):\n    pass\n")
    res = audit_mutable_default_args(ctx)
    assert not res.passed
    assert "f" in res.findings[0].evidence


def test_call_to_a_user_factory_is_not_flagged(tmp_path):
    """A call the audit cannot statically prove returns a shared mutable
    object -- correctly out of scope. Guessing here would trade a real bug
    class for false positives on legitimate code (e.g. `default=Config()`
    that intentionally returns a fresh, cheap object)."""
    ctx = _repo(tmp_path, "def make():\n    return object()\n\n\n"
                          "def f(config=make()):\n    pass\n")
    assert audit_mutable_default_args(ctx).passed


def test_ctor_call_with_arguments_is_not_flagged(tmp_path):
    """`list(range(3))` shares the exact same evaluate-once mechanism as
    `list()` -- this is a deliberate PRECISION tradeoff, not a claim that it's
    a different bug. An empty no-arg constructor has no legitimate reason to
    want shared state, so flagging it is always correct; a populated one
    occasionally IS an intentional shared read-only lookup table, so flagging
    it risks a false positive on legitimate code. Scoped narrow on purpose."""
    ctx = _repo(tmp_path, "def f(items=list(range(3))):\n    pass\n")
    assert audit_mutable_default_args(ctx).passed


# ------------------------------------------------------------------- shared
def test_skips_rather_than_passing_on_a_repo_with_no_python(tmp_path):
    (tmp_path / "README.md").write_text("no python here\n", encoding="utf-8")
    ctx = RepoContext(root=tmp_path)
    assert audit_bare_except(ctx).skipped
    assert audit_mutable_default_args(ctx).skipped


def test_a_syntax_error_does_not_crash_the_audit(tmp_path):
    ctx = _repo(tmp_path, "def broken(:\n    pass\n")
    res_a = audit_bare_except(ctx)   # must not raise
    res_b = audit_mutable_default_args(ctx)
    assert res_a.passed and res_b.passed   # nothing PARSED, so nothing flagged


def test_detects_on_shape(tmp_path):
    (tmp_path / "x.py").write_text("pass\n", encoding="utf-8")
    assert PythonQualityPlugin().detect(RepoContext(root=tmp_path))


def test_does_not_detect_a_non_python_repo(tmp_path):
    (tmp_path / "README.md").write_text("hi\n", encoding="utf-8")
    assert not PythonQualityPlugin().detect(RepoContext(root=tmp_path))


def test_every_finding_carries_evidence(tmp_path):
    ctx = _repo(tmp_path, "try:\n    x()\nexcept:\n    pass\n\n\n"
                          "def f(items=[]):\n    pass\n")
    for audit in (audit_bare_except, audit_mutable_default_args):
        for f in audit(ctx).findings:
            assert f.evidence.strip()


def test_plugin_is_registerable_against_this_very_repository():
    """The real proof of generality: run it against orchestrate_kit itself,
    which is not sample data -- it's the production code this whole project
    ships. Whatever it reports here must be true."""
    from orchestrate_kit.evaluator import Evaluator, RepoContext as RC

    root = Path(__file__).resolve().parents[2]
    ev = Evaluator(RC(root=root))
    ev.register(PythonQualityPlugin())
    result = ev.run()
    assert result.plugins == ["python-quality"]
    # Not asserting zero findings -- asserting the run COMPLETES and reports
    # real metrics, which is the actual claim being tested.
    quality = result.categories.get("quality")
    assert quality is not None
    assert quality.audits_run == 2
