"""Experiment isolation. One measured delta can only be attributed to one
change. This does not (cannot) know whether two changed files are
"related" in intent -- it flags the shape that historically means a
measurement got contaminated: noise files (docs, memory, generated
artifacts) mixed into the diff, or a diff too large to plausibly be one
change."""

from __future__ import annotations

import re

_NOISE_PATTERNS = [
    re.compile(r"^README", re.I),
    re.compile(r"^docs/", re.I),
    re.compile(r"memory\.json$", re.I),
    re.compile(r"^CHANGELOG", re.I),
    re.compile(r"\.orchestrate_(score_history|experiments)\.json$"),
    re.compile(r"^\.git"),
]

_LARGE_DIFF_FILE_COUNT = 8


def check_contamination(changed_files: list[str]) -> tuple[bool, str]:
    """Returns (contaminated, reason). Not contaminated with an empty
    changed_files list -- that's a different problem (no-op experiment),
    caught elsewhere."""
    if not changed_files:
        return False, ""

    noise = [f for f in changed_files if any(p.search(f) for p in _NOISE_PATTERNS)]
    code_like = [f for f in changed_files if f not in noise]

    if noise and code_like:
        return True, (f"unrelated file(s) mixed into the measured diff: "
                     f"{', '.join(noise)} (alongside {len(code_like)} "
                     "code-like file(s)) -- the delta cannot be cleanly "
                     "attributed to one change")

    if len(changed_files) > _LARGE_DIFF_FILE_COUNT:
        return True, (f"{len(changed_files)} files changed -- too broad to "
                     "plausibly be one isolated change; split into "
                     "separate experiments")

    return False, ""
