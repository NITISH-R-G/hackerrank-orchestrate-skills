---
name: orchestrate-package
description: Orchestrate final packaging. Checks the repo against the exact submission rules in problem_statement.md (output.csv header, row coverage, allowed values, code, README, transcript, secrets) and only then builds the submission/ folder with output.csv, code.zip, README, transcript and usage report. Use in the final hours, after orchestrate-submit's self-check, and whenever you want to know "are we submission ready?"
---

# Package the Submission

This skill answers one question: is everything ready for the submission, according to the problem statement? It does not invent requirements. The problem statement is the only authority. If the challenge page disagrees with this file, the challenge page wins.

## Step 1 - Read the submission rules (from the problem statement)
Write these down in `SUBMISSION-CHECKLIST.md` before checking anything. Past rounds required:

| Round | Required files | Extra rules |
|---|---|---|
| May 26 (support triage) | `support_tickets/output.csv`, `code.zip`, `log.txt` chat transcript, README | 5 output columns; AI judge interview |
| Jun 26 (claims review) | `output.csv` (repo root), `code.zip`, transcript | 13 output columns in exact order; `image_paths` separated by `;` |
| Aug 26 (message router) | `output.csv`, `code.zip`, transcript | 6 columns; `confidence` between 0 and 1; `evidence_message_ids` semicolon-separated or `none` |
| Sep 26 (buy or wait) | `output.csv`, `code.zip` (must include `evaluation/usage_report.md`), transcript | 8 columns; `0 <= amount_safe_to_pay <= requested_amount`; strict payment-plan format |

For the current challenge, copy its exact list from the problem statement. Do not trust this table for the current round.

## Step 2 - Run the checker

```bash
python skills/orchestrate-package/scripts/package_submission.py \
  --repo . \
  --input dataset/<input-file>.csv \
  --key <id-column> \
  --columns "<col1>,<col2>,..." \
  --allowed "<enum-col>=<v1>,<v2>,..." \
  --transcript log.txt \
  --out submission
```

If the installed copy lives in `~/.claude/skills/orchestrate-package/`, use that path instead. Run it from the repo root.

- Every line prints PASS or FAIL with the evidence.
- Exit code 0 and `READY TO SUBMIT` means the folder was built.
- Exit code 1 and `NOT READY` means nothing was built. Fix the FAIL lines and run again.

## Step 3 - Judge the things the script cannot check
The script checks shape, not quality. Also check by hand:
- Justifications match their status and cite the evidence used (see `orchestrate-test-fix`).
- Output values are what the code produced on the latest run, not a stale file. Re-run the pipeline from a clean folder first.
- The README lists setup, environment variables, the run command, and the expected input and output paths, and every claim in it is true.
- No `.env`, API keys, absolute local paths, or personal data in any file.
- Usage and cost numbers in `evaluation/usage_report.md` come from the final full run, not from a test.
- The transcript is complete, not truncated, and shows your own decisions.

## Step 4 - Verify the package
Unzip `submission/code.zip` into an empty folder. Follow only the README. Confirm it runs and writes `output.csv` that matches the one in `submission/`. If it does not match, the submission is not ready.

## Step 5 - Upload
Upload exactly what the problem statement lists, from `submission/`. Do not upload `dataset/` or the raw working folder unless the statement asks for it.

## Rules
- Never edit `output.csv` by hand to pass the checker. Fix the pipeline and regenerate.
- Never add a column, rename a column, or change a value format to satisfy a check you disagree with. Raise it with the organisers if the statement is unclear.
- If the checker reports a shape problem you cannot fix in time, submit the best valid file you have and say what is wrong in the README.

Related: `orchestrate-submit` (self-scoring and hardening), `orchestrate-score` (estimated score), `orchestrate-reference` (release checklist).

## Goal mode (readiness)
Run this in the session (the skill cannot set it for you):

```text
/goal package_submission.py reports READY TO SUBMIT and the submission/ folder contains output.csv, code.zip, README.md and the transcript. Stop after 30 turns.
```

Each turn, print the checker output. Creative freedom: fix anything the checker flags in the repo, but never edit output.csv by hand.

The goal evaluator only sees what appears in the transcript, so print the evidence each turn. It clears the goal when the condition is met, or when it judges it impossible.
