---
name: orchestrate-score
description: Estimate the Orchestrate score the way HackerRank weights it - four signals (Code ZIP 30%, Output CSV 30%, AI Interview 30%, Chat Transcript 10%) with the published sub-weights. Uses the kit's scoring module as a heuristic and clearly separates measured facts from estimates. Use before submission, after each improvement, and to decide which section to fix next.
---

# Score Estimate

Read `references/scoring-model.md` first. It states what HackerRank published, what is missing, and what is guessed. Do not report a number without saying which part of it is estimated.

## What this skill can and cannot do
- **Can:** estimate each section from evidence you can check, combine them with the published weights, and show which section is the weakest to fix.
- **Cannot:** produce HackerRank's real score. The golden datasets and the grader are not public. The kit's scorer is a heuristic and says so in its code (`orchestrate_kit/score/signals.py`, DISCLAIMER).

## Step 1 - Run the kit's scorer
From the repo root:

```bash
python -m orchestrate_kit score --no-history --python python
```

Options:
- `--transcript <file>` to score the chat transcript export.
- `--interview-result <file>` for a JSON saved by `python -m orchestrate_kit interview --save <path>`.
- `--what-if output +5` to see the weighted impact of a possible gain. It does not predict whether the gain is achievable.
- `--audit` to run the scorer's own self-test first. Run it once, so you trust the scorer before you trust its numbers.

Without the Output CSV, Interview and Transcript artifacts the report shows UNKNOWN for them. That is correct: supply the artifacts to get estimates for those sections.
- `--official-score <n>` to record a real score you were given; the report then shows the gap.

The report shows four signal scores, the combined estimate, and the highest-leverage signal to fix. Save the output in `evaluation/score_estimate.md` if the challenge asks for evaluation evidence.

## Step 2 - Check each section by hand
The heuristic is a starting point. Confirm each section against the evidence below.

| Section | Weight | Check |
|---|---|---|
| Output CSV | 30% | Accuracy on the sample you have labels for, per column. Justification quality per row. Safety rows handled without crashing. Use the per-column list in the current problem statement. |
| Code ZIP | 30% | Architecture is a real pipeline with clear seams. Prompts specify allowed outputs. Retries and caps exist. Secrets from env. README matches the code. |
| AI Interview | 30% | You can explain every decision in `DESIGN.md`, every number in `CONSTANTS.md`, and one measured regression. Use `orchestrate-interview`. |
| Chat Transcript | 10% | Plans before builds, specific instructions, real errors pasted, pushback visible. Use `orchestrate-transcript` rules in `orchestrate`. |

Score each section 0-100 with one line of evidence each. Do not score a section you have not checked; write "not checked" instead.

## Step 2b - Apply the scoring rules
Before you score a section, apply the rules in `references/scoring-model.md` ("Scoring rules derived for the estimator"). In particular: cap rows with weak justifications at 70, credit only code that is observable, score interview answers by depth and mechanism, and never credit transcript volume.

## Step 3 - Combine with the published weights
```
Estimate = 0.30 x Code + 0.30 x Output + 0.30 x Interview + 0.10 x Transcript
```
If any section is "not checked", show the combined number as a range (missing sections at 0 and at 100), not a single number.

## Step 4 - Decide what to fix next
- The section with the largest `weight x (100 - score)` gap is the best use of the next hour.
- Output CSV gaps are usually the cheapest to close with a targeted fix. Use `orchestrate-test-fix` and measure with the change-record loop.
- Interview gaps are the cheapest in absolute time, but they are scored on depth, so prepare concrete mechanisms, not general claims.

## Calibrate against official results (when you have them)
Only your own official section scores can validate this skill. Put them in `official_scores.json` (format in `scripts/calibrate.py`), then run from the repo root that produced those scores:

```bash
python skills/orchestrate-score/scripts/calibrate.py --repo . --official official_scores.json   --transcript log.txt --interview-result interview.json
```

It prints, per section, the estimate, the official percentage and the gap, and whether the published weights reproduce your official final. Rules:
- Use only numbers HackerRank gave you for THIS submission. Never type in another team's numbers against your own repo: that compares two different submissions and proves nothing. (A test run that did exactly this produced a 40-point code gap; the gap came from the wrong repo, not from the scorer.)
- A section with no official number is reported as unchecked. Do not treat it as passed.
- Record each calibration in `references/scoring-model.md` with the date and the round.

## Rules
- Label every number as MEASURED (you ran it), ESTIMATED (heuristic or judgement), or NOT CHECKED.
- Do not compare your estimate with another team's score unless both used the same method.
- Never write a number that the challenge did not publish as if it were the official score.

## Goal mode (estimate and improve)
Run this in the session (the skill cannot set it for you):

```text
/goal the score estimate exists for all four sections with evidence labels (MEASURED, ESTIMATED or NOT CHECKED), the weakest section has a planned fix, and calibrate.py has been run if official_scores.json exists. Stop after 40 turns.
```

Each turn, print the four section estimates and the weakest one. Creative freedom: improve the estimator's logic, but do not change published weights.

The goal evaluator only sees what appears in the transcript, so print the evidence each turn. It clears the goal when the condition is met, or when it judges it impossible.
