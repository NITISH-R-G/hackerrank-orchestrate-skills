---
name: orchestrate-secrets-and-determinism
description: Enforce the two hard technical constraints HackerRank Orchestrate submissions are explicitly graded on — secrets only in environment variables (never hardcoded), and deterministic/seeded behavior for anything involving randomness or sampling. Use when writing configuration/setup code, when an agent's output changes between identical runs, or before packaging a submission zip to check for embedded credentials or local absolute paths.
---

# Orchestrate: Secrets and Determinism

**Direct evidence**: the official starter repository states these as hard constraints, not suggestions — *"Store secrets in environment variables only; never hardcode keys,"* and *"Be deterministic; seed random sampling."* HackerRank's own advice separately names *"Hardcoded paths/secrets: Eliminate local dependencies and embedded credentials"* as a scored mistake.

## Why these two specific things

Both are graded mechanically, not by judgment call — which makes them the cheapest possible points to lose:

- **A hardcoded API key or local path breaks the submission the moment it's graded on infrastructure that isn't your laptop.** `code/` gets extracted somewhere else and run fresh; an absolute path like `/Users/yourname/orchestrate/corpus/` or an API key baked into a `.py` file either fails to run or, worse, leaks a credential into a public submission.
- **Non-deterministic output makes the golden-dataset comparison unreliable, and looks like it might be gaming the metric.** If two runs on the same input produce different `output.csv` rows, a grader can't trust that what they're scoring is representative — and unseeded randomness in an evaluation-sensitive system reads as an oversight at best.

## The concrete checklist

- [ ] Every API key, token, or credential is read via `os.environ` / `process.env` — none appear as string literals anywhere in the code
- [ ] A `.env.example` (not `.env` itself) documents which environment variables are needed, so a fresh grader knows what to set
- [ ] No absolute local paths (`/Users/...`, `C:\Users\...`) — everything is relative to the project root or passed as a config value
- [ ] Any `random`, `numpy.random`, or sampling call has an explicit, fixed seed
- [ ] Running the submission twice on the same input produces byte-identical (or at minimum row-identical) `output.csv`
- [ ] The zip itself contains no `.env` file, no `node_modules`, no `venv` — per the starter repo's explicit exclusion list

## Why this belongs in the code-quality 30%, specifically

This is exactly the kind of check a code reviewer runs first, before reading a single line of business logic — grep for `sk-`, `api_key = "`, `/Users/`, and unseeded `random.` calls. Failing any of these signals "this wasn't built with the assumption that someone else would run it," which is a bad first impression to make on 30% of your score before the interesting engineering is even evaluated.
