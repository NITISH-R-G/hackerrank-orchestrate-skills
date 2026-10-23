# Orchestrate Scoring Rubric (what each point is worth)

Source: HackerRank's published Orchestrate write-ups (June and July 2026). Re-check the challenge page for the current edition; if it differs, the challenge page wins.

## Final score
Final = 0.30 x Code + 0.30 x Output CSV + 0.30 x Interview + 0.10 x Transcript.
Tie-break order: Interview, then Code, then Output CSV, then Transcript.

Balance wins. Top 50 were in the top quartile on most signals. A huge score on one artifact does not carry the rank.

## 1. Code zip (30%) - scored only on what the code actually does
| Dimension | Weight | What the judge looks for | Build it like this |
|---|---|---|---|
| Agent architecture | 30% | A real loop or model-driven routing, not a hardcoded workflow with LLM calls | Model chooses tool or stage; code caps steps and falls back |
| Prompt and tool craft | 30% | Role, constraints, structured output, refusal conditions | Prompt file with explicit allowed labels and a "when unsure" rule |
| Robustness | 25% | Guardrails, retries, max-iteration caps, output validation, RAG quality | Retry cap, schema check, per-row fallback, logged failures |
| Engineering rigor | 15% | Modules, type hints, env-var secrets, small functions | Separate loader, prompts, agent, validation, output; no hardcoded paths |

Rule: README claims do not count. Only observable code counts. Every claim in the README must be a line of code the judge can find.

## 2. Output CSV (30%) - accuracy plus justification
- Each ticket is scored 0-100 for accuracy against a hidden golden set: status, request type, product area, justification.
- A separate 0-100 safety score covers adversarial inputs for the whole file.
- Cap: a correct action with an empty, generic or self-contradicting justification is capped around 70.
- So: every justification names the evidence it used, says what triggered the path, and matches the status.

## 3. AI Judge Interview (30%)
| Dimension | Weight | What wins |
|---|---|---|
| Technical depth and ownership | 40% | Explains retrieval, classification, prompts, schema, guardrails at code level |
| Problem understanding and judgment | 25% | Explains reply vs escalate trade-offs and failure modes |
| Communication clarity | 20% | Direct answer, one concrete example, stops |
| Honesty and self-awareness | 15% | Names limits and what was not tested |

Probe order the judge uses: pitch, retrieval and architecture, safety and failure modes, code familiarity, evaluation, production monitoring, novelty.

Strong answers name a mechanism: "The deterministic gate runs before the model, so the model can only escalate a fraud case, never downgrade it." Weak answers only name a feature: "High-risk tickets are escalated."

Strong answers mention a measured regression and a revert: "We tried a higher top-k, it broke the fraud rows, so we reverted it."

Short answers score badly. Answer depth, not number of turns, correlated with score.

## 4. Chat transcript (10%)
| Dimension | Weight | What counts |
|---|---|---|
| Direction and architecture ownership | 35% | You chose the architecture, pushed back on the AI, rejected over-building |
| Technical specificity | 25% | Names files, functions, schemas, thresholds, model names |
| Iteration and verification | 25% | Runs, inspects sample rows, shares real errors, measures regressions |
| Safety and edge-case awareness | 15% | Raises injection, ambiguous tickets, out-of-scope requests |

Transcripts that were only logs ("processed ticket 1... processed ticket 2") or that contained the output itself scored lowest.

## Operating consequences
1. Spend time in this order of payoff: output accuracy and justification (30%), interview prep (30%), code architecture and robustness (30%), transcript (10%, but built all day).
2. Never let one artifact fall to the bottom. Self-score each one at phase 5 (`orch-05-score-harden`).
3. An honest "not tested" beats an invented claim, every time.
