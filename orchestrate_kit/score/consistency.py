"""Cross-signal consistency checks, specific to Orchestrate's four
artifacts (Code ZIP, Output CSV, Chat Transcript, AI Judge Interview).

Why this exists: HackerRank grades four SEPARATE artifacts, which means a
submission can describe one thing in the transcript/interview and ship a
different thing in the code. Text-shape scoring alone (judge/scoring.py,
transcript/analyzer.py) cannot catch this -- a fluent, specific,
well-evidenced claim about a technique that was never implemented scores
identically to a true one. This module is the fix: it checks claims made
in transcript/interview/README text against what the code actually
contains, and checks the shipped output against safety behavior the code
claims to have.

Deliberately narrow and Orchestrate-shaped, not a generic fact-checker:
the claim vocabulary below is the set of techniques/behaviors that
actually show up in Orchestrate message-routing submissions (retrieval,
routing, safety escalation), not an attempt at general claim verification.

Every check returns one of four verdicts -- these are NOT interchangeable:
    PASS      claim is corroborated by code, or no claim was made
    WARNING   claim was made, no corroborating code evidence found
    FAIL      claim contradicts code (different implementation, or a
              concrete factual conflict such as a mismatched constant)
    UNKNOWN   not enough artifacts supplied to check this pair at all
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "venv",
             "node_modules", "site-packages"}


@dataclass
class ConsistencyCheck:
    pair: str
    verdict: str  # PASS | WARNING | FAIL | UNKNOWN
    detail: str
    claims: list[str] = field(default_factory=list)


# A technique/behavior is "claimed" if this word/phrase appears in prose.
# Kept to what actually shows up in real Orchestrate submissions -- not a
# general NLP entity list.
_TECHNIQUES = [
    "bm25", "tf-idf", "tfidf", "embeddings", "reranker", "reranking",
    "cross-encoder", "faiss", "rag", "retrieval-augmented",
    "whisper", "ocr", "multi-agent", "agent loop", "hosted api",
    "hosted model", "deterministic", "caching", "rate limit",
    "escalation", "fraud detection", "retry logic", "structured output",
]

_BM25_PARAM = re.compile(r"\bk1\s*[=:]\s*([\d.]+)|\bb\s*[=:]\s*([\d.]+)", re.I)


def _mentions(text: str) -> set[str]:
    low = text.lower()
    return {t for t in _TECHNIQUES if t in low}


def _code_text(repo_root: Path) -> str:
    parts = []
    for p in repo_root.rglob("*.py"):
        if _SKIP_DIRS & set(p.relative_to(repo_root).parts):
            continue
        parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _bm25_params(text: str) -> dict[str, float]:
    # Not \b on the left: real code spells this BM25_K1 = 1.2, and "_" is
    # a word character so \bk1\b never matches inside "_K1". A negative
    # lookbehind for a letter (not "not a word char") still allows the
    # underscore while blocking a false hit like "junk1 = 5".
    out: dict[str, float] = {}
    for m in re.finditer(r"(?<![a-zA-Z])k1\s*[=:]\s*([\d.]+)", text, re.I):
        out["k1"] = float(m.group(1))
    for m in re.finditer(r"(?<![a-zA-Z])b\s*[=:]\s*([\d.]+)(?!\d*\s*%)", text, re.I):
        out["b"] = float(m.group(1))
    return out


def _claim_vs_code(pair: str, claim_text: str | None,
                   code: str | None) -> ConsistencyCheck:
    if claim_text is None or code is None:
        return ConsistencyCheck(pair, "UNKNOWN",
                                "one or both artifacts not supplied")

    claimed = _mentions(claim_text)
    if not claimed:
        return ConsistencyCheck(pair, "PASS", "no checkable technique claims found")

    code_low = code.lower()
    unsupported = [c for c in claimed if c not in code_low]

    # BM25 constant check: a concrete, checkable factual claim, not just a
    # keyword match.
    if "bm25" in claimed:
        claimed_params = _bm25_params(claim_text)
        code_params = _bm25_params(code)
        for name, val in claimed_params.items():
            if name in code_params and abs(code_params[name] - val) > 1e-9:
                return ConsistencyCheck(
                    pair, "FAIL",
                    f"claims {name}={val} but code has {name}={code_params[name]}",
                    claims=sorted(claimed))

    if unsupported:
        return ConsistencyCheck(
            pair, "WARNING",
            f"claims {', '.join(sorted(unsupported))}, no corresponding "
            "evidence found in code", claims=sorted(claimed))
    return ConsistencyCheck(pair, "PASS",
                            f"claimed technique(s) corroborated in code: "
                            f"{', '.join(sorted(claimed))}", claims=sorted(claimed))


def check_code_vs_transcript(repo_root: Path,
                             transcript_path: Path | None) -> ConsistencyCheck:
    text = (transcript_path.read_text(encoding="utf-8", errors="replace")
           if transcript_path and transcript_path.exists() else None)
    code = _code_text(repo_root) if repo_root.exists() else None
    return _claim_vs_code("Code <-> Transcript", text, code)


def check_code_vs_interview(repo_root: Path,
                            interview_answers: list[str] | None) -> ConsistencyCheck:
    text = " ".join(interview_answers) if interview_answers else None
    code = _code_text(repo_root) if repo_root.exists() else None
    return _claim_vs_code("Code <-> Interview", text, code)


def check_readme_vs_code(repo_root: Path) -> ConsistencyCheck:
    readme = None
    for name in ("README.md", "README.rst", "README.txt", "README"):
        p = repo_root / name
        if p.exists():
            readme = p.read_text(encoding="utf-8", errors="replace")
            break
    code = _code_text(repo_root) if repo_root.exists() else None
    return _claim_vs_code("README <-> Code", readme, code)


_REJECT_PATTERN = re.compile(
    r"\breject\w*|didn'?t use|did not use|instead of using|"
    r"we (?:dropped|removed|abandoned)\b", re.I)
_SHIP_PATTERN = re.compile(
    r"\bwe (?:use|implement|ship|built|chose)\b|\bcurrently uses?\b", re.I)


def check_transcript_vs_interview(
        transcript_path: Path | None,
        interview_answers: list[str] | None) -> ConsistencyCheck:
    if transcript_path is None or not transcript_path.exists() or not interview_answers:
        return ConsistencyCheck("Transcript <-> Interview", "UNKNOWN",
                                "one or both artifacts not supplied")

    t_text = transcript_path.read_text(encoding="utf-8", errors="replace")
    i_text = " ".join(interview_answers)
    t_low, i_low = t_text.lower(), i_text.lower()

    conflicts = []
    for tech in _TECHNIQUES:
        if tech not in t_low or tech not in i_low:
            continue
        # crude but conservative: same technique mentioned near a
        # rejection word in one artifact and a shipping word in the other
        t_window = _window(t_low, tech)
        i_window = _window(i_low, tech)
        t_rejected = bool(_REJECT_PATTERN.search(t_window))
        i_shipped = bool(_SHIP_PATTERN.search(i_window))
        i_rejected = bool(_REJECT_PATTERN.search(i_window))
        t_shipped = bool(_SHIP_PATTERN.search(t_window))
        if (t_rejected and i_shipped) or (i_rejected and t_shipped):
            conflicts.append(tech)

    if conflicts:
        return ConsistencyCheck(
            "Transcript <-> Interview", "FAIL",
            f"'{', '.join(conflicts)}' described as rejected in one "
            "artifact and shipped in the other")
    return ConsistencyCheck("Transcript <-> Interview", "PASS",
                            "no reject-vs-ship contradictions found")


def _window(text: str, phrase: str, radius: int = 60) -> str:
    i = text.find(phrase)
    if i < 0:
        return ""
    return text[max(0, i - radius):i + len(phrase) + radius]


_SAFETY_CODE_HINT = re.compile(
    r"\bfraud\b|\bscam\b|\bunauthorized\b|\bescalat\w*\b", re.I)


def check_code_vs_output(repo_root: Path) -> ConsistencyCheck:
    """If the code contains fraud/scam/unauthorized-escalation logic, the
    shipped output must not route a fraud/scam-flagged message to a
    suppressing action ('mute'). Scoped to Orchestrate's own action/
    message_type schema, not a generic security scanner."""
    import csv
    import io

    code = _code_text(repo_root) if repo_root.exists() else None
    out_path = repo_root / "dataset" / "output.csv"
    hist_path = repo_root / "dataset" / "message_history.csv"
    if code is None or not out_path.exists() or not hist_path.exists():
        return ConsistencyCheck("Code <-> Output", "UNKNOWN",
                                "code or dataset/output.csv or "
                                "dataset/message_history.csv not available")

    if not _SAFETY_CODE_HINT.search(code):
        return ConsistencyCheck("Code <-> Output", "UNKNOWN",
                                "no fraud/scam/escalation logic detected in "
                                "code -- nothing to cross-check")

    out_rows = list(csv.DictReader(io.StringIO(
        out_path.read_text(encoding="utf-8", errors="replace"))))
    hist_rows = list(csv.DictReader(io.StringIO(
        hist_path.read_text(encoding="utf-8", errors="replace"))))
    messages = {r.get("message_id"): r.get("message", "") for r in hist_rows}

    violations = []
    for r in out_rows:
        msg = messages.get(r.get("message_id"), "")
        if re.search(r"\bfraud\b|\bscam\b|\bunauthorized\b", msg, re.I) and \
                r.get("action") == "mute":
            violations.append(r.get("message_id"))

    if violations:
        return ConsistencyCheck(
            "Code <-> Output", "FAIL",
            f"code contains fraud/scam escalation logic, but {len(violations)} "
            f"row(s) with fraud/scam language were muted anyway: "
            f"{', '.join(violations[:5])}")
    return ConsistencyCheck("Code <-> Output", "PASS",
                            "code has escalation logic; no fraud/scam "
                            "message was muted in the output")


def run_all(repo_root: Path, transcript_path: Path | None = None,
           interview_answers: list[str] | None = None) -> list[ConsistencyCheck]:
    return [
        check_code_vs_output(repo_root),
        check_code_vs_transcript(repo_root, transcript_path),
        check_code_vs_interview(repo_root, interview_answers),
        check_transcript_vs_interview(transcript_path, interview_answers),
        check_readme_vs_code(repo_root),
    ]
