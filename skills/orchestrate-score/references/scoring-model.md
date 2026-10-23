# Scoring model: what is known, what is inferred

Read this before you trust any estimated score. The point is to separate published facts from guesses.

## Published by HackerRank (verified in the repos)

- **Final score** = weighted sum of four signals (July 2026 write-up, May round):
  `Final = 0.10 x Chat + 0.30 x Interview + 0.30 x Output CSV + 0.30 x Code ZIP`
- **Tie-break order:** Interview, then Code ZIP, then Output CSV, then Chat.
- **Code ZIP sub-weights:** agent architecture 30%, prompt and tool craft 30%, robustness 25%, engineering rigor 15%. Only observable code counts; README claims do not.
- **Chat sub-weights:** direction and architecture ownership 35%, technical specificity 25%, iteration and verification 25%, safety and edge-case awareness 15%.
- **Interview sub-weights:** technical depth and ownership 40%, problem understanding and judgment 25%, communication clarity 20%, honesty and self-awareness 15%.
- **Output CSV:** each row scored 0-100 for accuracy against a hidden golden set. One whole-file safety score for adversarial inputs. A correct action with an empty or contradicting justification is capped near 70.
- **Evaluation criteria per column** (May round `evalutation_criteria.md`): status, product_area, response, justification, request_type. The per-column weights were NOT published.
- **Sept round:** scored on `amount_safe_to_pay`, `affordability_status`, `recommended_payment_method` and `payment_plan`, `earliest_date_for_full_payment`, `spending_changes_needed`, `decision_explanation`. Weights NOT published.
- **Balance:** every Top 10 candidate was in the top quartile on all four signals; 37 of the Top 50 were in the top quartile on all four and 11 more on three. Pairwise Spearman correlations between signals are all below 0.45 (1,349 participants).

## Verified on the official September leaderboard (strongest evidence so far)
Source: HackerRank's public leaderboard for `hackerrank-orchestrate-september26`, challenge `buy-or-wait`, page 1 (30 of 3,062 entries). Fetched during the verification on the date of this edit.
- **Columns shown:** Chat transcript /10, AI judge interview /30, Output CSV /30, Code zip /30, Final /100.
- **The final equals the sum of the four displayed points in all 30 rows** (max difference 0.00). So the displayed section points already include the weights: the maxima 10 + 30 + 30 + 30 add to 100.
- **Spread in the top 30 (per section, points):** Chat 4.9 to 10.0 (mean 9.09); Interview 22.8 to 27.6 (mean 25.40); Output 12.6 to 21.9 (mean 16.40); Code 16.8 to 27.9 (mean 24.19). Output CSV has the widest spread, which matches it being the hardest section to score high on.
- **Final range in the top 30:** 80.0 down to 72.7.
- **Page banner bug:** the "Final Results" banner on the page showed 0.0 for the top three, while the table showed 80.0, 79.6 and 77.8. Do not use the banner.
- **Not published on the page:** no rubric, no per-row output scoring, no interview or transcript method. The page only has the column headers.

What this does and does not prove:
- It proves the section points add to the final. It does not prove the internal weights, because the page shows only the already-weighted points.
- It gives 30 data points from the top of the board. It says nothing about how the middle or bottom were scored.
- A web search found no published rubric beyond the July blog, so the sub-weights in this file remain from the blog, not from the leaderboard.

## Not available (so cannot be reverse-engineered exactly)
- The hidden golden datasets.
- HackerRank's grader code. `code/evaluation/` in the Sept repo is empty, and the other rounds' evaluation folders contain only participant-side harnesses.
- Per-column weights for the output CSV.
- How the interview judge converts a transcript into a number.
- The exact cap and rounding rules.

## Verification log
- **Weights reproduce a published total.** Stage points from one third-place write-up (May round, total 70.1): Code 27.6/30, Chat 9.8/10, Interview 21.3/30, Output 11.4/30. Run through the kit's `ScoreCard.weighted_estimate` with the published weights, it returns 70.10. An equal-weight version of the same stage percentages gives 74.75, so the test distinguishes the two weightings.
- **Limits of that check:** one data point, from a third-party post, not from HackerRank. It confirms the formula is consistent with that post. It does not verify HackerRank's internal grader, the per-row output scoring, or the interview and transcript scoring.
- **Kit self-audit** (`python -m orchestrate_kit score --audit`) passes its own adversarial fixtures. That tests the scorer against its own cases, not against real graded submissions.

## Inferred (estimate only, label it that way)
- The output score is probably per-row accuracy averaged over rows, then combined with a safety score. Each column in a row is probably weighted, but the weights are unknown. Treat any per-column number as a guess.
- A row with a correct decision but a weak justification is probably capped, as the blog says.
- A `payment_plan` or CSV format error probably zeroes that field, not the row. This is a guess; check the statement for stated penalties.

## How to use this file
1. Use the published weights for the four-signal estimate.
2. Use the per-column list from the current statement for the output estimate, but do not present per-column weights as facts.
3. Compare your estimate with the kit's heuristic in `orchestrate score`, which is labelled as a heuristic and is not HackerRank's grader (`orchestrate_kit/score/signals.py` DISCLAIMER).
4. When a number is reported, say which parts were measured and which were estimated.
