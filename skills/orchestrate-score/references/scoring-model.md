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
- **Balance:** the top 50 were in the top quartile across all four signals. Correlations between signals are all below 0.45 (Spearman, 1,349 participants).

## Not available (so cannot be reverse-engineered exactly)
- The hidden golden datasets.
- HackerRank's grader code. `code/evaluation/` in the Sept repo is empty, and the other rounds' evaluation folders contain only participant-side harnesses.
- Per-column weights for the output CSV.
- How the interview judge converts a transcript into a number.
- The exact cap and rounding rules.

## Inferred (estimate only, label it that way)
- The output score is probably per-row accuracy averaged over rows, then combined with a safety score. Each column in a row is probably weighted, but the weights are unknown. Treat any per-column number as a guess.
- A row with a correct decision but a weak justification is probably capped, as the blog says.
- A `payment_plan` or CSV format error probably zeroes that field, not the row. This is a guess; check the statement for stated penalties.

## How to use this file
1. Use the published weights for the four-signal estimate.
2. Use the per-column list from the current statement for the output estimate, but do not present per-column weights as facts.
3. Compare your estimate with the kit's heuristic in `orchestrate score`, which is labelled as a heuristic and is not HackerRank's grader (`orchestrate_kit/score/signals.py` DISCLAIMER).
4. When a number is reported, say which parts were measured and which were estimated.
