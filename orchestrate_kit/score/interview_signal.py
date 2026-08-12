"""AI Judge Interview signal.

Cannot be computed from static analysis -- an interview is a live,
adaptive conversation, and `orchestrate interview` is deliberately
interactive (reads real answers from stdin). There is no honest way to
produce this number without a completed session, so this reads a result
saved by `orchestrate interview --save <path>` and reports UNKNOWN if none
exists. No score is invented to fill the gap.

KNOWN, STATED LIMIT: the underlying analyser (judge/scoring.py) grades the
SHAPE of an answer -- numbers, evidence verbs, named alternatives -- not
its truth. Confirmed by direct test: a fluent, specific, well-evidenced
description of a feature that was never built currently outscores an
honest "I don't know" (66 vs 25 in the adversarial battery). Text alone
cannot fix this -- there is no way to tell a true claim from a false one
by its shape. What CAN fix it is checking the claim against the actual
code: if the saved session's answers name a checkable technique (BM25,
reranker, RAG, ...) that the code doesn't contain, or a constant
(BM25 k1/b) that contradicts the code's actual value, that is docked here
as an unsupported or contradicted claim. This does not make the scorer
omniscient -- a hallucination about something not on the checkable list
still isn't caught -- but it closes the exact case the audit named."""

from __future__ import annotations

import json
from pathlib import Path

from .consistency import check_code_vs_interview
from .signals import Confidence, Finding, SignalScore

# A caught factual contradiction (wrong BM25 constant, claiming a
# technique the code doesn't have) is a credibility failure, not a minor
# deduction -- in a real interview, being confidently wrong about a
# checkable detail reads worse than admitting you don't know. Modeled as
# a hard CAP, not a flat subtraction: a flat -30 still let a fluent,
# maximally-specific hallucination (66) beat honest uncertainty (25) --
# confirmed by direct test. A cap guarantees a caught contradiction can
# never coast on the fluency that produced the high raw score.
_CONTRADICTED_CLAIM_CAP = 15.0
_UNSUPPORTED_CLAIM_CAP = 55.0


def score_interview(result_path: Path | None,
                    repo_root: Path | None = None) -> SignalScore:
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
    score = float(score)

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
            "judge's score",
            "known limitation: this scorer grades answer SHAPE, not "
            "truth, except where the Code <-> Interview consistency "
            "check below can verify a specific claim"]

    if repo_root is not None and repo_root.exists():
        answers = [a.get("text", "") for a in record.get("answers", [])]
        if answers:
            check = check_code_vs_interview(repo_root, answers)
            if check.verdict == "FAIL":
                score = min(score, _CONTRADICTED_CLAIM_CAP)
                findings.append(Finding(
                    "interview claim contradicts code", check.detail))
            elif check.verdict == "WARNING":
                score = min(score, _UNSUPPORTED_CLAIM_CAP)
                findings.append(Finding(
                    "interview claim not corroborated in code", check.detail))
            notes.append(f"Code <-> Interview consistency: {check.verdict}")
        else:
            notes.append("saved result has no answer text -- re-run with "
                         "the current `interview --save` to enable "
                         "Code <-> Interview consistency checking")

    return SignalScore("interview", "AI Judge Interview", score, 0.30,
                       Confidence.HEURISTIC, findings, notes)
