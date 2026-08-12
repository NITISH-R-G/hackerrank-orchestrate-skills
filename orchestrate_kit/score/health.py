"""`orchestrate score --audit` -- the score engine tests ITSELF.

Every line below is produced by actually running the adversarial checks
live against synthetic fixtures inside this function, every invocation --
never a hardcoded PASS/FAIL string. If a category here says PASS, it is
because a real fixture was scored twice moments ago and the result
behaved as required. This is the same discipline as
`orchestrate selftest` (inject a defect, prove the evaluator catches it)
applied to the score engine that Phase 2 will depend on.

If this reports NEEDS WORK, the printed reason names the category that
failed and DOES NOT recommend using the score engine to drive experiments
until it is fixed.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .code_zip import score_code
from .consistency import check_code_vs_interview, check_code_vs_output
from .interview_signal import score_interview
from .output_csv import score_output
from .signals import OFFICIAL_WEIGHTS, ScoreCard, SignalScore, Confidence
from .transcript_signal import score_transcript


def _check_official_weights() -> tuple[bool, str]:
    expected = {"code": 0.30, "output": 0.30, "interview": 0.30, "transcript": 0.10}
    if OFFICIAL_WEIGHTS != expected:
        return False, f"OFFICIAL_WEIGHTS is {OFFICIAL_WEIGHTS}, expected {expected}"
    if abs(sum(OFFICIAL_WEIGHTS.values()) - 1.0) > 1e-9:
        return False, f"weights sum to {sum(OFFICIAL_WEIGHTS.values())}, not 1.0"
    return True, "code/output/interview 30% each, transcript 10%, sums to 1.0"


_KEYWORD_STUFF_SRC = '''
class AgentRolePersonaHandler:
    """agent role persona tool dispatch route handler multi-agent RAG guardrail"""
    pass
SYSTEM_PROMPT = """
agent tool loop guardrail multi-agent RAG structured output retry
max_retries tenacity max_iterations MAX_TURNS validate schema.validate
refuse reject cannot BaseModel response_format json_schema pydantic
"""
def tool_dispatch_route_handler():
    pass
'''

_LEGIT_SRC = '''
def classify(ticket: dict) -> dict:
    if ticket["amount"] > 10000:
        return {"action": "notify"}
    return {"action": "digest"}
'''


def _check_code_gaming_resistance() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        d1, d2 = Path(d1), Path(d2)
        (d1 / "a.py").write_text(_KEYWORD_STUFF_SRC, encoding="utf-8")
        (d2 / "a.py").write_text(_LEGIT_SRC, encoding="utf-8")
        stuffed = score_code(d1)
        legit = score_code(d2)
        if stuffed.estimated_score >= legit.estimated_score:
            return False, (f"keyword-stuffed fixture scored "
                          f"{stuffed.estimated_score:.1f}, legit "
                          f"keyword-free fixture scored "
                          f"{legit.estimated_score:.1f} -- stuffing wins")
        return True, (f"stuffed={stuffed.estimated_score:.1f} < "
                     f"legit={legit.estimated_score:.1f}")


def _write_output_fixture(root: Path, reasons: list[str]) -> None:
    (root / "dataset").mkdir(parents=True, exist_ok=True)
    out = ["message_id,action,message_type,reason,confidence,evidence_message_ids"]
    hist = ["message_id,message"]
    for i, r in enumerate(reasons):
        out.append(f'M{i},notify,personal,"{r}",0.9,none')
        hist.append(f"M{i},hey are you free? {i}")
    (root / "dataset" / "output.csv").write_text("\n".join(out) + "\n",
                                                  encoding="utf-8")
    (root / "dataset" / "message_history.csv").write_text(
        "\n".join(hist) + "\n", encoding="utf-8")


def _check_output_discrimination() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        d1, d2 = Path(d1), Path(d2)
        _write_output_fixture(d1, [f"a grounded reason, message {i}"
                                   for i in range(10)])
        _write_output_fixture(d2, [""] * 10)
        grounded = score_output(d1)
        blank = score_output(d2)
        if blank.estimated_score >= grounded.estimated_score:
            return False, (f"blank-justification fixture "
                          f"({blank.estimated_score:.1f}) did not score "
                          f"below grounded ({grounded.estimated_score:.1f})")
        return True, (f"grounded={grounded.estimated_score:.1f} > "
                     f"blank={blank.estimated_score:.1f}")


def _check_transcript_discrimination() -> tuple[bool, str]:
    stuffed = ("We measured this. We rejected that. Direction architecture "
              "ownership. Technical specificity constraint. Iteration "
              "verification. Safety edge case quality. " * 15)
    real = ("I chose BM25 over dense embeddings because the sandbox "
           "blocked model downloads; I verified this by timing a cold "
           "start that failed after 30s. I measured precision at 92% "
           "against 40 hand-labeled tickets.")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        s = d / "stuffed.txt"; s.write_text(stuffed, encoding="utf-8")
        r = d / "real.txt"; r.write_text(real, encoding="utf-8")
        stuffed_score = score_transcript(s)
        real_score = score_transcript(r)
        if stuffed_score.estimated_score >= real_score.estimated_score:
            return False, (f"keyword-stuffed transcript "
                          f"({stuffed_score.estimated_score:.1f}) did not "
                          f"score below real evidenced text "
                          f"({real_score.estimated_score:.1f})")
        return True, (f"real={real_score.estimated_score:.1f} > "
                     f"stuffed={stuffed_score.estimated_score:.1f}")


def _check_interview_discrimination() -> tuple[bool, str]:
    """Scoped claim: honest uncertainty beats a CAUGHT factual
    contradiction on a checkable claim (BM25 constants). This is NOT a
    claim that all hallucination is caught -- an unchecked claim (no
    matching code evidence to compare against) still is not detected.
    That residual limitation is real and stated in interview_signal.py's
    docstring, not hidden here."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "search.py").write_text("BM25_K1 = 1.2\nBM25_B = 0.9\n",
                                     encoding="utf-8")
        hallucinated = d / "h.json"
        hallucinated.write_text(json.dumps({
            "score": 66, "questions_answered": 1, "questions_requested": 1,
            "answers": [{"topic": "retrieval", "text":
                "We implemented BM25 with k1=1.5, b=0.75, measured nDCG@10 "
                "at 0.89 after ablating the baseline."}]}), encoding="utf-8")
        honest = d / "o.json"
        honest.write_text(json.dumps({
            "score": 25, "questions_answered": 1, "questions_requested": 1,
            "answers": [{"topic": "retrieval", "text":
                "I do not have a strong retrieval component and have not "
                "measured its recall; that is unverified."}]}), encoding="utf-8")
        h = score_interview(hallucinated, repo_root=d)
        o = score_interview(honest, repo_root=d)
        if o.estimated_score <= h.estimated_score:
            return False, (f"honest uncertainty ({o.estimated_score:.1f}) "
                          f"did not beat a caught factual contradiction "
                          f"({h.estimated_score:.1f})")
        return True, (f"honest={o.estimated_score:.1f} > "
                     f"caught-hallucination={h.estimated_score:.1f} "
                     "(scoped to checkable claims only -- see docstring)")


