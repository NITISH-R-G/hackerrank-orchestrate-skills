"""HackerRank Orchestrate plugin — the first complete case study.

Everything competition-specific lives here. The core does not import it and does
not know it exists beyond the plugin list.

`detect()` keys on the dataset shape rather than on a repo name, so it works for
any Orchestrate season: swap the CSVs, the plugin still applies.
"""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

from ...core.plugin_api import (
    AuditResult,
    Confidence,
    Finding,
    RepoContext,
    Severity,
    SimpleAudit,
)
from ..generic import audit_artifact_freshness, audit_determinism
from .leakage import audit_label_leakage

# Transcribed from problem_statement.md, NOT imported from the target's code.
# Importing the target's schema would only prove the code agrees with itself.
SPEC_COLUMNS = ["message_id", "action", "message_type", "reason",
                "confidence", "evidence_message_ids"]
SPEC_ACTIONS = {"notify", "digest", "mute"}
SPEC_TYPES = {"personal", "urgent", "event", "payment", "business_update",
              "promotion", "greeting", "forward", "spam", "scam", "unknown"}
SPEC_SEPARATOR = ";"
SPEC_NO_EVIDENCE = "none"


def _rows(ctx: RepoContext, rel: str) -> list[dict]:
    text = ctx.read(rel)
    if not text:
        return []
    return list(csv.DictReader(io.StringIO(text)))


# --------------------------------------------------------------------------
def audit_spec_conformance(ctx: RepoContext) -> AuditResult:
    res = AuditResult("spec-conformance", "specification", True)
    out = _rows(ctx, "dataset/output.csv")
    msgs = _rows(ctx, "dataset/messages.csv")
    if not out or not msgs:
        res.skipped = "dataset/output.csv or messages.csv not readable"
        return res

    header = list(out[0].keys())
    checks: list[tuple[str, bool, str]] = [
        ("columns exact and ordered", header == SPEC_COLUMNS, str(header)),
        ("one row per input", len(out) == len(msgs), f"{len(out)} vs {len(msgs)}"),
        ("same ids, same order",
         [r["message_id"] for r in out] == [m["message_id"] for m in msgs], ""),
        ("no duplicate ids",
         len({r["message_id"] for r in out}) == len(out), ""),
    ]
    bad_actions = sorted({r["action"] for r in out} - SPEC_ACTIONS)
    checks.append(("action values legal", not bad_actions, str(bad_actions)))
    bad_types = sorted({r["message_type"] for r in out} - SPEC_TYPES)
    checks.append(("message_type values legal", not bad_types, str(bad_types)))

    bad_conf = []
    for r in out:
        try:
            v = float(r["confidence"])
            if not 0.0 <= v <= 1.0:
                bad_conf.append(r["message_id"])
        except (TypeError, ValueError):
            bad_conf.append(r["message_id"])
    checks.append(("confidence numeric in [0,1]", not bad_conf, str(bad_conf[:5])))

    comma = [r["message_id"] for r in out if "," in r["evidence_message_ids"]]
    checks.append((f"evidence separated by '{SPEC_SEPARATOR}'", not comma, str(comma[:5])))
    blank = [r["message_id"] for r in out if not r["evidence_message_ids"].strip()]
    checks.append((f"empty evidence written as '{SPEC_NO_EVIDENCE}'", not blank, str(blank[:5])))

    hist = {h["message_id"] for h in _rows(ctx, "dataset/message_history.csv")}
    cited = [i for r in out if r["evidence_message_ids"] != SPEC_NO_EVIDENCE
             for i in r["evidence_message_ids"].split(SPEC_SEPARATOR)]
    unknown = sorted(set(cited) - hist) if hist else []
    checks.append(("every cited evidence id exists", not unknown, str(unknown[:5])))

    for label, ok, detail in checks:
        if not ok:
            res.passed = False
            res.findings.append(Finding(
                f"spec violation: {label}", Severity.BLOCKER, Confidence.MEASURED,
                evidence=detail or "see problem_statement.md",
                remediation="The output contract is graded literally.",
            ))
    res.metrics = {"rows": len(out), "types_used": len({r["message_type"] for r in out}),
                   "evidence_none": sum(1 for r in out
                                        if r["evidence_message_ids"] == SPEC_NO_EVIDENCE)}
    return res


