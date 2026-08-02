"""Reporting. Evidence first, score last.

The score exists to be skimmed. The evidence exists to be acted on. If a reader
takes only the number and ignores the findings, the report has failed -- so
blockers are printed BEFORE the score, not after it.
"""

from __future__ import annotations

from .evaluator import Evaluation
from .memory import EngineeringMemory
from .plugin_api import Confidence, Severity

BADGE = {
    "READY": "READY",
    "READY WITH RESERVATIONS": "READY (with reservations)",
    "NOT READY": "NOT READY",
    "DO NOT SHIP": "DO NOT SHIP",
}
ORDER = [Severity.BLOCKER, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]


def render_markdown(ev: Evaluation, memory: EngineeringMemory | None = None) -> str:
    out: list[str] = []
    a = out.append

    a(f"# Evaluation — `{ev.repo.name}`\n")
    a(f"**Verdict: {BADGE.get(ev.verdict, ev.verdict)}**  ·  score {ev.overall}/100  ·  "
      f"plugins: {', '.join(ev.plugins)}\n")

    # ---- blockers first, deliberately above the score table -------------
    if ev.blockers:
        a("## Release blockers\n")
        a("These cap the verdict regardless of every other result.\n")
        for f in ev.blockers:
            a(f"### {f.title}")
            a(f"- **evidence** (`{f.confidence.value}`): `{_clip(f.evidence)}`")
            if f.detail:
                a(f"- {f.detail}")
            if f.remediation:
                a(f"- **fix**: {f.remediation}")
            if f.memory_key and memory and f.memory_key in memory.entries:
                m = memory.entries[f.memory_key]
                a(f"- **seen before** — `{m.key}` {m.title}")
                if m.chosen:
                    a(f"  - previously fixed by: {m.chosen}")
                if m.rejected:
                    a(f"  - previously rejected: {'; '.join(m.rejected)}")
            a("")
    else:
        a("## Release blockers\n\nNone.\n")

    # ---- categories -----------------------------------------------------
    a("## Categories\n")
    a("| category | score | audits | findings | blockers |")
    a("|---|---:|---:|---:|---:|")
    for name, c in sorted(ev.categories.items()):
        run = f"{c.audits_run}" + (f" (+{c.audits_skipped} skipped)" if c.audits_skipped else "")
        a(f"| {name} | {c.score} | {run} | {len(c.findings)} | {c.blockers} |")
    a("")

    # ---- findings by severity -------------------------------------------
    rest = [f for r in ev.results for f in r.findings if f.severity is not Severity.BLOCKER]
    if rest:
        a("## Findings\n")
        for sev in ORDER[1:]:
            group = [f for f in rest if f.severity is sev]
            if not group:
                continue
            a(f"### {sev.value.upper()} ({len(group)})\n")
            for f in group:
                a(f"- **{f.title}** — `{f.confidence.value}`")
                a(f"  - evidence: `{_clip(f.evidence, 240)}`")
                if f.remediation:
                    a(f"  - fix: {f.remediation}")
            a("")

    # ---- what NOT to change ---------------------------------------------
    if memory:
        rej = memory.rejections()
        if rej:
            a("## Do NOT change these\n")
            a("Previously measured and rejected. Re-proposing one of these "
              "without new evidence is a regression, not an improvement.\n")
            a("| idea | why it was rejected | evidence |")
            a("|---|---|---|")
            for m in rej:
                a(f"| {m.title} | {m.root_cause or m.problem} | {_clip(m.evidence, 90)} |")
            a("")

    # ---- honest unknowns -------------------------------------------------
    if ev.unknowns:
        a("## Unknown — could not be determined\n")
        a("Reported rather than assumed either way.\n")
        for u in ev.unknowns:
            a(f"- {u}")
        a("")

    a("---")
    a(f"_Audits run: {sum(1 for r in ev.results if not r.skipped)} · "
      f"skipped: {sum(1 for r in ev.results if r.skipped)} · "
      f"total time {sum(r.duration_s for r in ev.results):.1f}s_")
    return "\n".join(out)


def render_terminal(ev: Evaluation) -> str:
    lines = [f"{ev.verdict}   score {ev.overall}/100   [{', '.join(ev.plugins)}]", ""]
    for name, c in sorted(ev.categories.items()):
        flag = "!" if c.blockers else " "
        bar = "#" * (c.score // 10) + "." * (10 - c.score // 10)
        lines.append(f" {flag} {name:<16} {bar} {c.score:>3}  "
                     f"({c.audits_run} audits, {len(c.findings)} findings)")
    if ev.blockers:
        lines += ["", "BLOCKERS:"]
        lines += [f"  - {f.title}" for f in ev.blockers]
    return "\n".join(lines)


def _clip(text: str, n: int = 400) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + " ..."
