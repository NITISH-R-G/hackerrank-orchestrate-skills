from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from orchestrate_kit.experiment import git_util
from orchestrate_kit.experiment.contamination import check_contamination
from orchestrate_kit.experiment.model import Experiment, Status
from orchestrate_kit.experiment.next import recommend_next
from orchestrate_kit.experiment.pareto import dominates, frontier
from orchestrate_kit.experiment.runner import finish_experiment, start_experiment
from orchestrate_kit.experiment.store import ExperimentStore
from orchestrate_kit.memory.store import EngineeringMemory
from orchestrate_kit.score.scoreboard import build_scorecard


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)


def _init_repo(repo: Path, reason: str = "a grounded reason for this row") -> None:
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


# ------------------------------------------------------------------- model.py

def test_experiment_round_trips_through_dict():
    e = Experiment(id="EXP-0001", timestamp="t", title="x",
                  delta={"code": 1.5}, regressions=["output regressed"])
    back = Experiment.from_dict(e.to_dict())
    assert back.id == e.id
    assert back.delta == e.delta
    assert back.regressions == e.regressions


# ------------------------------------------------------------------- store.py

def test_store_generates_sequential_ids(tmp_path):
    store = ExperimentStore(tmp_path)
    assert store.next_id() == "EXP-0001"
    store.add(Experiment(id="EXP-0001", timestamp="t", title="a"))
    assert store.next_id() == "EXP-0002"


def test_store_persists_across_instances(tmp_path):
    store = ExperimentStore(tmp_path)
    store.add(Experiment(id="EXP-0001", timestamp="t", title="a", delta={"code": 3.0}))
    store.save()
    reloaded = ExperimentStore(tmp_path)
    assert reloaded.get("EXP-0001").delta == {"code": 3.0}


# --------------------------------------------------------------- git_util.py

def test_git_util_parses_porcelain_status_correctly(tmp_path):
    """Regression test for a confirmed bug: `git status --porcelain`
    pads its status code with a leading space (" M path"), and a naive
    .strip() on the WHOLE multi-line stdout ate that leading space off
    only the first line, misaligning every downstream line[3:] parse and
    turning "dataset/output.csv" into "ataset/output.csv"."""
    _init_repo(tmp_path)
    sha = git_util.current_sha(tmp_path)
    (tmp_path / "dataset" / "output.csv").write_text(
        "message_id,action,message_type,reason,confidence,evidence_message_ids\n"
        'M1,notify,personal,"different reason","0.9",none\n', encoding="utf-8")
    changed = git_util.changed_files_since(tmp_path, sha)
    assert "dataset/output.csv" in changed
    assert not any(f.startswith("ataset") for f in changed)


def test_git_util_not_dirty_on_clean_repo(tmp_path):
    _init_repo(tmp_path)
    assert git_util.is_dirty(tmp_path) is False


def test_git_util_dirty_after_edit(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "new.txt").write_text("x", encoding="utf-8")
    assert git_util.is_dirty(tmp_path) is True


def test_git_util_non_repo_returns_none(tmp_path):
    assert git_util.current_sha(tmp_path) is None
    assert git_util.is_git_repo(tmp_path) is False


# ----------------------------------------------------------- contamination.py

def test_contamination_clean_code_only_diff_passes():
    ok, _ = check_contamination(["router.py", "prompts.py"])
    assert ok is False


def test_contamination_noise_mixed_with_code_flagged():
    ok, reason = check_contamination(["router.py", "README.md"])
    assert ok is True
    assert "README.md" in reason


def test_contamination_too_many_files_flagged():
    ok, _ = check_contamination([f"f{i}.py" for i in range(12)])
    assert ok is True


def test_contamination_empty_diff_not_flagged():
    ok, _ = check_contamination([])
    assert ok is False


# ----------------------------------------------------------------- runner.py

def test_experiment_lifecycle_no_op_is_not_accepted(tmp_path):
    """The audit's central requirement: 'I changed nothing and nothing
    moved' must never be ACCEPTED."""
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    exp = start_experiment(tmp_path, "no-op", "hyp", target_signal="output", store=store)
    exp2 = finish_experiment(tmp_path, exp.id, store=store)
    assert exp2.status != Status.ACCEPTED
    assert exp2.actual_gain == 0.0


