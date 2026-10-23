"""Compare the orchestrate-score estimate with OFFICIAL section scores.

Create official_scores.json from the numbers HackerRank gives you (never guess them):

    {
      "code":       {"points": 27.6, "max": 30},
      "output":     {"points": 11.4, "max": 30},
      "interview":  {"points": 21.3, "max": 30},
      "transcript": {"points": 9.8,  "max": 10},
      "final":      70.1
    }

Run from the repo root:

    python skills/orchestrate-score/scripts/calibrate.py --repo . --official official_scores.json \
        --transcript log.txt --interview-result interview.json

It reports, per section, the estimate, the official percentage, and the gap, plus
whether the published weights reproduce the official final. Gaps are the evidence
for how far to trust each estimate. Nothing is written to the repo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WEIGHTS = {"code": 0.30, "output": 0.30, "interview": 0.30, "transcript": 0.10}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--official", required=True, type=Path)
    ap.add_argument("--transcript", type=Path, default=None)
    ap.add_argument("--interview-result", type=Path, default=None)
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    official = json.loads(args.official.read_text(encoding="utf-8"))
    repo = args.repo.resolve()

    # Use the kit's own scorer so the estimate is exactly what the skill reports.
    sys.path.insert(0, str(repo))
    from orchestrate_kit.score.scoreboard import build_scorecard

    card = build_scorecard(repo, python=args.python,
                           transcript_path=args.transcript,
                           interview_result_path=args.interview_result)
    estimates = {s.name: s.estimated_score for s in card.signals}

    print(f"{'section':<12}{'estimate':>10}{'official':>10}{'gap':>9}  note")
    gaps = {}
    for name in WEIGHTS:
        off = official.get(name)
        est = estimates.get(name)
        if not off:
            print(f"{name:<12}{'-':>10}{'-':>10}{'-':>9}  no official score supplied")
            continue
        off_pct = off["points"] / off["max"] * 100
        if est is None:
            print(f"{name:<12}{'UNKNOWN':>10}{off_pct:>9.1f}%{'-':>9}  artifact not supplied to the scorer")
            continue
        gap = est - off_pct
        gaps[name] = gap
        print(f"{name:<12}{est:>9.1f}%{off_pct:>9.1f}%{gap:>+8.1f}  "
              f"{'estimate within 10 pts' if abs(gap) <= 10 else 'estimate off by more than 10 pts'}")

    if all(n in official for n in WEIGHTS):
        published = sum(WEIGHTS[n] * official[n]["points"] / official[n]["max"] * 100 for n in WEIGHTS)
        print(f"\nweights on official section scores -> {published:.2f}")
        if "final" in official:
            diff = published - official["final"]
            verdict = "REPRODUCED" if abs(diff) < 0.2 else "NOT reproduced"
            print(f"official final {official['final']:.2f}  -> weights {verdict} (difference {diff:+.2f})")

    if gaps:
        worst = max(gaps, key=lambda n: abs(gaps[n]))
        print(f"\nlargest estimate gap: {worst} ({gaps[worst]:+.1f} pts). Treat that section's estimate as least reliable.")
    print("\nThis is one data point per section. Re-run after each new official result to build the record.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