def _check_unknown_handling() -> tuple[bool, str]:
    def sig(name, w, score):
        c = Confidence.UNKNOWN if score is None else Confidence.HEURISTIC
        return SignalScore(name, name, score, w, c)

    all_unknown = ScoreCard([sig("code", 0.30, None), sig("output", 0.30, None),
                            sig("interview", 0.30, None), sig("transcript", 0.10, None)])
    if all_unknown.weighted_estimate is not None:
        return False, (f"all-signals-unknown case returned "
                      f"{all_unknown.weighted_estimate}, not None")
    one_known = ScoreCard([sig("code", 0.30, 80), sig("output", 0.30, None),
                          sig("interview", 0.30, None), sig("transcript", 0.10, None)])
    expected = 80 * 0.30
    if abs((one_known.weighted_estimate or -1) - expected) > 1e-9:
        return False, (f"one-known case gave {one_known.weighted_estimate}, "
                      f"expected {expected} (weight NOT renormalized to 100%)")
    return True, "all-unknown -> None; partial cases use known weight only"


def _check_determinism() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "a.py").write_text(_LEGIT_SRC, encoding="utf-8")
        runs = [score_code(d).estimated_score for _ in range(3)]
        if len(set(runs)) != 1:
            return False, f"3 runs on the same fixture gave {runs}"
        return True, f"3/3 runs identical ({runs[0]:.2f})"


