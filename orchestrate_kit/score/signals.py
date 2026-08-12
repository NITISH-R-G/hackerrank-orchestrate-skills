"""Shared types for the four published Orchestrate signals.

Weights are the ones HackerRank published (see the "Behind the Scenes of
HackerRank Orchestrate" writeup, June 2026): Code ZIP 30%, Output CSV 30%,
AI Judge Interview 30%, AI Chat Transcript 10%. Nothing else about
HackerRank's grading is assumed -- every SignalScore below is explicitly
`ESTIMATED`, never presented as the real judge's number, because none of
these scorers has ever been calibrated against a real graded submission.
That's not a caveat bolted on afterward; it's the reason `official_score`
exists as a separate field from `estimated_score` at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Confidence(str, Enum):
    """How much this SCORE should be trusted, not how confident the
    heuristic is in its own pattern matches. Even a HIGH-confidence
    signal here is a heuristic estimate, not a prediction of the real
    HackerRank judge -- see SignalScore.disclaimer."""

    MEASURED = "measured"      # derived from real audits against real files
    HEURISTIC = "heuristic"    # pattern-based, no ground truth to check against
    UNKNOWN = "unknown"        # could not be computed at all


OFFICIAL_WEIGHTS = {
    "code": 0.30,
    "output": 0.30,
    "interview": 0.30,
    "transcript": 0.10,
}

DISCLAIMER = (
    "ESTIMATED, not official. No public ground-truth graded Orchestrate "
    "submission exists to calibrate any of these scorers against. Treat "
    "this as a structured self-review, not a prediction of your real "
    "HackerRank score.")


@dataclass
class Finding:
    label: str
    detail: str = ""


@dataclass
class SignalScore:
    name: str                    # "code" | "output" | "interview" | "transcript"
    label: str                   # human-readable
    estimated_score: float | None   # 0-100, or None if UNKNOWN
    official_weight: float
    confidence: Confidence
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def contribution(self) -> float | None:
        if self.estimated_score is None:
            return None
        return self.estimated_score * self.official_weight

    @property
    def is_unknown(self) -> bool:
        return self.estimated_score is None


@dataclass
class ScoreCard:
    signals: list[SignalScore]
    official_score: float | None = None   # only set when the user supplies a real result

    @property
    def known_signals(self) -> list[SignalScore]:
        return [s for s in self.signals if not s.is_unknown]

    @property
    def weighted_estimate(self) -> float | None:
        """The weighted overall estimate -- but ONLY over the weight that's
        actually known. Silently treating a missing 30%-weight signal as 0
        (or dropping it and renormalizing the rest to 100%) would both be
        dishonest in different ways: the first punishes an unmeasured
        signal as if it failed, the second overstates confidence in the
        signals that ARE known. Instead this reports the true weighted sum
        AND the fraction of total weight it's based on, so the caller can
        judge for themselves rather than be handed a fake 100%-confidence
        number."""
        known = self.known_signals
        if not known:
            return None
        return sum(s.contribution for s in known)

    @property
    def known_weight_fraction(self) -> float:
        return sum(s.official_weight for s in self.known_signals)

    @property
    def weakest_known_signal(self) -> SignalScore | None:
        known = self.known_signals
        return min(known, key=lambda s: s.estimated_score) if known else None

    @property
    def strongest_known_signal(self) -> SignalScore | None:
        known = self.known_signals
        return max(known, key=lambda s: s.estimated_score) if known else None
