# CONSTANTS.md

Build this before the interview. The judge asked a past candidate to explain retrieval hyperparameters they could not recall. That one gap cost the most points. Every number in your code gets one row.

| Constant | Value | Where in code | Provenance | Evidence or reason | Losing alternative (if MEASURED) |
|---|---|---|---|---|---|
| | | | | | |

## Provenance labels (use only these)
- **MEASURED**: you swept it and another value scored worse. Give the number and the losing alternative.
- **SPEC**: fixed by the problem statement or the labels. Cite the line.
- **STANDARD**: canonical value from the literature, not tuned by you. Say so.
- **BOUND**: derived from an external standard. Cite it.
- **JUDGEMENT**: reasoned, not measured. Say so, and give the reasoning.

## Rules
- Never write "chosen after evaluation" for a value you did not sweep. That is a fabrication, and one follow-up question exposes it.
- The provenance column matters more than the number.
- Categories you must cover: retrieval parameters, confidence floor and ceiling, evidence count, any resize dimension, provider confidence threshold, every numeric threshold in a rule, every regex bound, every timeout.

## Model answer for an untuned standard value
> "k1 = 1.5, b = 0.75: the canonical Robertson / Spärck Jones defaults. I deliberately did not tune them. Tuning two hyperparameters on 28 labelled rows is how you overfit a hidden set."
