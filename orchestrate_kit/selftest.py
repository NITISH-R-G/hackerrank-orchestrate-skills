"""Negative control for the evaluator itself.

    orchestrate selftest

Builds a minimal, healthy repository in a temp directory, confirms the
evaluator passes it, then injects one defect at a time and requires the
evaluator to CATCH each one.

Why this is a command and not a paragraph in the README: "we ran a negative
control" is exactly the kind of claim that decays. A harness that has never
failed has never been tested, and an audit suite is a harness. This makes the
claim re-runnable by anyone, in about four seconds.

Exit code 0 only if the baseline is clean AND every injected defect is caught.
A defect that slips through is reported by name -- that is the useful output,
not the score.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .evaluator import Evaluator, RepoContext, Severity
from .evaluator.plugins.generic import GenericPlugin
from .evaluator.plugins.orchestrate import OrchestratePlugin

MESSAGES = """message_id,sender_id,recipient_id,timestamp,message_text
msg_001,u_alice,u_me,2026-08-01T09:00:00,Are we still on for lunch?
msg_002,u_bank,u_me,2026-08-01T09:05:00,Your OTP is 449213. Do not share it.
msg_003,u_shop,u_me,2026-08-01T09:10:00,50% off everything. Unsubscribe here.
msg_004,u_bob,u_me,2026-08-01T09:15:00,Send me the UPI id and I will transfer
"""

HISTORY = """message_id,sender_id,recipient_id,timestamp,message_text
hist_001,u_alice,u_me,2026-07-30T12:00:00,Lunch on Friday works for me
hist_002,u_bank,u_me,2026-07-29T08:00:00,A login was detected on a new device
hist_003,u_shop,u_me,2026-07-28T18:00:00,New season arrivals are live
"""

OUTPUT = """message_id,action,message_type,reason,confidence,evidence_message_ids
msg_001,notify,personal,Known contact asking a direct question,0.86,hist_001
msg_002,notify,urgent,One-time passcode from a financial sender,0.91,hist_002
msg_003,digest,promotion,Bulk marketing with an unsubscribe footer,0.78,hist_003
msg_004,mute,scam,Unsolicited payment-credential request,0.88,none
"""

STATEMENT = """# Problem statement

Route each message to an action and a message_type.

action:       notify | digest | mute
message_type: personal | urgent | event | payment | business_update |
              promotion | greeting | forward | spam | scam | unknown

Output columns, in order: message_id, action, message_type, reason,
confidence, evidence_message_ids. Evidence ids are separated by ';'.
Write 'none' when there is no supporting evidence.
"""

MAIN = '''"""Minimal reference router for the selftest fixture."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / "dataset" / "output.csv"


def main() -> int:
    # The fixture regenerates a fixed artifact; the point of the selftest is
    # the AUDITS, not the routing.
    return 0 if ROWS.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


@dataclass
class Injection:
    name: str
    apply: Callable[[Path], None]
    expect: str          # substring that must appear in some finding title
    severity: Severity = Severity.BLOCKER


def _write_healthy(root: Path) -> None:
    (root / "dataset").mkdir(parents=True, exist_ok=True)
    (root / "code").mkdir(parents=True, exist_ok=True)
    (root / "dataset" / "messages.csv").write_text(MESSAGES, encoding="utf-8")
    (root / "dataset" / "message_history.csv").write_text(HISTORY, encoding="utf-8")
    (root / "dataset" / "output.csv").write_text(OUTPUT, encoding="utf-8")
    (root / "problem_statement.md").write_text(STATEMENT, encoding="utf-8")
    (root / "code" / "main.py").write_text(MAIN, encoding="utf-8")
    (root / "README.md").write_text("# fixture\n", encoding="utf-8")


def _sub(root: Path, old: str, new: str) -> None:
    p = root / "dataset" / "output.csv"
    text = p.read_text(encoding="utf-8")
    assert old in text, f"selftest fixture drift: {old!r} not in output.csv"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


