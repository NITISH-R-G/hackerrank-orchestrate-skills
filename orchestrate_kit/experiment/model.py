"""The Experiment record.

One experiment == one hypothesis, one baseline, one change, one measured
result. The whole point of Phase 2 (per its own stated philosophy) is
making it HARDER to fool ourselves -- "I changed something and the score
went up" is not a successful experiment; "we defined a hypothesis,
measured a baseline, changed one thing, measured the result, checked
regressions, and can reproduce it" is. This dataclass is the contract
that shape enforces: nothing here lets a caller mark ACCEPTED without
actual_gain being a real measured number.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


class Status:
    PROPOSED = "PROPOSED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ABORTED = "ABORTED"

    ALL = (PROPOSED, RUNNING, COMPLETED, ACCEPTED, REJECTED, INCONCLUSIVE, ABORTED)
    # only these may be reached after a measured finish() -- ACCEPTED can
    # never be assigned without actual_gain being set to a real float.
    TERMINAL = (ACCEPTED, REJECTED, INCONCLUSIVE, ABORTED)


@dataclass
class Experiment:
    id: str
    timestamp: str
    title: str
    hypothesis: str = ""
    target_signal: str = ""
    target_dimension: str = ""

    baseline_commit: str = ""
    experiment_commit: str = ""
    baseline_score: dict = field(default_factory=dict)     # {signal: float|None, "weighted": float|None}
    experiment_score: dict = field(default_factory=dict)
    delta: dict = field(default_factory=dict)               # {signal: float}  only where both known

    confidence: str = "UNKNOWN"       # HIGH | MEDIUM | LOW | UNKNOWN
    expected_gain: str = "UNKNOWN"    # a string on purpose -- "UNKNOWN" is a
                                       # valid, honest value; a number is too
    actual_gain: float | None = None  # the ONLY thing that may gate ACCEPTED

    status: str = Status.PROPOSED
    decision: str = ""                # human-readable verdict + reason

    files_changed: list = field(default_factory=list)
    tests_run: str = ""
    evaluation_command: str = ""
    evidence: list = field(default_factory=list)
    regressions: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    parent_experiment: str = ""
    supersedes: str = ""
    reconsider_if: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Experiment":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})
