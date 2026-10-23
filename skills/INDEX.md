# Orchestrate skills - index

Works in any AI agent. Read the table, pick the row that matches where you are, open that skill's `SKILL.md`.

| Where you are | Open this skill |
|---|---|
| Just started, or unsure what is next | `orchestrate/SKILL.md` |
| Read the problem, need a design, now building | `orchestrate-build/SKILL.md` |
| Pipeline runs on sample, need to find wrong rows | `orchestrate-test-fix/SKILL.md` |
| Rows are wrong or weakly justified | `orchestrate-test-fix/SKILL.md` (Part B) |
| Output is stable, need scores, security, packaging | `orchestrate-submit/SKILL.md` |
| Preparing for the AI judge interview | `orchestrate-interview/SKILL.md` |
| Output is final, want the submission folder and a readiness check | `orchestrate-package/SKILL.md` |
| Want an estimated score, or the weakest section | `orchestrate-score/SKILL.md` |
| Need a ready-to-paste prompt, principle, or checklist | `orchestrate-reference/SKILL.md` |

## Order

1. `orchestrate` (read first, re-read on failure)
2. `orchestrate-build`
3. `orchestrate-test-fix`
4. `orchestrate-submit`

`orchestrate-interview` runs in parallel from mid-build. `orchestrate-reference` is lookup only.

## Installing the skills into a harness

- Claude Code: `scripts/install-skills.sh` or `scripts/install-skills.ps1` (copies to `~/.claude/skills`).
- Other agents: point them at this file, or paste `orchestrate/SKILL.md` into the agent's instruction file. The root `AGENTS.md` is read by Codex, Cursor, Copilot and most other agents.

## Goal conditions (keep working until the skill's job is done)

Each phase skill has a `Goal mode` section with a condition to paste into `/goal`. A skill cannot start its own goal, so you set it once per phase. `/goal` keeps Claude working after each turn until the condition holds. Use `/goal clear` to stop early. The evaluator only reads the transcript, so the skill tells Claude what evidence to print each turn.

