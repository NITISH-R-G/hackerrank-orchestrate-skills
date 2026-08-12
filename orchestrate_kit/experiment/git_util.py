"""Git provenance for experiments. "The working tree looked different" is
not evidence -- a SHA and a diff are. Every function here fails soft
(returns None / empty / True-for-dirty) rather than raising, because a
missing git repo must degrade the experiment engine's confidence, not
crash it."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run(repo_root: Path, args: list[str], raw: bool = False) -> str | None:
    """raw=True preserves leading whitespace -- `git status --porcelain`
    pads its 2-char status code with a leading space for an unstaged-only
    change (" M path"), and a blanket .strip() on the whole multi-line
    string quietly eats that leading space off only the FIRST line,
    misaligning every fixed-width `line[3:]` parse downstream. Confirmed
    by direct reproduction: it silently turned "dataset/output.csv" into
    "ataset/output.csv"."""
    try:
        r = subprocess.run(["git", *args], cwd=str(repo_root),
                          capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.rstrip("\n") if raw else r.stdout.strip()


def is_git_repo(repo_root: Path) -> bool:
    return _run(repo_root, ["rev-parse", "--is-inside-work-tree"]) == "true"


def current_sha(repo_root: Path) -> str | None:
    return _run(repo_root, ["rev-parse", "HEAD"])


def current_branch(repo_root: Path) -> str | None:
    return _run(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])


def is_dirty(repo_root: Path) -> bool:
    out = _run(repo_root, ["status", "--porcelain"], raw=True)
    return bool(out)


def changed_files_since(repo_root: Path, baseline_sha: str | None) -> list[str]:
    """Union of committed changes since baseline_sha AND any uncommitted
    working-tree changes -- an experiment can be measured against either a
    committed SHA or a dirty working tree, and contamination checking must
    see both."""
    files: set[str] = set()
    if baseline_sha:
        committed = _run(repo_root, ["diff", "--name-only", baseline_sha, "--"], raw=True)
        if committed:
            files.update(committed.splitlines())
    status = _run(repo_root, ["status", "--porcelain"], raw=True)
    if status:
        for line in status.splitlines():
            if not line:
                continue
            # porcelain format: "XY path" or "XY orig -> path" for renames
            path = line[3:].split(" -> ")[-1].strip()
            if path:
                files.add(path)
    return sorted(files)


def diff_stat(repo_root: Path, baseline_sha: str | None) -> dict[str, tuple[int, int]]:
    """{path: (added, removed)} from `git diff --numstat`, committed and
    working-tree combined (working tree overrides committed for the same
    path -- it's the more current number)."""
    out: dict[str, tuple[int, int]] = {}
    if baseline_sha:
        text = _run(repo_root, ["diff", "--numstat", baseline_sha, "--"])
        _parse_numstat(text, out)
    text = _run(repo_root, ["diff", "--numstat"])
    _parse_numstat(text, out)
    return out


def _parse_numstat(text: str | None, out: dict[str, tuple[int, int]]) -> None:
    if not text:
        return
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        try:
            out[path] = (int(added), int(removed))
        except ValueError:
            out[path] = (0, 0)  # binary file ("-" counts)
