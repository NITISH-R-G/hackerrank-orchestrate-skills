"""Pareto frontier over completed experiments' measured deltas.

Compares only signals BOTH experiments actually measured -- an
experiment cannot be said to dominate another on a dimension neither of
them has real data for. An experiment with strictly fewer comparable
dimensions than another is never treated as dominating it (missing data
is not evidence of superiority)."""

from __future__ import annotations

from .model import Experiment, Status

_COMPARE_SIGNALS = ("code", "output", "transcript", "interview")


def _comparable_deltas(exp: Experiment) -> dict[str, float]:
    return {k: v for k, v in exp.delta.items() if k in _COMPARE_SIGNALS}


def dominates(a: Experiment, b: Experiment) -> bool:
    """True if `a` is at least as good as `b` on every dimension they both
    measured, and strictly better on at least one. Requires at least one
    shared measured dimension -- otherwise there's nothing to compare."""
    da, db = _comparable_deltas(a), _comparable_deltas(b)
    shared = set(da) & set(db)
    if not shared:
        return False
    at_least_as_good = all(da[k] >= db[k] for k in shared)
    strictly_better = any(da[k] > db[k] for k in shared)
    return at_least_as_good and strictly_better


def frontier(experiments: list[Experiment]) -> list[Experiment]:
    """Non-dominated set among COMPLETED-or-later experiments with at
    least one measured delta. Rejected/inconclusive experiments are
    eligible too -- the frontier is about measured tradeoffs, not final
    verdicts; a rejected experiment can still be Pareto-informative."""
    candidates = [e for e in experiments
                 if e.status in Status.TERMINAL and _comparable_deltas(e)]
    return [e for e in candidates
           if not any(dominates(other, e) for other in candidates if other is not e)]
