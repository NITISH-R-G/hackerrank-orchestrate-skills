"""Output CSV scorer -- wraps the evaluator's existing Orchestrate-domain
audits (spec conformance, evidence quality, label leakage, output sanity)
into a single 0-100 signal.

Deliberately NOT inventing sub-weights HackerRank never published.
The article states Output CSV is graded on status/type/area accuracy
against a hidden golden set plus a safety score for adversarial input --
none of that is independently checkable offline (no golden set exists
locally). What IS checkable offline, and what actually predicts whether a
submission generalizes to a hidden set, is exactly what this project's own
Engineering Memory already learned the hard way building a real
submission: spec conformance, hallucinated/duplicate evidence, and
dataset-coupling (leakage). Scored by the same penalty mechanism
orchestrate_kit's own Evaluator already uses -- this isn't a second,
different scoring philosophy, it's the existing one applied and reported
as one of the four signals.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from ..evaluator.plugin_api import RepoContext, Severity
from ..evaluator.plugins.orchestrate import (
    audit_evidence_quality,
    audit_output_sanity,
    audit_spec_conformance,
)
from ..evaluator.plugins.orchestrate.leakage import audit_label_leakage
from .signals import Confidence, Finding, SignalScore

_PENALTY = {Severity.BLOCKER: 100, Severity.HIGH: 25, Severity.MEDIUM: 10,
           Severity.LOW: 3, Severity.INFO: 0}


JUSTIFICATION_COLUMNS = (
    "reason", "justification", "claim_status_justification", "decision_explanation",
)


def _justification_finding(ctx: RepoContext) -> tuple[Finding | None, float]:
    """Per-row justification quality. Confirmed gap in the shared
    evaluator: `audit_output_sanity` only flags reasons that are IDENTICAL
    across every row; nothing checks whether an individual row's reason is
    blank. HackerRank's own writeup states a correct action with an empty
    or contradictory justification must not be treated the same as one
    with a grounded justification -- so this scorer adds that check itself
    rather than waiting on a shared-plugin change. Returns
    (finding-or-None, penalty-points)."""
    text = ctx.read("dataset/output.csv")
    if not text:
        return None, 0.0
    rows = list(csv.DictReader(io.StringIO(text)))
    # Justification column differs by round: May 'reason'-style, June
    # 'claim_status_justification', Sept 'decision_explanation'. Use the first
    # one present; a round with none of them is reported as unchecked.
    column = next((c for c in JUSTIFICATION_COLUMNS if rows and c in rows[0]), None)
    if column is None:
        return None, 0.0
    blank = sum(1 for r in rows if not (r.get(column) or "").strip())
    if not blank:
        return None, 0.0
    fraction = blank / len(rows)
    penalty = min(60.0, 100.0 * fraction)
    return Finding(
        "blank justification",
        f"{blank}/{len(rows)} row(s) have an empty '{column}' field -- a "
        "correct action with no justification is not equivalent to one "
        "with a grounded justification"), penalty

GENERIC_REASONS = {
    "n/a", "na", "none", "ok", "okay", "unknown", "as per policy", "per policy",
    "no reason", "see above", "-", "tbd", "todo",
}
MIN_WORDS = 5
# HackerRank's writeup: a correct action with a generic or contradicting
# justification is capped near 70. A capped row loses at least 30 of 100
# points, so a file with a fraction f of weak rows loses at least 30 * f.
WEAK_ROW_CAP_LOSS = 30.0
# Phrases that argue FOR the opposite of the row's action. Deliberately
# phrase-level: a bare word like "urgent" often describes content (a scam asks
# for "urgent" OTP) and must not count as a contradiction.
_CONTRADICTIONS = {
    "mute": ("should notify", "notify the user now", "deserves immediate", "needs immediate attention"),
    "notify": ("should be muted", "should mute", "mute this", "safe to mute"),
}


def _weak_justification_finding(ctx: RepoContext) -> tuple[Finding | None, float]:
    """Rows whose justification is generic, or contradicts the row's action,
    are capped at 70 by the rubric. Heuristic: a reason under MIN_WORDS words,
    a placeholder phrase, or a reason that argues against its own action word
    (only checked when an 'action' column exists). Penalty = 30 * fraction of
    weak rows. Blank rows are handled by _justification_finding instead."""
    text = ctx.read("dataset/output.csv")
    if not text:
        return None, 0.0
    rows = list(csv.DictReader(io.StringIO(text)))
    column = next((c for c in JUSTIFICATION_COLUMNS if rows and c in rows[0]), None)
    if column is None:
        return None, 0.0
    weak = []
    for r in rows:
        reason = (r.get(column) or "").strip()
        if not reason:
            continue
        lowered = reason.lower().strip(" .")
        contradicts = False
        action = (r.get("action") or "").strip().lower()
        for word in _CONTRADICTIONS.get(action, ()):
            if word in lowered:
                contradicts = True
        if len(reason.split()) < MIN_WORDS or lowered in GENERIC_REASONS or contradicts:
            weak.append(r.get("message_id") or r.get("request_id") or r.get("user_id") or "?")
    if not weak:
        return None, 0.0
    fraction = len(weak) / len(rows)
    return Finding(
        "generic or contradicting justification",
        f"{len(weak)}/{len(rows)} row(s) have a justification that is too short, "
        f"generic, or argues against its own action (e.g. {', '.join(weak[:3])}); "
        "rubric caps these rows near 70"), WEAK_ROW_CAP_LOSS * fraction


def score_output(repo_root: Path, python: str = "python") -> SignalScore:
    ctx = RepoContext(root=repo_root, python=python)

    if not ctx.exists("dataset/output.csv"):
        return SignalScore("output", "Output CSV", None, 0.30,
                           Confidence.UNKNOWN,
                           notes=["dataset/output.csv not found under this path"])

    results = [audit_spec_conformance(ctx), audit_evidence_quality(ctx),
              audit_output_sanity(ctx), audit_label_leakage(ctx)]

    score = 100.0
    findings: list[Finding] = []
    for r in results:
        if r.skipped:
            findings.append(Finding(f"{r.audit}: could not run",
                                    r.skipped))
            continue
        for f in r.findings:
            score -= _PENALTY.get(f.severity, 0)
            if f.severity in (Severity.BLOCKER, Severity.HIGH):
                findings.append(Finding(f.title, f.evidence[:200]))

    just_finding, just_penalty = _justification_finding(ctx)
    if just_finding:
        score -= just_penalty
        findings.append(just_finding)
    weak_finding, weak_penalty = _weak_justification_finding(ctx)
    if weak_finding:
        score -= weak_penalty
        findings.append(weak_finding)

    score = max(0.0, score)

    notes = [f"{sum(1 for r in results if not r.skipped)}/{len(results)} "
            f"underlying audits ran (spec conformance, evidence quality, "
            f"output sanity, label leakage)"]

    return SignalScore("output", "Output CSV", score, 0.30,
                       Confidence.MEASURED, findings, notes)
