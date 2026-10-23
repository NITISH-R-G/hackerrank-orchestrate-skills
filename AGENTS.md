# AGENTS.md - instructions for any AI coding agent

This repository holds **Orchestrate skills**: plain-markdown playbooks for the HackerRank Orchestrate hackathon, plus a Python toolkit that audits submissions.

Any agent can use them: Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Windsurf, Aider, or a plain chat model with the files pasted in. Skills are ordinary markdown. The `SKILL.md` frontmatter is only used by Claude Code's skill loader; every other agent reads the body text.

## How to use the skills (any agent)

1. Read `skills/INDEX.md`. It maps each situation to one skill.
2. Start with `skills/orchestrate/SKILL.md`. It holds the phase order and the failure routing.
3. Go to the phase skill it names. Each skill lists its `references/` files. Read only the ones you need.
4. Re-open `orchestrate` whenever a step fails.

Phase order: `orchestrate` -> `orchestrate-build` -> `orchestrate-test-fix` -> `orchestrate-submit`. `orchestrate-interview` runs in parallel from mid-build. `orchestrate-reference` is lookup only.

## Rules for the agent working on a submission

- Never tune against sample rows until one number matches. That is overfitting.
- Model describes, code decides. Decisions use booleans and enums, never free text.
- Keep the output contract exact: column names, allowed values, separators, row count.
- Never write a number you did not measure. Use the provenance labels in `skills/orchestrate-interview/references/CONSTANTS-template.md`.
- Do not overwrite a starter `CLAUDE.md` or `AGENTS.md` in the challenge repo. Append to it.
- Keep a safe fallback output banked before any experiment.
- Before changing anything, state the metric it should move and the rows it could break.

## Rules for working on this repository

- Python 3.10+. Run tests with `python -m pytest -q`.
- Tests must pass on Windows and Linux. Full git history is required for commit-provenance tests (`git fetch --unshallow` on a shallow clone).
- Keep skills in `skills/<name>/SKILL.md` with `name` and `description` frontmatter. Keep each skill's detail in `references/`.
- Do not add a new skill when an existing one covers the job. Edit the existing skill instead.
- Historical documents live in `docs/history/`. Do not link to them from skills.
