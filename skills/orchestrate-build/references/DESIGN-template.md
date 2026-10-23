# DESIGN.md

Copy this file into the repo root as `DESIGN.md` at the end of phase 1. Fill every section. If a section is empty, the design is not done.

## 1. Problem in one paragraph
What goes in, what comes out, who uses it. Quote the challenge's own words where you can.

## 2. Output contract
One row per input. For every output column:

| Column | Allowed values (exact) | Source (model field or code rule) | Rule ID |
|---|---|---|---|
| | | | |

Also list: separator, encoding, required row count, ID handling (keep as given, never reformat).

## 3. Architecture
- Entry point file:
- Stages, in order: load -> validate input -> build context -> model call -> parse -> validate output -> decide -> write
- Agent or workflow? One line why.
- What the model decides (free text, labels it may choose from):
- What code decides (every label that reaches the CSV):

## 4. The seam
The typed record the model returns, and the only thing code reads from it.

```
ModelObservation:
  field_name: type  # allowed values or range
```

Rule: decisions read booleans and enums from this record, never free text.

## 5. Decision rules (ordered)
Highest-risk rules first. The first matching rule wins.

| Order | Rule ID | Condition (on observations/inputs) | Outcome | Why this order |
|---|---|---|---|---|
| 1 | R1 | | | |
| 2 | R2 | | | |

Check: every allowed label is produced by at least one rule. Write the rule that produces each one.

## 6. Escalation and refusal
- Reply when:
- Escalate when:
- Refuse when:
- Default when evidence is missing:
- Why "escalate everything" and "reply to everything" are both wrong for this dataset:

## 7. Input validation and overrides
Checks before the model is called (empty row, missing field, duplicate ID, oversized text, injection markers). For each: action taken (reject row / flag / continue with note).

## 8. Failure handling
| Failure | What happens to the row | Logged where | Run continues? |
|---|---|---|---|
| Model call times out | | | |
| Malformed model output (after retries) | | | |
| Unknown label | | | |
| Unexpected exception | | | |

## 9. Retrieval (if used)
What is indexed, how it is searched, how many results go to the model, how you will measure recall on sample rows. Skip if no retrieval.

## 10. Test plan
- Edge cases to build first:
- Sample rows to use as a regression set (IDs only, do not tune to them):
- Blank-input and swap test (if multimodal or text-heavy):
- Determinism check: run twice, expect identical output.

## 11. Decisions log
Every real choice. One line each.

| # | Decision | Alternative rejected | Why |
|---|---|---|---|
| 1 | | | |

## 12. Known limits (write now, refine later)
Things this design will get wrong. The interview will ask.
-
-

## 13. Review gate (tick before phase 2)
- [ ] Every output column has a named source
- [ ] Every allowed label is produced by a rule
- [ ] Escalation rule explained in one sentence
- [ ] Risk rules come first in the order
- [ ] Failure table has no empty cell
- [ ] Decisions log has at least 5 entries
