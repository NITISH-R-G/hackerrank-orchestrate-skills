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
    score = max(0.0, score)

    notes = [f"{sum(1 for r in results if not r.skipped)}/{len(results)} "
            f"underlying audits ran (spec conformance, evidence quality, "
            f"output sanity, label leakage)"]

    return SignalScore("output", "Output CSV", score, 0.30,
                       Confidence.MEASURED, findings, notes)
