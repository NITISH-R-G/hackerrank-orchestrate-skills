"""AI Judge Interview signal.

Cannot be computed from static analysis -- an interview is a live,
adaptive conversation, and `orchestrate interview` is deliberately
interactive (reads real answers from stdin). There is no honest way to
produce this number without a completed session, so this reads a result
saved by `orchestrate interview --save <path>` and reports UNKNOWN if none
exists. No score is invented to fill the gap."""

from __future__ import annotations

import json
from pathlib import Path

from .signals import Confidence, Finding, SignalScore


def score_interview(result_path: Path | None) -> SignalScore:
    if result_path is None or not result_path.exists():
        return SignalScore("interview", "AI Judge Interview", None, 0.30,
                           Confidence.UNKNOWN,
                           notes=["no saved interview result -- run "
                                  "`orchestrate interview --save <path>` "
                                  "and pass --interview-result <path>"])

    try:
        record = json.loads(result_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return SignalScore("interview", "AI Judge Interview", None, 0.30,
                           Confidence.UNKNOWN,
                           notes=[f"could not read {result_path}"])

    score = record.get("score")
    if score is None:
        return SignalScore("interview", "AI Judge Interview", None, 0.30,
                           Confidence.UNKNOWN,
                           notes=["saved result has no 'score' field"])

    findings = []
    answered = record.get("questions_answered", 0)
    requested = record.get("questions_requested", 0)
    if requested and answered < requested:
        findings.append(Finding(
            "session ended early",
            f"{answered}/{requested} questions answered"))

    notes = [f"from a saved {record.get('persona', '?')} / "
            f"{record.get('difficulty', '?')} session, "
            f"saved {record.get('saved_at', 'at an unknown time')} -- "
            "this is a self-practice score, not the real HackerRank "
            "judge's score"]

    return SignalScore("interview", "AI Judge Interview", float(score), 0.30,
                       Confidence.HEURISTIC, findings, notes)
