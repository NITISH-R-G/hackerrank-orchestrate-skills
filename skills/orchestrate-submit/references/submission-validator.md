---
name: orchestrate-submission-validator
description: Prove the three submission artifacts are current, consistent, and correspond to the same commit. Use in the final hour, and after any change that touches production code. Catches stale outputs, which is the single most common silent submission defect.
---

# Orchestrate: Submission Validator

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Any generated artifact is stale until proven current, in the same breath as the
code that generates it.**

## What this caught in a real build

`output.csv` was **28 rows different** from what the committed code produced. It had
been generated three commits earlier. Nothing in a file listing shows this — the file
exists, has a sane size, and opens fine.

Found by regenerating to a temp path and comparing hashes. Never by looking at it.

## The procedure

```bash
# 1. Regenerate to a TEMP path -- never overwrite the artifact you are checking
python code/main.py --out /tmp/regen.csv

# 2. Hash both
sha256sum dataset/output.csv /tmp/regen.csv

# 3. Identical? current. Different? stale -- regenerate before shipping.
```

If your entry point has no `--out` flag, **add one**. A pipeline that can only write
to one hardcoded path cannot be verified without destroying the thing being verified.

## The checklist

- [ ] `git status --porcelain` empty for tracked files
- [ ] Artifact regenerated to a temp path and hash-compared
- [ ] The artifact was produced by the **current** commit
- [ ] Package rebuilt **after** the last code change, not before
- [ ] Every file in the package byte-matches the working tree
- [ ] No `__pycache__`, caches, or editor files in the package
- [ ] No secrets in the package, the repo, **or git history**
- [ ] Transcript artifact located and current

## Failure modes

- **Rebuilding the package before the final commit.** Order matters: code → artifact → package.
- **Trusting a timestamp.** A file touched by an unrelated tool looks fresh.
- **Checking the working tree but not history** for secrets. A rotated key is still
  in history unless purged.
