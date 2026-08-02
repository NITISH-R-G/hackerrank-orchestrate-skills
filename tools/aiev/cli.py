"""aiev — evidence-driven evaluation for AI systems.

    python -m aiev evaluate <repo>            run every applicable audit
    python -m aiev why-not <topic> [repo]     why wasn't X shipped?
    python -m aiev recall <query> [repo]      has this happened before?
    python -m aiev graph [repo]               decision graph (Mermaid)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core.evaluator import Evaluator
from .core.memory import EngineeringMemory
from .core.plugin_api import RepoContext
from .core.reporting import render_markdown, render_terminal
from .plugins.generic import GenericPlugin
from .plugins.orchestrate import OrchestratePlugin

PLUGINS = [GenericPlugin(), OrchestratePlugin()]


def _memory(repo: Path) -> EngineeringMemory:
    """Memory lives with the repo under audit, so it is reviewable and diffable."""
    return EngineeringMemory(repo / ".aiev" / "memory.json")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aiev", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evaluate")
    ev.add_argument("repo", nargs="?", default=".")
    ev.add_argument("--only", help="comma-separated categories")
    ev.add_argument("--markdown", metavar="PATH", help="write full report here")
    ev.add_argument("--python", default=sys.executable)

    wn = sub.add_parser("why-not"); wn.add_argument("topic"); wn.add_argument("repo", nargs="?", default=".")
    rc = sub.add_parser("recall"); rc.add_argument("query"); rc.add_argument("repo", nargs="?", default=".")
    gr = sub.add_parser("graph"); gr.add_argument("repo", nargs="?", default=".")

    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    mem = _memory(repo)

    if args.cmd == "why-not":
        hits = mem.why_not(args.topic)
        if not hits:
            print(f"No recorded rejection matching {args.topic!r}.")
            print("That is not the same as 'it was never considered'.")
            return 1
        for m in hits:
            print(f"\n{m.key}  {m.title}   [{m.status}]")
            print(f"  reason   : {m.root_cause or m.problem}")
            print(f"  evidence : {m.evidence}")
            if m.lesson:
                print(f"  lesson   : {m.lesson}")
        return 0

    if args.cmd == "recall":
        hits = mem.recall(args.query, limit=5)
        if not hits:
            print("No prior art found.")
            return 1
        for m in hits:
            print(f"\n{m.key}  {m.title}")
            if m.problem:
                print(f"  problem : {m.problem}")
            if m.chosen:
                print(f"  fixed by: {m.chosen}")
            if m.rejected:
                print(f"  rejected: {'; '.join(m.rejected)}")
            if m.evidence:
                print(f"  evidence: {m.evidence}")
        return 0

    if args.cmd == "graph":
        print(mem.decision_graph())
        return 0

    ctx = RepoContext(root=repo, python=args.python)
    runner = Evaluator(ctx, memory=mem)
    for p in PLUGINS:
        runner.register(p)
    only = set(args.only.split(",")) if args.only else None
    result = runner.run(only=only)

    print(render_terminal(result))
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(result, mem), encoding="utf-8")
        print(f"\nfull report -> {args.markdown}")
    return 0 if not result.blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
