"""Assembles all four signal scorers into one ScoreCard and renders the
scoreboard report format. This is the only place that combines signals --
each scorer in this package stays independent and testable on its own."""

from __future__ import annotations

import json
from pathlib import Path

from .code_zip import score_code
from .interview_signal import score_interview
from .output_csv import score_output
from .signals import DISCLAIMER, ScoreCard
from .transcript_signal import score_transcript


def build_scorecard(repo_root: Path, python: str = "python",
                    transcript_path: Path | None = None,
                    interview_result_path: Path | None = None) -> ScoreCard:
    signals = [
        score_code(repo_root),
        score_output(repo_root, python=python),
        score_interview(interview_result_path),
        score_transcript(transcript_path),
    ]
    return ScoreCard(signals=signals)


_HISTORY_FILE = ".orchestrate_score_history.json"


def _load_previous(repo_root: Path) -> float | None:
    p = repo_root / _HISTORY_FILE
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    history = data.get("history", [])
    return history[-1]["weighted_estimate"] if history else None


def record_history(repo_root: Path, card: ScoreCard) -> None:
    p = repo_root / _HISTORY_FILE
    data = {"history": []}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"history": []}
    data.setdefault("history", []).append({
        "weighted_estimate": card.weighted_estimate,
        "known_weight_fraction": card.known_weight_fraction,
        "signals": {s.name: s.estimated_score for s in card.signals},
    })
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def render_scoreboard(card: ScoreCard, repo_root: Path,
                      save_history: bool = True) -> str:
    lines = ["HACKERRANK ORCHESTRATE SCOREBOARD", "=" * 34, ""]

    for s in card.signals:
        lines.append(s.label.upper())
        if s.is_unknown:
            lines.append("  UNKNOWN (not measurable locally)")
        else:
            lines.append(f"  {s.estimated_score:.1f} / 100  "
                         f"[{s.confidence.value}]")
            lines.append(f"  Weight: {s.official_weight * 100:.0f}%")
            lines.append(f"  Contribution: {s.contribution:.2f}")
        for f in s.findings[:5]:
            lines.append(f"  - {f.label}: {f.detail}" if f.detail
                        else f"  - {f.label}")
        for n in s.notes:
            lines.append(f"  note: {n}")
        lines.append("")

    lines.append("-" * 34)
    weighted = card.weighted_estimate
    missing = [s.label for s in card.signals if s.is_unknown]

    if weighted is None:
        lines.append("ESTIMATED ORCHESTRATE SCORE: UNKNOWN")
        lines.append("  Reason: no signal is measurable locally "
                     f"({', '.join(missing)} all unavailable).")
    elif missing:
        # Deliberately NOT rendered as "X / 100" -- that would visually
        # equate a 90%-known partial estimate with a full-confidence one.
        # The published scale tops out at 100; showing a smaller-looking
        # fraction of KNOWN weight makes the gap impossible to mistake for
        # a complete score.
        lines.append("CURRENT ESTIMATED SCORE: UNKNOWN (partial data only)")
        lines.append(f"  Measured contribution so far: {weighted:.2f} "
                     f"points, from {card.known_weight_fraction * 100:.0f}% "
                     "of the official weight")
        lines.append(f"  Missing signal(s), NOT counted as zero: "
                     f"{', '.join(missing)} "
                     f"({(1 - card.known_weight_fraction) * 100:.0f}% of "
                     "official weight unaccounted for)")
    else:
        lines.append(f"ESTIMATED ORCHESTRATE SCORE: {weighted:.2f} / 100")
        lines.append("  All four official signals were measurable.")

    if weighted is not None:
        prev = _load_previous(repo_root)
        if prev is not None:
            delta = weighted - prev
            sign = "+" if delta >= 0 else ""
            lines.append(f"  Previous estimate: {prev:.2f}")
            lines.append(f"  Delta: {sign}{delta:.2f}")
        else:
            lines.append("  Previous estimate: none recorded yet")

        weakest = card.weakest_known_signal
        strongest = card.strongest_known_signal
        if weakest:
            lines.append(f"  Weakest known signal: {weakest.label} "
                         f"({weakest.estimated_score:.1f}/100, "
                         f"{weakest.official_weight * 100:.0f}% weight)")
        if strongest and strongest is not weakest:
            lines.append(f"  Strongest known signal: {strongest.label} "
                         f"({strongest.estimated_score:.1f}/100)")

        if save_history:
            record_history(repo_root, card)

    lines.append("")
    lines.append(DISCLAIMER)

    if card.official_score is not None:
        lines.append("")
        lines.append(f"OFFICIAL SCORE (user-supplied): "
                     f"{card.official_score:.2f} / 100")
        if weighted is not None:
            lines.append(f"  Calibration error (estimate - official): "
                         f"{weighted - card.official_score:+.2f}")

    return "\n".join(lines)