# ---------------------------------------------------------------------
def audit_output_sanity(ctx: RepoContext) -> AuditResult:
    """Distribution smells that suggest a degenerate or truncated run."""
    res = AuditResult("output-sanity", "evaluation", True)
    out = _rows(ctx, "dataset/output.csv")
    if not out:
        res.skipped = "no output.csv"
        return res
    from collections import Counter
    acts = Counter(r["action"] for r in out)
    types = Counter(r["message_type"] for r in out)
    reasons = {r["reason"] for r in out}
    res.metrics = {"actions": str(dict(acts)), "distinct_types": len(types),
                   "distinct_reasons": len(reasons)}

    top_share = acts.most_common(1)[0][1] / len(out)
    if top_share > 0.80:
        res.findings.append(Finding(
            "one action dominates the output", Severity.HIGH, Confidence.MEASURED,
            evidence=f"{acts.most_common(1)[0][0]} = {top_share:.0%} of rows",
            detail="A near-constant predictor can score well on an imbalanced "
                   "set while learning nothing.",
        ))
    if len(types) <= 2:
        res.findings.append(Finding(
            "message_type is nearly constant", Severity.HIGH, Confidence.MEASURED,
            evidence=f"only {len(types)} distinct values: {list(types)}"))
    if len(reasons) == 1:
        res.findings.append(Finding(
            "every row has an identical reason", Severity.MEDIUM, Confidence.MEASURED,
            evidence=f"reason={list(reasons)[0][:60]!r}",
            detail="`reason` is an explicitly scored dimension."))
    return res


# --------------------------------------------------------------------------
def audit_evidence_quality(ctx: RepoContext) -> AuditResult:
    """Hallucinated / self-referencing / duplicated evidence ids."""
    res = AuditResult("evidence-quality", "evidence", True)
    out = _rows(ctx, "dataset/output.csv")
    hist = {h["message_id"] for h in _rows(ctx, "dataset/message_history.csv")}
    if not out or not hist:
        res.skipped = "output.csv or message_history.csv unavailable"
        return res
    hallucinated = dup = self_ref = 0
    for r in out:
        raw = r["evidence_message_ids"]
        if raw == SPEC_NO_EVIDENCE:
            continue
        ids = raw.split(SPEC_SEPARATOR)
        if len(ids) != len(set(ids)):
            dup += 1
        for i in ids:
            if i not in hist:
                hallucinated += 1
            if i == r["message_id"]:
                self_ref += 1
    cited = sum(1 for r in out if r["evidence_message_ids"] != SPEC_NO_EVIDENCE)
    res.metrics = {"rows_citing_evidence": cited, "hallucinated": hallucinated,
                   "duplicates": dup, "self_references": self_ref}
    for n, label, sev in ((hallucinated, "hallucinated evidence ids", Severity.BLOCKER),
                          (self_ref, "self-referencing evidence", Severity.HIGH),
                          (dup, "duplicate ids within one cell", Severity.MEDIUM)):
        if n:
            res.passed = False
            res.findings.append(Finding(
                f"{label}: {n}", sev, Confidence.MEASURED,
                evidence=f"{n} occurrence(s) across {len(out)} rows"))
    return res


# --------------------------------------------------------------------------
def audit_artifact(ctx: RepoContext) -> AuditResult:
    return audit_artifact_freshness(
        ctx, artifact="dataset/output.csv",
        command=[ctx.python, "code/main.py"])


def audit_det(ctx: RepoContext) -> AuditResult:
    return audit_determinism(
        ctx, command=[ctx.python, "code/main.py"],
        artifact="dataset/output.csv", runs=3)


class OrchestratePlugin:
    name = "hackerrank-orchestrate"
    description = "Message-routing submission: spec, evidence, leakage, artifact"

    def audits(self):
        return [
            SimpleAudit("spec-conformance", "specification", audit_spec_conformance),
            SimpleAudit("label-leakage", "generalization", audit_label_leakage),
            SimpleAudit("output-sanity", "evaluation", audit_output_sanity),
            SimpleAudit("evidence-quality", "evidence", audit_evidence_quality),
            SimpleAudit("artifact-freshness", "release", audit_artifact),
            SimpleAudit("determinism", "determinism", audit_det),
        ]

    def detect(self, ctx: RepoContext) -> bool:
        """Shape-based, not name-based, so it works for any season."""
        return ctx.exists("dataset/messages.csv") and ctx.exists("problem_statement.md")