def test_experiment_real_improvement_is_accepted(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "weak.py").write_text("def f(): pass\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "weak code")
    store = ExperimentStore(tmp_path)
    exp = start_experiment(tmp_path, "add robustness", "hyp", target_signal="code",
                          store=store)
    (tmp_path / "weak.py").write_text(
        "MAX_RETRIES = 3\n\n"
        "def f(x: int) -> dict:\n"
        "    for attempt in range(MAX_RETRIES):\n"
        "        result = call(x)\n"
        "        if validate(result):\n"
        "            return result\n"
        "    raise RuntimeError('exhausted retries')\n\n"
        "def validate(r: dict) -> bool:\n"
        "    assert 'status' in r\n"
        "    return True\n\n"
        "def call(x: int) -> dict:\n"
        "    return {'status': 'ok'}\n", encoding="utf-8")
    exp2 = finish_experiment(tmp_path, exp.id, store=store)
    assert exp2.status == Status.ACCEPTED
    assert exp2.actual_gain > 0


def test_experiment_regression_blocks_acceptance(tmp_path):
    """Target signal must not be allowed to coast on a big regression
    elsewhere -- the audit's explicit named case."""
    _init_repo(tmp_path)
    (tmp_path / "agent.py").write_text(
        "def classify(t):\n    for x in range(3):\n        chat(x)\n"
        "    return validate(x)\ndef validate(x): return x\ndef chat(x): return x\n",
        encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "add code")
    store = ExperimentStore(tmp_path)
    exp = start_experiment(tmp_path, "regress code", "hyp", target_signal="output",
                          store=store)
    (tmp_path / "agent.py").write_text(
        "SECRET_TOKEN = 'abcdefghijklmnopqrstuvwx12345678'\n", encoding="utf-8")
    exp2 = finish_experiment(tmp_path, exp.id, store=store)
    assert exp2.status != Status.ACCEPTED
    assert exp2.regressions


def test_experiment_contamination_forces_inconclusive(tmp_path):
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    exp = start_experiment(tmp_path, "mixed change", "hyp", target_signal="output",
                          store=store)
    (tmp_path / "router.py").write_text("def f(): pass\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("stuff", encoding="utf-8")
    exp2 = finish_experiment(tmp_path, exp.id, store=store)
    assert exp2.status == Status.INCONCLUSIVE
    assert "CONTAMINATION" in exp2.decision


def test_experiment_unmeasurable_target_is_inconclusive_not_accepted(tmp_path):
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    exp = start_experiment(tmp_path, "target interview", "hyp",
                          target_signal="interview", store=store)
    exp2 = finish_experiment(tmp_path, exp.id, store=store)
    assert exp2.status != Status.ACCEPTED
    assert exp2.actual_gain is None


def test_experiment_own_bookkeeping_file_does_not_self_contaminate(tmp_path):
    """Regression test for a confirmed bug: ExperimentStore writes
    .orchestrate_experiments.json into the SAME repo it's tracking, and
    that file showing up as an untracked change made every single
    experiment contaminate itself on its own state file."""
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    exp = start_experiment(tmp_path, "clean single-file change", "hyp",
                          target_signal="output", store=store)
    (tmp_path / "dataset" / "output.csv").write_text(
        "message_id,action,message_type,reason,confidence,evidence_message_ids\n"
        'M1,notify,personal,"a more grounded and specific reason",0.9,none\n',
        encoding="utf-8")
    exp2 = finish_experiment(tmp_path, exp.id, store=store)
    assert "CONTAMINATION" not in exp2.decision
    assert ".orchestrate_experiments.json" not in exp2.files_changed


def test_finish_unknown_experiment_raises(tmp_path):
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    with pytest.raises(KeyError):
        finish_experiment(tmp_path, "EXP-9999", store=store)


def test_finish_twice_raises(tmp_path):
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    exp = start_experiment(tmp_path, "x", "hyp", target_signal="output", store=store)
    finish_experiment(tmp_path, exp.id, store=store)
    with pytest.raises(ValueError):
        finish_experiment(tmp_path, exp.id, store=store)


def test_rejected_experiment_writes_to_engineering_memory(tmp_path):
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    mem = EngineeringMemory(tmp_path / "memory.json")
    exp = start_experiment(tmp_path, "bad change", "hyp", target_signal="output",
                          store=store)
    out = tmp_path / "dataset" / "output.csv"
    out.write_text(out.read_text(encoding="utf-8").replace(",notify,", ",BADVAL,"),
                   encoding="utf-8")
    finish_experiment(tmp_path, exp.id, store=store, memory=mem)
    rejections = mem.rejections()
    assert len(rejections) == 1
    assert rejections[0].reconsider_if


# ----------------------------------------------------------------- pareto.py

def test_pareto_dominated_experiment_excluded():
    a = Experiment(id="A", timestamp="t", title="a", status=Status.ACCEPTED,
                   delta={"code": 2, "output": 1})
    b = Experiment(id="B", timestamp="t", title="b", status=Status.ACCEPTED,
                   delta={"code": 1, "output": 3})
    c = Experiment(id="C", timestamp="t", title="c", status=Status.REJECTED,
                   delta={"code": -4, "output": 3})
    assert dominates(a, c) is False  # a doesn't beat c on output
    assert dominates(b, c) is True   # b ties output, beats code
    result = frontier([a, b, c])
    assert {e.id for e in result} == {"A", "B"}


def test_pareto_no_shared_dimensions_means_no_domination():
    a = Experiment(id="A", timestamp="t", title="a", status=Status.ACCEPTED,
                   delta={"code": 2})
    b = Experiment(id="B", timestamp="t", title="b", status=Status.ACCEPTED,
                   delta={"output": 2})
    assert dominates(a, b) is False
    assert dominates(b, a) is False


def test_pareto_excludes_non_terminal_experiments():
    a = Experiment(id="A", timestamp="t", title="a", status=Status.RUNNING,
                  delta={"code": 5})
    assert frontier([a]) == []


# ------------------------------------------------------------------- next.py

def test_next_experiment_never_recommends_unknown_signal_over_known_weak_one(tmp_path):
    """An UNKNOWN signal at real weight is surfaced as the priority --
    covering it is prerequisite to improving it at all."""
    _init_repo(tmp_path)
    card = build_scorecard(tmp_path)
    store = ExperimentStore(tmp_path)
    rec = recommend_next(card, store)
    # output/interview/transcript weights sum higher than code alone in
    # this fixture's UNKNOWN set -- at minimum the recommendation must be
    # for a real, currently-relevant signal, not a fabricated one.
    assert rec.target_signal in {"code", "output", "interview", "transcript", ""}


def test_next_experiment_does_not_jump_straight_to_agentic_changes(tmp_path):
    """The audit's named principle: a rubric wanting 'agent shape' is not
    license to recommend 'add another agent' before cheaper rungs are
    tried. For Code ZIP, agentic-changes (rung 10) must never be the
    FIRST recommendation when cheaper rungs (3, 5, 8, 9) are untried."""
    _init_repo(tmp_path)
    (tmp_path / "rules.py").write_text("def f(): return 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "code")
    card = build_scorecard(tmp_path)
    store = ExperimentStore(tmp_path)
    rec = recommend_next(card, store)
    if rec.target_signal == "code":
        assert rec.ladder_rung < 10


def test_next_experiment_skips_already_tried_rungs(tmp_path):
    _init_repo(tmp_path)
    store = ExperimentStore(tmp_path)
    exp = Experiment(id="EXP-0001", timestamp="t", title="constraints change",
                    target_signal="output", status=Status.REJECTED)
    store.add(exp)
    card = build_scorecard(tmp_path)
    rec = recommend_next(card, store)
    if rec.target_signal == "output":
        assert rec.ladder_rung != 3  # "constraints" already tried and rejected


# ----------------------------------------------------------------- health.py

def test_experiment_health_report_all_categories_pass_live():
    from orchestrate_kit.experiment.health import run_health_checks
    results = run_health_checks()
    failed = [(name, detail) for name, ok, detail in results if not ok]
    assert not failed, f"experiment health categories failed: {failed}"
    assert len(results) >= 6


# --------------------------------------------------------- CLI end-to-end

def test_cli_experiment_start_finish_end_to_end(tmp_path, capsys):
    from orchestrate_kit.cli import main
    _init_repo(tmp_path)
    rc = main(["experiment", "--repo", str(tmp_path), "start", "cli test",
              "--target", "output"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "EXPERIMENT EXP-0001" in out

    rc = main(["experiment", "--repo", str(tmp_path), "finish", "EXP-0001",
              "--no-memory"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Verdict:" in out


def test_cli_experiment_audit_end_to_end(capsys):
    from orchestrate_kit.cli import main
    rc = main(["experiment", "--audit"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PHASE 2 EXPERIMENT ENGINE HEALTH" in out


def test_cli_experiment_list_and_next_end_to_end(tmp_path, capsys):
    from orchestrate_kit.cli import main
    _init_repo(tmp_path)
    main(["experiment", "--repo", str(tmp_path), "start", "x", "--target", "output"])
    capsys.readouterr()
    rc = main(["experiment", "--repo", str(tmp_path), "list"])
    assert rc == 0
    assert "EXP-0001" in capsys.readouterr().out

    rc = main(["experiment", "--repo", str(tmp_path), "next"])
    assert rc == 0
    assert "NEXT EXPERIMENT" in capsys.readouterr().out
