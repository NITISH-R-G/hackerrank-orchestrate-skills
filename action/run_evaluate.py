"""The Action's actual work, as a script rather than terminal-scraping.

`orchestrate evaluate` prints human-readable text; parsing that with grep in
a composite action's bash step is exactly the kind of fragile regex-over-
formatted-output pattern this project's own audits exist to catch. This
script instead calls the same `Evaluator` the CLI calls, gets back the real
`Evaluation` object, and writes GitHub Actions outputs directly from its
structured fields.

Usage: python run_evaluate.py <repo-path> <report-path>
Writes GITHUB_OUTPUT: score, verdict, blockers, findings
Exit code: 0 clean, 2 if any blocker (matches `orchestrate evaluate`'s own
contract, so a consumer piping this into `exit-code` checks sees the same
number either way).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrate_kit.evaluator import Evaluator, RepoContext, render_markdown  # noqa: E402
from orchestrate_kit.evaluator.plugins.generic import GenericPlugin  # noqa: E402
from orchestrate_kit.evaluator.plugins.orchestrate import OrchestratePlugin  # noqa: E402
from orchestrate_kit.memory.store import EngineeringMemory, default_path  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: run_evaluate.py <repo-path> <report-path>", file=sys.stderr)
        return 1
    repo = Path(sys.argv[1]).resolve()
    report_path = Path(sys.argv[2])

    mem = EngineeringMemory(default_path(repo))
    ctx = RepoContext(root=repo, python=sys.executable)
    ev = Evaluator(ctx, mem)
    ev.register(GenericPlugin())
    ev.register(OrchestratePlugin())
    result = ev.run()

    report_path.write_text(render_markdown(result, mem), encoding="utf-8")

    outputs = {
        "score": result.overall,
        "verdict": result.verdict,
        "blockers": len(result.blockers),
        "findings": sum(len(r.findings) for r in result.results),
        "report-path": str(report_path),
    }
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            for k, v in outputs.items():
                f.write(f"{k}={v}\n")

    print(f"{result.verdict}  score {result.overall}/100  "
          f"blockers={len(result.blockers)}  report={report_path}")
    for b in result.blockers:
        print(f"  BLOCKER: {b.title}")

    return 2 if result.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
