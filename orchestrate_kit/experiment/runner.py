"""The experiment lifecycle: start (baseline) -> finish (measure, gate,
decide, record). This is the enforcement point for the whole Phase 2
philosophy -- ACCEPTED can only be reached through a real measured
actual_gain, REJECTED experiments are written to Engineering Memory with
a reconsider_if condition, and a contaminated or baseline-less experiment
can never be ACCEPTED no matter what the numbers say.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..memory.store import Benchmark, EngineeringMemory, MemoryEntry
from ..score.scoreboard import build_scorecard
from ..score.signals import ScoreCard
from . import git_util
from .contamination import check_contamination
from .model import Experiment, Status
from .store import ExperimentStore

# A signal moving worse than this many points, while not the target of
# the experiment, is a "material" regression -- small heuristic noise
# (a hedge-word count shifting a transcript score by a point) should not
# by itself sink an otherwise-real improvement.
_REGRESSION_THRESHOLD = 2.0


def _score_dict(card: ScoreCard) -> dict:
    d = {s.name: s.estimated_score for s in card.signals}
    d["weighted"] = card.weighted_estimate
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_experiment(repo_root: Path, title: str, hypothesis: str,
                     target_signal: str, target_dimension: str = "",
                     python: str = "python",
                     transcript_path: Path | None = None,
                     interview_result_path: Path | None = None,
                     store: ExperimentStore | None = None) -> Experiment:
    store = store or ExperimentStore(repo_root)
    card = build_scorecard(repo_root, python=python,
                           transcript_path=transcript_path,
                           interview_result_path=interview_result_path)

    sha = git_util.current_sha(repo_root)
    notes = []
    if not git_util.is_git_repo(repo_root):
        notes.append("not a git repository -- baseline/experiment commits "
                     "cannot be recorded; provenance is UNKNOWN")
    elif git_util.is_dirty(repo_root):
        notes.append("WARNING: working tree was dirty when the baseline was "
                     "captured -- the baseline itself may include "
                     "uncommitted work, which weakens attribution")

    exp = Experiment(
        id=store.next_id(), timestamp=_now(), title=title,
        hypothesis=hypothesis, target_signal=target_signal,
        target_dimension=target_dimension,
        baseline_commit=sha or "", baseline_score=_score_dict(card),
        status=Status.RUNNING, notes=notes)
    store.add(exp)
    store.save()
    return exp


def finish_experiment(repo_root: Path, exp_id: str,
                      python: str = "python",
                      transcript_path: Path | None = None,
                      interview_result_path: Path | None = None,
                      store: ExperimentStore | None = None,
                      memory: EngineeringMemory | None = None) -> Experiment:
    store = store or ExperimentStore(repo_root)
    exp = store.get(exp_id)
    if exp is None:
        raise KeyError(f"no experiment {exp_id}")
    if exp.status not in (Status.RUNNING, Status.PROPOSED):
        raise ValueError(f"{exp_id} is already {exp.status} -- cannot re-finish "
                        "a terminal experiment (start a new one instead)")

    changed = git_util.changed_files_since(repo_root, exp.baseline_commit or None)
    # The experiment/score engine's own bookkeeping files are written
    # into the target repo by this tool itself (store.save(),
    # record_history()) -- they are not part of the change under test and
    # must never even be CATEGORIZED as noise-worth-flagging, or every
    # single experiment would self-contaminate on its own state file.
    changed = [f for f in changed if f not in
              (".orchestrate_experiments.json", ".orchestrate_score_history.json")]
    contaminated, contamination_reason = check_contamination(changed)
    sha_now = git_util.current_sha(repo_root)

    card = build_scorecard(repo_root, python=python,
                           transcript_path=transcript_path,
                           interview_result_path=interview_result_path)
    exp.experiment_commit = sha_now or ""
    exp.experiment_score = _score_dict(card)
    exp.files_changed = changed
    exp.evaluation_command = "orchestrate score"

    delta = {}
    for key, before in exp.baseline_score.items():
        after = exp.experiment_score.get(key)
        if before is not None and after is not None:
            delta[key] = round(after - before, 4)
    exp.delta = delta

    regressions = []
    for sig_name, d in delta.items():
        if sig_name in ("weighted", exp.target_signal):
            continue
        if d <= -_REGRESSION_THRESHOLD:
            regressions.append(f"{sig_name} regressed {d:+.2f}")
    exp.regressions = regressions

    target_delta = delta.get(exp.target_signal)
    exp.actual_gain = target_delta

    if not exp.baseline_commit and not exp.baseline_score:
        exp.status = Status.ABORTED
        exp.decision = "ABORTED -- no baseline was ever captured"
    elif contaminated:
        exp.status = Status.INCONCLUSIVE
        exp.decision = f"INCONCLUSIVE -- EXPERIMENT CONTAMINATION: {contamination_reason}"
    elif target_delta is None:
        exp.status = Status.INCONCLUSIVE
        exp.decision = (f"INCONCLUSIVE -- target signal '{exp.target_signal}' "
                       "is not measurable in the baseline and/or current run")
    elif regressions:
        exp.status = Status.REJECTED
        exp.decision = (f"REJECTED -- target improved {target_delta:+.2f} but "
                       f"outweighed by regression(s): {'; '.join(regressions)}")
    elif target_delta > 0:
        exp.status = Status.ACCEPTED
        exp.decision = f"ACCEPTED -- target signal improved {target_delta:+.2f}, no material regression"
    else:
        exp.status = Status.REJECTED
        exp.decision = f"REJECTED -- no measured improvement (target delta {target_delta:+.2f})"

    exp.evidence.append(f"baseline={exp.baseline_score.get(exp.target_signal)} "
                        f"experiment={exp.experiment_score.get(exp.target_signal)} "
                        f"delta={target_delta}")
    if changed:
        exp.evidence.append(f"{len(changed)} file(s) changed: {', '.join(changed[:10])}")

    if memory is not None and exp.status in (Status.REJECTED, Status.ACCEPTED):
        _record_to_memory(memory, exp)

    store.add(exp)
    store.save()
    return exp


def _record_to_memory(memory: EngineeringMemory, exp: Experiment) -> None:
    key = f"experiment-{exp.id.lower()}"
    bm = Benchmark(
        metric=exp.target_signal,
        before=str(exp.baseline_score.get(exp.target_signal)),
        after=str(exp.experiment_score.get(exp.target_signal)),
        note=f"delta {exp.actual_gain:+.2f}" if exp.actual_gain is not None else "")
    entry = MemoryEntry(
        key=key, kind="decision", title=exp.title,
        problem=exp.hypothesis,
        chosen=exp.title if exp.status == Status.ACCEPTED else "",
        rejected=[exp.title] if exp.status == Status.REJECTED else [],
        evidence=exp.decision, benchmarks=[bm],
        reconsider_if=exp.reconsider_if or
                     "the measured regression/no-improvement condition above "
                     "no longer holds (e.g. the signal it hurt has since "
                     "been hardened, or a different implementation of the "
                     "same idea is being tried)",
        commit=exp.experiment_commit,
        files=exp.files_changed,
        tags=["experiment", exp.target_signal],
        status="rejected" if exp.status == Status.REJECTED else "accepted",
    )
    memory.add(entry)
    memory.save()
