"""Analyze a chat transcript against the rubric in `rubric.py`.

Same honesty boundary as `orchestrate_kit/judge/scoring.py`, stated
explicitly rather than implied: this measures the SHAPE of a transcript
-- ownership language, named alternatives, concrete constraints, reported
measurements, named risk mechanisms -- not whether the underlying claims
are true. A transcript that says "I measured X" scores the same whether X
was actually measured or invented. This tool cannot tell the difference,
and does not claim to.

It also cannot reproduce HackerRank's actual grading model, because no
ground-truth graded transcript exists to calibrate against. What it CAN
honestly do: apply the same four published dimensions and weights,
surface which behaviors are present or missing, and let a human decide
what to do about it. Presenting this as "your real HackerRank score" would
be exactly the kind of unearned confidence this project refuses elsewhere
-- so it isn't. It's a self-review checklist with a number attached, not a
prediction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .rubric import DIMENSIONS, Behavior, Dimension

_OWNERSHIP = re.compile(
    r"\bi (?:chose|chose|decided|rejected|picked|went with|kept|reverted|"
    r"overrode|pushed back|disagreed|changed|redirected)\b|"
    r"\bwe (?:chose|decided|rejected|picked|went with|reverted)\b", re.I)

_TOOL_NARRATION = re.compile(
    r"\b(?:claude|the agent|the ai|codex|copilot|cursor|it) "
    r"(?:created|decided|built|generated|wrote|figured out|handled)\b", re.I)

_ALTERNATIVE = re.compile(
    r"\b(instead of|rather than|chose .* over|as opposed to|compared "
    r"(?:to|with)|versus|\bvs\.?\b|tried .* first|reject\w*)\b", re.I)

_CONSTRAINT = re.compile(
    r"\b(must|should not|never|always|no more than|at least|within \d+|"
    r"under \d+|zero \w+|schema|validat\w+|format|threshold)\b", re.I)

_TECH_ENTITY = re.compile(
    r"\b[A-Za-z][\w.]*\.(?:py|ts|tsx|js|json|yaml|yml|md)\b|"
    r"\b(?:gpt|claude|gemini|llama|bm25|rag|json|sql|regex|"
    r"top_k|top-k|k1|rerank\w*)\b", re.I)

_MEASUREMENT = re.compile(
    r"\b\d+\s*(?:/|of|out of)\s*\d+\b|\b\d+%|\bran (?:it|the)\b|"
    r"\btested\b|\bmeasured\b|\bregress\w*\b|\bfailed on\b|"
    r"\bfound \d+\b", re.I)

_REVERSAL = re.compile(
    r"\brevert\w*\b|\brolled back\b|\bswitched back\b|\bundid\b|"
    r"\bthat (?:broke|regressed|made it worse)\b", re.I)

_EDGE_CASE = re.compile(
    r"\b(prompt injection|jailbreak|adversarial|edge case|ambiguous|"
    r"fraud|unauthorized|malicious|hallucinat\w*|out.of.scope|"
    r"multilingual)\b", re.I)

_MECHANISM = re.compile(
    r"\b(gate|guard\w*|validat\w*|before the model|deterministic|"
    r"cannot (?:downgrade|override)|only allowed to|falls? back to)\b",
    re.I)

_VAGUE_SAFETY = re.compile(
    r"\b(?:we )?(?:made sure|ensured|handled) (?:it'?s?|it is) safe\b|"
    r"\bshould be (?:escalated|safe|handled)\b", re.I)

_PATTERNS: dict[str, tuple[re.Pattern, re.Pattern | None]] = {
    "direction": (_OWNERSHIP, _TOOL_NARRATION),
    "direction_alt": (_ALTERNATIVE, None),
    "specificity_entity": (_TECH_ENTITY, None),
    "specificity_constraint": (_CONSTRAINT, None),
    "iteration_measure": (_MEASUREMENT, None),
    "iteration_reversal": (_REVERSAL, None),
    "safety_edge": (_EDGE_CASE, None),
    "safety_mechanism": (_MECHANISM, _VAGUE_SAFETY),
}


@dataclass
class BehaviorHit:
    behavior: Behavior
    count: int
    present: bool


@dataclass
class DimensionResult:
    dimension: Dimension
    score: float                 # 0-100
    hits: list[BehaviorHit] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


@dataclass
class TranscriptAnalysis:
    weighted_score: float
    dimensions: list[DimensionResult]
    word_count: int
    turn_count: int
    notes: list[str] = field(default_factory=list)


def _count(pattern: re.Pattern) -> int:
    return len(pattern.findall(_TEXT))


_TEXT = ""  # set per-call, module-level to keep helper functions simple


def analyze(transcript: str) -> TranscriptAnalysis:
    global _TEXT
    _TEXT = transcript

    words = transcript.split()
    turns = len(re.findall(r"^\s*(?:user|human|you|me)\s*:", transcript,
                           re.I | re.M)) or 1

    results: list[DimensionResult] = []
    for dim in DIMENSIONS:
        if dim.key == "direction":
            own = _count(_OWNERSHIP)
            narr = _count(_TOOL_NARRATION)
            alt = _count(_ALTERNATIVE)
            score = min(100, 30 * own - 15 * narr + 25 * alt)
            hits = [
                BehaviorHit(dim.behaviors[0], alt, alt > 0),
                BehaviorHit(dim.behaviors[1], alt, alt > 0),
                BehaviorHit(dim.behaviors[2], own, own > narr),
            ]
        elif dim.key == "specificity":
            ent = _count(_TECH_ENTITY)
            con = _count(_CONSTRAINT)
            score = min(100, 12 * ent + 15 * con)
            hits = [
                BehaviorHit(dim.behaviors[0], ent, ent > 0),
                BehaviorHit(dim.behaviors[1], con, con > 0),
            ]
        elif dim.key == "iteration":
            meas = _count(_MEASUREMENT)
            rev = _count(_REVERSAL)
            score = min(100, 20 * meas + 25 * rev)
            hits = [
                BehaviorHit(dim.behaviors[0], meas, meas > 0),
                BehaviorHit(dim.behaviors[1], rev, rev > 0),
            ]
        else:  # safety
            edge = _count(_EDGE_CASE)
            mech = _count(_MECHANISM)
            vague = _count(_VAGUE_SAFETY)
            score = min(100, 25 * edge + 25 * mech - 10 * vague)
            hits = [
                BehaviorHit(dim.behaviors[0], edge, edge > 0),
                BehaviorHit(dim.behaviors[1], mech, mech > vague),
            ]

        score = max(0.0, score)
        missing = [h.behavior.name for h in hits if not h.present]
        results.append(DimensionResult(dim, score, hits, missing))

    weighted = sum(r.score * r.dimension.weight for r in results)

    # Repetition penalty. Found by actually trying to break this analyzer:
    # three copies of one boilerplate sentence containing every keyword
    # scored 86/100 before this existed. Regex pattern-matching is
    # inherently gameable by anyone who reads the source -- which is
    # everyone, since this is open source -- and a tool that claims to
    # measure engineering judgment while rewarding copy-paste would be
    # worse than useless. This doesn't make gaming impossible; it makes
    # the CHEAPEST form of gaming (repeat the rubric's own vocabulary)
    # visibly not work, which is the honest ceiling a heuristic can reach.
    sentences = [s.strip().lower() for s in re.split(r"[.!?]+", transcript)
                if len(s.strip()) > 15]
    unique_ratio = (len(set(sentences)) / len(sentences)) if sentences else 1.0
    if sentences and unique_ratio < 0.7:
        penalty = (0.7 - unique_ratio) * 100
        weighted = max(0.0, weighted - penalty)

    notes = []
    if sentences and unique_ratio < 0.7:
        notes.append(
            f"REPETITION PENALTY APPLIED: only {unique_ratio:.0%} of "
            f"sentences are unique. Repeating rubric-matching phrases "
            f"does not raise this score, and duplicated content is "
            f"exactly what a human reviewer would notice fastest too.")
    if turns > 15 and weighted < 50:
        notes.append(
            "High turn count with a low score: HackerRank's own published "
            "interview data found turn count had a WEAK NEGATIVE "
            "correlation with score -- more back-and-forth is not the fix. "
            "Depth per answer is what correlated (r=0.615 for word count, "
            "r=0.583 for specificity in the published interview analysis).")
    if len(words) < 50:
        notes.append("Very short transcript -- most dimensions will read "
                     "as 'missing' simply because there is little text to "
                     "find evidence in, not necessarily because the work "
                     "itself was thin.")

    return TranscriptAnalysis(weighted, results, len(words), turns, notes)
