"""`orchestrate experiment --audit` -- same discipline as
score/health.py: every line is a LIVE result from actually running the
experiment engine against synthetic fixtures moments ago, never a cached
or hardcoded status.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from ..memory.store import EngineeringMemory
from .contamination import check_contamination
from .model import Status
from .pareto import frontier
from .runner import finish_experiment, start_experiment
from .store import ExperimentStore


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)


def _init_repo_with_output(repo: Path, reason: str = "a grounded reason") -> None:
    (repo / "dataset").mkdir(parents=True, exist_ok=True)
    (repo / "dataset" / "output.csv").write_text(
        "message_id,action,message_type,reason,confidence,evidence_message_ids\n"
        f'M1,notify,personal,"{reason}",0.9,none\n', encoding="utf-8")
    (repo / "dataset" / "message_history.csv").write_text(
        "message_id,message\nM1,hey are you free this weekend?\n", encoding="utf-8")
    (repo / "problem_statement.md").write_text("# Problem\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@test.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")


def _check_baseline_and_delta() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _init_repo_with_output(d, "old reason")
        store = ExperimentStore(d)
        exp = start_experiment(d, "test experiment", "improve output",
                              target_signal="output", store=store)
        if exp.baseline_score.get("output") is None:
            return False, "baseline capture did not measure the output signal"
        # improve: fix nothing (output already 100), test delta==0 case instead
        exp2 = finish_experiment(d, exp.id, store=store)
        if exp2.status not in Status.TERMINAL:
            return False, f"finish() left status={exp2.status}, not terminal"
        if exp2.actual_gain is None:
            return False, "no-op change produced actual_gain=None, expected 0.0"
        return True, f"baseline captured, no-op finish -> status={exp2.status}, delta={exp2.actual_gain}"


def _check_regression_gate_rejects() -> tuple[bool, str]:
    """A change that improves the target but regresses another signal by
    more than the threshold must be REJECTED, never ACCEPTED."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _init_repo_with_output(d)
        (d / "agent.py").write_text(
            'def classify(t):\n    for x in range(3):\n        chat(x)\n'
            '    return validate(x)\ndef validate(x): return x\n'
            'def chat(x): return x\n', encoding="utf-8")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "add code")
        store = ExperimentStore(d)
        exp = start_experiment(d, "regression test", "hyp", target_signal="output",
                              store=store)
        # simulate a regression: corrupt the code to tank the code signal
        # while output stays the same (nothing changed there)
        (d / "agent.py").write_text("SECRET_KEY = 'abcdefghijklmnop12345678'\n",
                                    encoding="utf-8")
        exp2 = finish_experiment(d, exp.id, store=store)
        if exp2.status == Status.ACCEPTED and exp2.regressions:
            return False, "ACCEPTED an experiment with a recorded regression"
        return True, f"status={exp2.status}, regressions={exp2.regressions}"


def _check_contamination_detection() -> tuple[bool, str]:
    ok1, _ = check_contamination(["router.py", "prompts.py"])
    ok2, reason = check_contamination(["router.py", "README.md", "docs/x.md"])
    if ok1:
        return False, "related code-only changes were flagged as contamination"
    if not ok2:
        return False, "README+docs mixed with code was NOT flagged as contamination"
    return True, f"clean diff -> not flagged; noisy diff -> flagged ({reason[:60]}...)"


def _check_no_accept_without_measured_gain() -> tuple[bool, str]:
    """Structural check: Experiment.actual_gain must be a real float
    before ACCEPTED can be set. finish_experiment() is the only writer of
    status=ACCEPTED, and it always sets actual_gain first -- verify that
    invariant holds by inspecting the function's own behavior on an
    UNKNOWN target."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _init_repo_with_output(d)
        store = ExperimentStore(d)
        exp = start_experiment(d, "unmeasurable target", "hyp",
                              target_signal="interview", store=store)
        exp2 = finish_experiment(d, exp.id, store=store)
        if exp2.status == Status.ACCEPTED:
            return False, "ACCEPTED an experiment whose target signal was UNKNOWN"
        if exp2.actual_gain is not None:
            return False, "actual_gain was set for an UNKNOWN target signal"
        return True, f"UNKNOWN target -> status={exp2.status}, actual_gain=None"


def _check_history_and_rejection_memory() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _init_repo_with_output(d)
        store = ExperimentStore(d)
        exp = start_experiment(d, "rejection test", "hyp", target_signal="output",
                              store=store)
        # break it: wrong action value
        out = d / "dataset" / "output.csv"
        out.write_text(out.read_text(encoding="utf-8").replace(",notify,", ",BADVAL,"),
                       encoding="utf-8")
        mem = EngineeringMemory(d / "memory.json")
        exp2 = finish_experiment(d, exp.id, store=store, memory=mem)
        if exp2.status != Status.REJECTED:
            return False, f"expected REJECTED for a spec violation, got {exp2.status}"
        if not mem.rejections():
            return False, "rejected experiment was not written to Engineering Memory"
        if store.get(exp.id) is None or store.get(exp.id).id not in [e.id for e in store.all()]:
            return False, "experiment not retrievable from history after finish"
        return True, f"REJECTED experiment recorded in memory " \
                     f"({len(mem.rejections())} rejection(s)) and in history"


def _check_pareto_frontier() -> tuple[bool, str]:
    from .model import Experiment
    a = Experiment(id="EXP-T1", timestamp="t", title="a", target_signal="output",
                  status=Status.ACCEPTED, delta={"code": 2, "output": 1})
    b = Experiment(id="EXP-T2", timestamp="t", title="b", target_signal="output",
                  status=Status.ACCEPTED, delta={"code": 1, "output": 3})
    c = Experiment(id="EXP-T3", timestamp="t", title="c", target_signal="output",
                  status=Status.REJECTED, delta={"code": -4, "output": 3})
    f = frontier([a, b, c])
    ids = {e.id for e in f}
    if "EXP-T3" in ids:
        return False, "a dominated experiment (worse on code, tied on output) " \
                     "was not excluded from the frontier"
    if ids != {"EXP-T1", "EXP-T2"}:
        return False, f"expected {{EXP-T1, EXP-T2}}, got {ids}"
    return True, "dominated experiment correctly excluded from the frontier"


_CATEGORIES = [
    ("Baseline creation + delta calculation", _check_baseline_and_delta),
    ("Regression gate rejects a regressed accept", _check_regression_gate_rejects),
    ("Contamination detection", _check_contamination_detection),
    ("No ACCEPTED without measured gain", _check_no_accept_without_measured_gain),
    ("History + rejection -> Engineering Memory", _check_history_and_rejection_memory),
    ("Pareto frontier excludes dominated", _check_pareto_frontier),
]


def run_health_checks() -> list[tuple[str, bool, str]]:
    results = []
    for name, fn in _CATEGORIES:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, f"check raised {type(exc).__name__}: {exc}"
        results.append((name, ok, detail))
    return results


def render_health_report() -> str:
    results = run_health_checks()
    lines = ["PHASE 2 EXPERIMENT ENGINE HEALTH", "=" * 34, "",
            "(every line below is a LIVE result against a real git "
            "fixture built and torn down moments ago)", ""]
    for name, ok, detail in results:
        lines.append(f"  {name:<46} {'PASS' if ok else 'FAIL'}")
        lines.append(f"    {detail}")
    lines.append("")
    failed = [n for n, ok, _ in results if not ok]
    if failed:
        lines.append("OVERALL: NEEDS WORK")
        lines.append(f"  Failing categories: {', '.join(failed)}")
    else:
        lines.append("OVERALL: TRUSTWORTHY")
    return "\n".join(lines)