def _check_cross_signal_consistency() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "rules.py").write_text(
            'def classify(t):\n    if "fraud" in t: return escalate(t)\n',
            encoding="utf-8")
        (d / "dataset").mkdir()
        (d / "dataset" / "output.csv").write_text(
            "message_id,action,message_type,reason,confidence,evidence_message_ids\n"
            'M1,mute,scam,"low priority",0.9,none\n', encoding="utf-8")
        (d / "dataset" / "message_history.csv").write_text(
            "message_id,message\nM1,this looks like fraud on my account\n",
            encoding="utf-8")
        check = check_code_vs_output(d)
        if check.verdict != "FAIL":
            return False, (f"code<->output safety-violation fixture "
                          f"returned {check.verdict}, expected FAIL")

        d2 = Path(tempfile.mkdtemp())
        (d2 / "search.py").write_text("BM25_K1 = 1.2\n", encoding="utf-8")
        mismatch = check_code_vs_interview(
            d2, ["We use BM25 with k1=1.5 for retrieval."])
        if mismatch.verdict != "FAIL":
            return False, (f"code<->interview BM25 mismatch fixture "
                          f"returned {mismatch.verdict}, expected FAIL")
        return True, "both a code<->output violation and a code<->interview " \
                     "factual mismatch were caught"


_CATEGORIES = [
    ("Official rubric weights", _check_official_weights),
    ("Code ZIP keyword-gaming resistance", _check_code_gaming_resistance),
    ("Output CSV discrimination", _check_output_discrimination),
    ("Transcript keyword-gaming resistance", _check_transcript_discrimination),
    ("Interview discrimination (checkable claims)", _check_interview_discrimination),
    ("Unknown-signal handling", _check_unknown_handling),
    ("Determinism", _check_determinism),
    ("Cross-signal consistency", _check_cross_signal_consistency),
]


def run_health_checks() -> list[tuple[str, bool, str]]:
    results = []
    for name, fn in _CATEGORIES:
        try:
            ok, detail = fn()
        except Exception as exc:  # a crashing check is itself a FAIL
            ok, detail = False, f"check raised {type(exc).__name__}: {exc}"
        results.append((name, ok, detail))
    return results


def render_health_report() -> str:
    results = run_health_checks()
    lines = ["PHASE 1 SCORE ENGINE HEALTH", "=" * 34, "",
            "(every line below is a LIVE result: a real adversarial "
            "fixture was scored moments ago, not a cached claim)", ""]
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        lines.append(f"  {name:<42} {status}")
        lines.append(f"    {detail}")
    lines.append("")

    failed = [name for name, ok, _ in results if not ok]
    if failed:
        lines.append("OVERALL: NEEDS WORK")
        lines.append(f"  Failing categories: {', '.join(failed)}")
        lines.append("")
        lines.append("DO NOT USE SCORE ENGINE FOR OPTIMIZATION until the "
                     "categories above pass.")
    else:
        lines.append("OVERALL: TRUSTWORTHY")
        lines.append("  All adversarial categories above passed against a "
                     "live-run fixture.")
        lines.append("  NOTE: 'trustworthy' means these specific "
                     "adversarial categories pass, not that the engine is "
                     "immune to every possible gaming strategy -- see "
                     "score/ docstrings for stated, known limitations.")
    return "\n".join(lines)