INJECTIONS = [
    Injection("illegal action value",
              lambda r: _sub(r, "msg_001,notify,", "msg_001,ESCALATE,"),
              "action values legal"),
    Injection("illegal message_type value",
              lambda r: _sub(r, ",personal,", ",very_personal,"),
              "message_type values legal"),
    Injection("confidence out of range",
              lambda r: _sub(r, ",0.86,", ",1.7,"),
              "confidence numeric in [0,1]"),
    Injection("comma instead of the spec separator",
              lambda r: _sub(r, "0.91,hist_002", "0.91,\"hist_002,hist_001\""),
              "evidence separated"),
    Injection("hallucinated evidence id",
              lambda r: _sub(r, "hist_003", "hist_999"),
              "cited evidence id"),
    Injection("empty evidence written as blank, not 'none'",
              lambda r: _sub(r, ",0.88,none", ",0.88,"),
              "empty evidence"),
    Injection("row dropped from the artifact",
              lambda r: (r / "dataset" / "output.csv").write_text(
                  "\n".join(OUTPUT.splitlines()[:-1]) + "\n", encoding="utf-8"),
              "one row per input"),
    Injection("degenerate output: one action for every row",
              lambda r: (r / "dataset" / "output.csv").write_text(
                  OUTPUT.replace(",digest,", ",notify,").replace(",mute,", ",notify,"),
                  encoding="utf-8"),
              "action dominates", Severity.HIGH),
    Injection("hardcoded answer table keyed by dataset id",
              lambda r: (r / "code" / "main.py").write_text(
                  MAIN + '\nSPECIAL = {"msg_002": ("notify", "urgent")}\n',
                  encoding="utf-8"),
              "dataset ids", Severity.BLOCKER),
    Injection("dataset id compared in decision logic",
              lambda r: (r / "code" / "main.py").write_text(
                  MAIN + '\ndef patch(mid):\n    if mid == "msg_004":\n'
                         '        return "mute", "scam"\n',
                  encoding="utf-8"),
              "dataset ids", Severity.BLOCKER),
]

# A POSITIVE control alongside the negative one. An audit that fires on
# everything is as useless as one that fires on nothing, and this particular
# audit has a documented history of a confident BLOCKER on a healthy repo.
# None of these may fire.
BENIGN = [
    ("dataset id in a comment",
     '\n# msg_002 is the OTP row; kept here as documentation\n'),
    ("dataset id in a docstring",
     '\ndef helper():\n    """Example: msg_002 routes to notify."""\n'
     '    return 1\n'),
    ("single fixture assignment",
     '\nEXAMPLE_ID = "msg_002"\n'),
]


def run(verbose: bool = True) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="orchestrate-selftest-"))
    failures: list[str] = []
    try:
        base = tmp / "healthy"
        _write_healthy(base)

        def evaluate(root: Path):
            ctx = RepoContext(root=root, python=sys.executable, timeout_s=120)
            ev = Evaluator(ctx)
            ev.register(GenericPlugin())
            ev.register(OrchestratePlugin())
            return ev.run(only={"specification", "evidence", "evaluation",
                                "generalization"})

        # ---- 1. the baseline must be clean ---------------------------
        baseline = evaluate(base)
        titles = [f.title for r in baseline.results for f in r.findings]
        if baseline.blockers:
            failures.append(
                "BASELINE NOT CLEAN — the healthy fixture already trips: "
                + "; ".join(f.title for f in baseline.blockers))
        if verbose:
            print(f"  baseline           {'CLEAN' if not baseline.blockers else 'DIRTY'}"
                  f"   ({len(titles)} finding(s))")

        # ---- 2. each defect must be caught ---------------------------
        for inj in INJECTIONS:
            # Sanitize hard: ':' is legal in a POSIX filename and illegal in a
            # Windows one, and a selftest that only runs on one OS is not one.
            root = tmp / re.sub(r"[^a-z0-9]+", "_", inj.name.lower())
            shutil.copytree(base, root)
            inj.apply(root)
            result = evaluate(root)
            found = [f for r in result.results for f in r.findings
                     if inj.expect.lower() in f.title.lower()]
            caught = bool(found)
            if verbose:
                print(f"  {'CAUGHT ' if caught else 'MISSED '}"
                      f"{inj.name:<48} "
                      f"{found[0].severity.value if found else '-'}")
            if not caught:
                failures.append(f"NOT DETECTED: {inj.name} "
                                f"(expected a finding matching {inj.expect!r})")

        # ---- 3. benign code must NOT fire ----------------------------
        # The other half of the control. This audit has a documented history
        # of firing a confident BLOCKER on a healthy repository, so proving it
        # stays quiet matters as much as proving it fires.
        for label, snippet in BENIGN:
            root = tmp / ("benign_" + re.sub(r"[^a-z0-9]+", "_", label.lower()))
            shutil.copytree(base, root)
            (root / "code" / "main.py").write_text(MAIN + snippet, encoding="utf-8")
            result = evaluate(root)
            fired = [f for r in result.results for f in r.findings
                     if "dataset ids" in f.title.lower()]
            if verbose:
                print(f"  {'FALSE+ ' if fired else 'quiet  '}{label:<48} "
                      f"(must stay quiet)")
            if fired:
                failures.append(f"FALSE POSITIVE on benign code: {label} "
                                f"-> {fired[0].evidence.splitlines()[0]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"SELFTEST FAILED — {len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        print()
        print("  A missed injection means the audit for it is decorative. Fix")
        print("  the audit, not the fixture.")
        return 2

    print(f"SELFTEST PASSED — baseline clean, {len(INJECTIONS)}/{len(INJECTIONS)} "
          f"injected defects caught, {len(BENIGN)}/{len(BENIGN)} benign cases quiet.")
    print("  This is the negative control. Re-run it whenever an audit changes;")
    print("  a suite that has never failed has never been tested.")
    return 0
