"""AI Chat Transcript signal -- thin wrapper around the already-built,
already-tested `orchestrate_kit.transcript.analyzer`. No new scoring logic
here on purpose: one analyzer, one place its heuristics can be wrong or
fixed, not two copies that could drift apart."""

from __future__ import annotations

from pathlib import Path

from ..transcript.analyzer import analyze
from .signals import Confidence, Finding, SignalScore


def score_transcript(transcript_path: Path | None) -> SignalScore:
    if transcript_path is None or not transcript_path.exists():
        return SignalScore("transcript", "AI Chat Transcript", None, 0.10,
                           Confidence.UNKNOWN,
                           notes=["no transcript file supplied -- pass "
                                  "--transcript <file>"])

    text = transcript_path.read_text(encoding="utf-8", errors="replace")
    a = analyze(text)

    findings = [Finding(d.dimension.label, f"{d.score:.0f}% -- "
                        f"missing: {', '.join(d.missing)}")
               for d in a.dimensions if d.verdict != "PASS"]
    notes = [f"{a.word_count} words, {a.turn_count} turn(s), "
            f"{a.chain.present_count}/7 evidence-chain nodes present"]
    notes.extend(a.notes)

    return SignalScore("transcript", "AI Chat Transcript", a.weighted_score,
                       0.10, Confidence.HEURISTIC, findings, notes)
