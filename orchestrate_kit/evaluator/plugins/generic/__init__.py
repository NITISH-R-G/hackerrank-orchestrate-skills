"""Generic plugin: audits that apply to ANY repository.

Everything here is black box. It clones, runs commands, reads files, and diffs
artifacts. It never imports the target's code, so it works on a Python router, a
TypeScript agent, or a Rust CLI with only the command names changed.

These implement the portable half of the PLAYBOOK:
  P15 fresh-clone simulation
  P16 stale artifacts
  P17 documentation is production code
  P10 hermetic / order-independent tests
  P12 dataset coupling (row order, timestamps, filenames)
  determinism, secrets, packaging hygiene
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path

from ...plugin_api import (
    AuditResult,
    Confidence,
    Finding,
    RepoContext,
    Severity,
    SimpleAudit,
)


def _ok(name: str, category: str, **metrics) -> AuditResult:
    return AuditResult(audit=name, category=category, passed=True, metrics=metrics)


# --------------------------------------------------------------------------
def audit_git_hygiene(ctx: RepoContext) -> AuditResult:
    res = AuditResult("git-hygiene", "repository", True)
    st = ctx.run("git", "status", "--porcelain", "--untracked-files=no")
    dirty = [ln for ln in st.stdout.splitlines() if ln.strip()]
    if dirty:
        res.passed = False
        res.findings.append(Finding(
            "uncommitted changes to tracked files", Severity.HIGH,
            Confidence.OBSERVED, evidence="\n".join(dirty[:10]),
            remediation="Commit or revert before evaluating; otherwise the "
                        "artifacts you ship may not match the code you tested.",
        ))
    tracked = ctx.run("git", "ls-files").stdout.splitlines()
    junk = [f for f in tracked if "__pycache__" in f or f.endswith((".pyc", ".pyo"))]
    if junk:
        res.passed = False
        res.findings.append(Finding(
            "build artifacts are tracked in git", Severity.LOW,
            Confidence.OBSERVED, evidence=str(junk[:8]),
            remediation="Add to .gitignore and `git rm --cached`.",
        ))
    res.metrics = {"tracked_files": len(tracked), "dirty": len(dirty)}
    return res


# --------------------------------------------------------------------------
def audit_secrets(ctx: RepoContext) -> AuditResult:
    """Real credentials, in the tree and in history."""
    res = AuditResult("secrets", "security", True)
    pat = re.compile(
        r"(gsk_[A-Za-z0-9]{30,}|AIzaSy[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9]{30,}"
        r"|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})")
    hits: list[str] = []
    for p in ctx.root.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".mp3", ".wav", ".zip",
                                ".webp", ".avif", ".onnx", ".bin"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pat.search(text):
            hits.append(str(p.relative_to(ctx.root)))
    hist = ctx.run("git", "log", "--all", "-p")
    hist_hits = len(pat.findall(hist.stdout)) if hist.returncode == 0 else 0
    if hits or hist_hits:
        res.passed = False
        res.findings.append(Finding(
            "credential-shaped strings found", Severity.BLOCKER,
            Confidence.OBSERVED,
            evidence=f"files={hits[:5]} history_matches={hist_hits}",
            remediation="Rotate the credential first, then purge. A key in git "
                        "history is compromised even after deletion.",
        ))
    res.metrics = {"files_scanned": "all", "hits": len(hits), "history_hits": hist_hits}
    return res


# --------------------------------------------------------------------------
def audit_fresh_clone(ctx: RepoContext) -> AuditResult:
    """PLAYBOOK P15. The single highest-yield audit in this framework."""
    res = AuditResult("fresh-clone", "release", True)
    tmp = Path(tempfile.mkdtemp(prefix="aiev_clone_"))
    clone = tmp / "repo"
    try:
        r = ctx.run("git", "clone", "--quiet", str(ctx.root), str(clone))
        if r.returncode != 0:
            res.passed = False
            res.findings.append(Finding(
                "repository does not clone", Severity.BLOCKER,
                Confidence.OBSERVED, evidence=r.stderr[-400:]))
            return res

        tracked = [ln for ln in ctx.run("git", "ls-files").stdout.splitlines()]
        src = [f for f in tracked if f.endswith((".py", ".ts", ".js", ".go", ".rs"))]
        res.metrics = {"cloned_files": len(tracked), "source_files": len(src)}

        # A clone containing almost no source is the "nothing was committed"
        # failure -- it looks fine locally and is fatal for anyone else.
        if len(src) < 3:
            res.passed = False
            res.findings.append(Finding(
                "clone contains almost no source files", Severity.BLOCKER,
                Confidence.MEASURED,
                evidence=f"{len(src)} source files tracked out of {len(tracked)}",
                remediation="Your work is probably untracked. Check "
                            "`git status --porcelain | grep '^??'`.",
            ))

        clone_ctx = RepoContext(root=clone, python=ctx.python, timeout_s=ctx.timeout_s)
        # Bare `pytest` is what a reviewer types first.
        pt = clone_ctx.run(ctx.python, "-m", "pytest")
        if pt.returncode not in (0, 5):  # 5 == no tests collected
            res.passed = False
            tail = (pt.stdout or pt.stderr)[-600:]
            res.findings.append(Finding(
                "`pytest` fails from a fresh clone", Severity.HIGH,
                Confidence.MEASURED, evidence=tail,
                remediation="Scope collection (testpaths) and set pythonpath; a "
                            "stray root-level test_*.py can abort the whole run.",
            ))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


# --------------------------------------------------------------------------
def audit_artifact_freshness(ctx: RepoContext, *, artifact: str, command: list[str],
                             out_flag: str = "--out") -> AuditResult:
    """PLAYBOOK P16. Regenerate to a TEMP path and compare (never overwrite)."""
    res = AuditResult("artifact-freshness", "release", True)
    if not ctx.exists(artifact):
        res.passed = False
        res.findings.append(Finding(
            f"artifact missing: {artifact}", Severity.BLOCKER,
            Confidence.OBSERVED, evidence=f"{ctx.root / artifact} does not exist"))
        return res
    tmp = Path(tempfile.mkdtemp(prefix="aiev_art_"))
    try:
        dest = tmp / "regen"
        r = ctx.run(*command, out_flag, str(dest))
        if r.returncode != 0 or not dest.exists():
            res.skipped = "could not regenerate the artifact to compare"
            res.findings.append(Finding(
                "artifact freshness UNKNOWN", Severity.MEDIUM, Confidence.UNKNOWN,
                evidence=(r.stderr or r.stdout)[-400:],
                detail="Reported as unknown rather than assumed fresh."))
            return res
        a = hashlib.sha256((ctx.root / artifact).read_bytes()).hexdigest()
        b = hashlib.sha256(dest.read_bytes()).hexdigest()
        res.metrics = {"committed_sha256": a, "regenerated_sha256": b}
        if a != b:
            res.passed = False
            res.findings.append(Finding(
                f"{artifact} is STALE", Severity.BLOCKER, Confidence.MEASURED,
                evidence=f"committed={a[:16]}...  regenerated={b[:16]}...",
                remediation="Regenerate from the current commit before shipping.",
            ))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


# --------------------------------------------------------------------------
def audit_determinism(ctx: RepoContext, *, command: list[str], artifact: str,
                      runs: int = 3, seeds: tuple[str, ...] = ("0", "1", "random")) -> AuditResult:
    """Same inputs, different processes and hash seeds -> one hash."""
    res = AuditResult("determinism", "determinism", True)
    tmp = Path(tempfile.mkdtemp(prefix="aiev_det_"))
    hashes: dict[str, str] = {}
    try:
        for i, seed in enumerate((list(seeds) * runs)[:runs]):
            dest = tmp / f"run{i}"
            ctx.env_overrides["PYTHONHASHSEED"] = seed
            r = ctx.run(*command, "--out", str(dest))
            if r.returncode != 0 or not dest.exists():
                res.skipped = "target does not support --out; cannot test safely"
                return res
            hashes[f"run{i}(seed={seed})"] = hashlib.sha256(dest.read_bytes()).hexdigest()
        ctx.env_overrides.pop("PYTHONHASHSEED", None)
        distinct = set(hashes.values())
        res.metrics = {"runs": len(hashes), "distinct_hashes": len(distinct)}
        if len(distinct) > 1:
            res.passed = False
            res.findings.append(Finding(
                "output is NOT deterministic across processes", Severity.HIGH,
                Confidence.MEASURED,
                evidence="\n".join(f"{k}: {v[:16]}..." for k, v in hashes.items()),
                remediation="Look for set/dict iteration reaching output, "
                            "unseeded randomness, or a network call on the path.",
            ))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


# --------------------------------------------------------------------------
def audit_doc_claims(ctx: RepoContext) -> AuditResult:
    """PLAYBOOK P17. Numeric claims in docs are assertions; flag unverifiable ones."""
    res = AuditResult("doc-claims", "documentation", True)
    docs = [p for p in ctx.root.rglob("*.md") if ".git" not in p.parts]
    claim = re.compile(r"(\d+(?:\.\d+)?)\s*(ms|s\b|seconds|MB|GB|%|/\d+)")
    claims: list[tuple[str, str]] = []
    for p in docs:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if claim.search(line) and not line.strip().startswith(("|", ">", "#")):
                claims.append((str(p.relative_to(ctx.root)), line.strip()[:100]))
    res.metrics = {"docs": len(docs), "numeric_claims": len(claims)}
    if claims:
        res.findings.append(Finding(
            f"{len(claims)} numeric claims in documentation", Severity.INFO,
            Confidence.OBSERVED,
            evidence="\n".join(f"{f}: {t}" for f, t in claims[:6]),
            detail="Each is an assertion a reviewer can test. Verify every one "
                   "at release time -- stale numbers are defects (P17).",
        ))
    return res


# --------------------------------------------------------------------------
def audit_test_isolation(ctx: RepoContext) -> AuditResult:
    """PLAYBOOK P10 corollary: each test file must pass ALONE."""
    res = AuditResult("test-isolation", "testing", True)
    files = [p for p in ctx.root.rglob("test_*.py") if ".git" not in p.parts]
    if not files:
        res.skipped = "no test files found"
        return res
    failed: list[str] = []
    for p in files:
        r = ctx.run(ctx.python, "-m", "pytest", str(p.relative_to(ctx.root)), "-q")
        if r.returncode not in (0, 5):
            failed.append(str(p.relative_to(ctx.root)))
    res.metrics = {"test_files": len(files), "fail_alone": len(failed)}
    if failed:
        res.passed = False
        res.findings.append(Finding(
            "test files that pass together but FAIL alone", Severity.HIGH,
            Confidence.MEASURED, evidence=str(failed),
            detail="The suite is passing by accident of import order. Renaming "
                   "or deleting one file would break the others.",
            remediation="Set pythonpath/conftest so imports do not depend on "
                        "which file ran first.",
        ))
    return res


AUDITS = [
    SimpleAudit("git-hygiene", "repository", audit_git_hygiene),
    SimpleAudit("secrets", "security", audit_secrets),
    SimpleAudit("fresh-clone", "release", audit_fresh_clone),
    SimpleAudit("doc-claims", "documentation", audit_doc_claims),
    SimpleAudit("test-isolation", "testing", audit_test_isolation),
]


class GenericPlugin:
    name = "generic"
    description = "Portable audits that apply to any repository"

    def audits(self):
        return AUDITS

    def detect(self, ctx: RepoContext) -> bool:
        return True
