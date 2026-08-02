"""Plugin contract.

The core knows nothing about any specific domain. It knows how to run Audits
against a RepoContext and aggregate Findings. Everything domain-specific --
HackerRank Orchestrate, RAG, agents, classifiers -- lives in a plugin.

Design rule: an Audit is BLACK BOX by default. It is handed a repository path
and the ability to run commands and read files. An audit that needs to import
the target's internals must declare `requires_import = True`, so a repository
that does not expose them degrades to the portable checks instead of erroring.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Protocol


class Severity(str, Enum):
    """Ordered. `BLOCKER` means do not ship."""

    BLOCKER = "blocker"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(str, Enum):
    """How strongly the evidence supports the finding.

    MEASURED  a number was produced by executing something
    OBSERVED  read directly out of a file or command output
    INFERRED  concluded from reasoning over the above
    UNKNOWN   could not be determined -- reported, never guessed
    """

    MEASURED = "measured"
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass
class Finding:
    """One claim, with the evidence that supports it.

    `evidence` is mandatory and is meant to be the literal command output or
    file excerpt. A Finding without evidence is an opinion, and the reporter
    marks it as such rather than presenting it as fact.
    """

    title: str
    severity: Severity
    confidence: Confidence
    evidence: str
    detail: str = ""
    remediation: str = ""
    where: str = ""
    memory_key: str = ""  # links to an EngineeringMemory entry, if one exists


@dataclass
class AuditResult:
    audit: str
    category: str
    passed: bool
    findings: list[Finding] = field(default_factory=list)
    metrics: dict[str, float | int | str] = field(default_factory=dict)
    duration_s: float = 0.0
    skipped: str = ""  # non-empty means the audit could not run, and why


@dataclass
class RepoContext:
    """Everything an audit is allowed to assume about the target."""

    root: Path
    python: str = "python"
    timeout_s: int = 900
    env_overrides: dict[str, str] = field(default_factory=dict)

    def run(self, *args: str, timeout: int | None = None) -> subprocess.CompletedProcess:
        """Run a command in the repo root with a hermetic-ish environment."""
        import os

        env = dict(os.environ)
        # Credentials are cleared by default: an evaluation that depends on the
        # operator's API keys is not reproducible (PLAYBOOK P10).
        for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                    "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(key, None)
        env.update(self.env_overrides)
        return subprocess.run(list(args), cwd=str(self.root), capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              env=env, timeout=timeout or self.timeout_s)

    def read(self, rel: str) -> str:
        p = self.root / rel
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def exists(self, rel: str) -> bool:
        return (self.root / rel).exists()

    def glob(self, pattern: str) -> list[Path]:
        return sorted(self.root.glob(pattern))


class Audit(Protocol):
    """One check. Must never raise; failure is reported, not thrown."""

    name: str
    category: str
    requires_import: bool

    def run(self, ctx: RepoContext) -> AuditResult: ...


@dataclass
class SimpleAudit:
    """Adapter so a plain function can be an Audit."""

    name: str
    category: str
    fn: Callable[[RepoContext], AuditResult]
    requires_import: bool = False

    def run(self, ctx: RepoContext) -> AuditResult:
        start = time.time()
        try:
            result = self.fn(ctx)
        except Exception as exc:  # noqa: BLE001 -- an audit crash is a finding
            result = AuditResult(
                audit=self.name, category=self.category, passed=False,
                findings=[Finding(
                    title=f"audit '{self.name}' crashed",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.OBSERVED,
                    evidence=f"{type(exc).__name__}: {exc}",
                    detail="The audit itself failed. Per PLAYBOOK P6 this is "
                           "reported, never silently treated as a pass.",
                )])
        result.duration_s = time.time() - start
        return result


class Plugin(Protocol):
    """A domain. Supplies audits and, optionally, seed memory."""

    name: str
    description: str

    def audits(self) -> Iterable[Audit]: ...

    def detect(self, ctx: RepoContext) -> bool:
        """True when this plugin applies to the given repository."""
        ...
