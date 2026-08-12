"""Assembles all four signal scorers into one ScoreCard and renders the
scoreboard report format. This is the only place that combines signals --
each scorer in this package stays independent and testable on its own.

Also owns: score history (for delta/attribution across runs), the
cross-signal consistency section, counterfactual "what if signal X moved
by N" math, and ranking which signal is the highest-leverage next thing
to work on. All of it derives from the same four SignalScores -- no
second, parallel scoring system.
"""

from __future__ import annotations

import json
from pathlib import Path

from .code_zip import score_code
from .consistency import run_all as run_consistency_checks
from .interview_signal import score_interview
from .output_csv import score_output
from .signals import DISCLAIMER, OFFICIAL_WEIGHTS, ScoreCard
from .transcript_signal import score_transcript


def build_scorecard(repo_root: Path, python: str = "python",
                    transcript_path: Path | None = None,
                    interview_result_path: Path | None = None) -> ScoreCard:
    signals = [
        score_code(repo_root),
        score_output(repo_root, python=python),
        score_interview(interview_result_path, repo_root=repo_root),
        score_transcript(transcript_path),
    ]
    return ScoreCard(signals=signals)


_HISTORY_FILE = ".orchestrate_score_history.json"


def _load_history(repo_root: Path) -> list[dict]:
    p = repo_root / _HISTORY_FILE
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data.get("history", [])


def _load_previous(repo_root: Path) -> float | None:
    history = _load_history(repo_root)
    return history[-1]["weighted_estimate"] if history else None


def record_history(repo_root: Path, card: ScoreCard) -> None:
    p = repo_root / _HISTORY_FILE
    data = {"history": _load_history(repo_root)}
    data["history"].append({
        "weighted_estimate": card.weighted_estimate,
        "known_weight_fraction": card.known_weight_fraction,
        "signals": {s.name: s.estimated_score for s in card.signals},
        # finding LABELS only (not full evidence text) -- enough to say
        # "this specific finding appeared/disappeared" between two runs
        # without the history file growing unboundedly.
        "finding_labels": {s.name: sorted(f.label for f in s.findings)
                          for s in card.signals},
    })
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _attribute_delta(repo_root: Path, card: ScoreCard) -> list[str]:
    """Answers 'why did my score change' using ONLY evidence this system
    actually has: the finding-label diff between the previous run and this
    one for each signal. Never claims CONFIRMED causality from correlation
    alone -- two runs changing together is not proof one caused the
    other -- so the strongest label this can ever produce is POSSIBLE,
    tied to a concrete finding that appeared or disappeared. No matching
    finding diff -> UNKNOWN, not a fabricated story."""
    history = _load_history(repo_root)
    if len(history) < 1:
        return []
    prev = history[-1]
    lines = ["", "SCORE ATTRIBUTION (previous run -> this run)"]
    any_line = False
    for s in card.signals:
        prev_score = prev.get("signals", {}).get(s.name)
        cur_score = s.estimated_score
        if prev_score is None or cur_score is None:
            continue
        delta = cur_score - prev_score
        if abs(delta) < 0.05:
            continue
        any_line = True
        sign = "+" if delta >= 0 else ""
        prev_labels = set(prev.get("finding_labels", {}).get(s.name, []))
        cur_labels = {f.label for f in s.findings}
        appeared = cur_labels - prev_labels
        resolved = prev_labels - cur_labels
        if resolved or appeared:
            reason = "; ".join(
                [f"resolved: {r}" for r in sorted(resolved)] +
                [f"new: {a}" for a in sorted(appeared)])
            lines.append(f"  {s.label} {sign}{delta:.2f}  "
                         f"CAUSE: POSSIBLE ({reason})")
        else:
            lines.append(f"  {s.label} {sign}{delta:.2f}  CAUSE: UNKNOWN "
                         "(score moved, no finding-level evidence why)")
    return lines if any_line else []


def counterfactual(card: ScoreCard, signal_name: str, delta: float) -> dict:
    """'If Output improved by +5, what happens to the weighted estimate?'
    Pure arithmetic over the published weight for that signal -- does NOT
    predict whether such an improvement is achievable, only what it would
    be worth if it happened."""
    sig = next((s for s in card.signals if s.name == signal_name), None)
    if sig is None:
        return {"error": f"unknown signal '{signal_name}', choose from "
                         f"{[s.name for s in card.signals]}"}
    if sig.is_unknown:
        return {"signal": signal_name, "impact": None,
               "reason": f"{sig.label} is currently UNKNOWN -- no baseline "
                        "to move from"}
    new_score = max(0.0, min(100.0, sig.estimated_score + delta))
    impact = (new_score - sig.estimated_score) * sig.official_weight
    return {"signal": signal_name, "label": sig.label,
           "current_score": sig.estimated_score, "delta_requested": delta,
           "weight": sig.official_weight, "weighted_impact": impact,
           "impact": impact}


def next_best_experiment(card: ScoreCard) -> list[dict]:
    """Ranks known signals by expected leverage, NOT by lowest score.
    Leverage = official_weight * realistic_headroom, where headroom caps
    at what confidence supports: a HEURISTIC signal's apparent gap to 100
    is not assumed fully closeable the way a MEASURED one's is, so
    heuristic headroom is discounted. This is still a rough proxy, not a
    guaranteed achievable gain -- stated as 'expected impact', not
    'guaranteed impact'."""
    from .signals import Confidence

    ranked = []
    for s in card.signals:
        if s.is_unknown:
            ranked.append({
                "signal": s.name, "label": s.label, "expected_impact": None,
                "reason": "UNKNOWN -- no local score to improve from; "
                         "supply the missing artifact first"})
            continue
        headroom = 100.0 - s.estimated_score
        discount = {Confidence.MEASURED: 1.0, Confidence.HEURISTIC: 0.6,
                   Confidence.UNKNOWN: 0.0}[s.confidence]
        expected_impact = headroom * discount * s.official_weight / 100.0 * 10
        ranked.append({
            "signal": s.name, "label": s.label,
            "expected_impact": round(expected_impact, 2),
            "confidence": s.confidence.value,
            "current_score": s.estimated_score,
            "reason": f"{len(s.findings)} open finding(s), "
                     f"{headroom:.0f} pts headroom to 100 "
                     f"at {s.confidence.value} confidence"})
    ranked.sort(key=lambda r: (r["expected_impact"] is None,
                              -(r["expected_impact"] or 0)))
    return ranked


def render_scoreboard(card: ScoreCard, repo_root: Path,
                      save_history: bool = True,
                      transcript_path: Path | None = None,
                      interview_answers: list[str] | None = None) -> str:
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

        lines.extend(_attribute_delta(repo_root, card))

        if save_history:
            record_history(repo_root, card)

    # ---- cross-signal consistency -----------------------------------
    lines.append("")
    lines.append("CONSISTENCY AUDIT")
    checks = run_consistency_checks(repo_root, transcript_path=transcript_path,
                                    interview_answers=interview_answers)
    for c in checks:
        lines.append(f"  {c.pair}")
        lines.append(f"    {c.verdict}  -  {c.detail}")

    # ---- highest-leverage next change --------------------------------
    lines.append("")
    lines.append("HIGHEST-LEVERAGE NEXT CHANGE")
    for i, r in enumerate(next_best_experiment(card), 1):
        if r["expected_impact"] is None:
            lines.append(f"  {i}. {r['label']}  --  {r['reason']}")
        else:
            lines.append(f"  {i}. {r['label']}  expected impact "
                         f"+{r['expected_impact']:.2f}  "
                         f"[{r['confidence']}]  -  {r['reason']}")

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
