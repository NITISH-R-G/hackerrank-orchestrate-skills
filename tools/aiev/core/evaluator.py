"""The runner: discover plugins, execute audits, aggregate, score.

Scoring principle: a score is a SUMMARY of findings, never a substitute for
them. Any category containing a BLOCKER caps the overall verdict regardless of
how green everything else is -- an average that lets 14 passes outvote one
release blocker is worse than no score at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .memory import EngineeringMemory
from .plugin_api import Audit, AuditResult, Confidence, Finding, Plugin, RepoContext, Severity

# What one finding costs its category, by severity.
PENALTY = {
    Severity.BLOCKER: 100,
    Severity.HIGH: 25,
    Severity.MEDIUM: 10,
    Severity.LOW: 3,
    Severity.INFO: 0,
}

# An INFERRED finding is discounted: it is reasoning, not measurement.
CONFIDENCE_WEIGHT = {
    Confidence.MEASURED: 1.0,
    Confidence.OBSERVED: 1.0,
    Confidence.INFERRED: 0.5,
    Confidence.UNKNOWN: 0.25,
}


@dataclass
class CategoryScore:
    category: str
    score: int
    blockers: int
    findings: list[Finding] = field(default_factory=list)
    audits_run: int = 0
    audits_skipped: int = 0


@dataclass
class Evaluation:
    repo: Path
    plugins: list[str]
    results: list[AuditResult]
    categories: dict[str, CategoryScore]
    overall: int
    verdict: str
    unknowns: list[str] = field(default_factory=list)

    @property
    def blockers(self) -> list[Finding]:
        return [f for r in self.results for f in r.findings
                if f.severity is Severity.BLOCKER]


class Evaluator:
    def __init__(self, ctx: RepoContext, memory: EngineeringMemory | None = None) -> None:
        self.ctx = ctx
        self.memory = memory
        self.plugins: list[Plugin] = []

    def register(self, plugin: Plugin) -> None:
        self.plugins.append(plugin)

    def applicable(self) -> list[Plugin]:
        out = []
        for p in self.plugins:
            try:
                if p.detect(self.ctx):
                    out.append(p)
            except Exception:  # noqa: BLE001 -- a broken detector must not abort
                continue
        return out

    def run(self, only: set[str] | None = None) -> Evaluation:
        plugins = self.applicable()
        results: list[AuditResult] = []
        for plugin in plugins:
            for audit in plugin.audits():
                if only and audit.category not in only:
                    continue
                res = audit.run(self.ctx)
                if self.memory:
                    self._attach_memory(res)
                results.append(res)
        return self._aggregate(results, [p.name for p in plugins])

    # ------------------------------------------------------------------
    def _attach_memory(self, res: AuditResult) -> None:
        """Link each finding to prior art, so the report can say 'seen before'."""
        assert self.memory is not None
        for f in res.findings:
            if f.memory_key:
                continue
            prior = self.memory.recall(f.title, limit=1)
            if prior:
                f.memory_key = prior[0].key

    def _aggregate(self, results: list[AuditResult], plugin_names: list[str]) -> Evaluation:
        cats: dict[str, CategoryScore] = {}
        for r in results:
            c = cats.setdefault(r.category, CategoryScore(r.category, 100, 0))
            if r.skipped:
                c.audits_skipped += 1
                continue
            c.audits_run += 1
            for f in r.findings:
                c.findings.append(f)
                if f.severity is Severity.BLOCKER:
                    c.blockers += 1
                cost = PENALTY[f.severity] * CONFIDENCE_WEIGHT[f.confidence]
                c.score -= int(round(cost))
        for c in cats.values():
            c.score = max(0, min(100, c.score))

        scored = [c for c in cats.values() if c.audits_run]
        overall = int(round(sum(c.score for c in scored) / len(scored))) if scored else 0
        total_blockers = sum(c.blockers for c in cats.values())

        if total_blockers:
            verdict = "DO NOT SHIP"
            overall = min(overall, 49)
        elif overall >= 90:
            verdict = "READY"
        elif overall >= 70:
            verdict = "READY WITH RESERVATIONS"
        else:
            verdict = "NOT READY"

        unknowns = [f.title for r in results for f in r.findings
                    if f.confidence is Confidence.UNKNOWN]
        return Evaluation(self.ctx.root, plugin_names, results, cats,
                          overall, verdict, unknowns)
