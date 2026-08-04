"""The `orchestrate` command.

    orchestrate evaluate <repo>          run every applicable audit
    orchestrate certify  <repo>          evaluate, but exit non-zero on ANY finding
    orchestrate release  <repo>          the pre-submission gate
    orchestrate mentor  "add OCR"        should I build this?
    orchestrate interview                adaptive judge simulator
    orchestrate memory  <sub>            recall · why-not · list · seed · add
    orchestrate graph                    decision graph (Mermaid)
    orchestrate viz     <name>           generated diagrams
    orchestrate selftest                 negative control: can the evaluator fail?
    orchestrate plugin new <name>        scaffold a plugin + its negative control

Exit codes are the contract, because these run in CI:
    0  clean
    1  usage / internal error
    2  release blocker
    3  findings present but none blocking (certify only)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .evaluator import Evaluator, RepoContext, Severity, render_markdown, render_terminal
from .evaluator.plugins.generic import GenericPlugin
from .evaluator.plugins.orchestrate import OrchestratePlugin
from .memory.store import EngineeringMemory, MemoryEntry, default_path
from .mentor.engine import Mentor
from .viz import render as viz

if hasattr(sys.stdout, "reconfigure"):      # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _memory(args) -> EngineeringMemory:
    repo = Path(getattr(args, "repo", ".") or ".").resolve()
    path = Path(args.memory) if getattr(args, "memory", None) else default_path(repo)
    return EngineeringMemory(path)


def _evaluator(repo: Path, mem: EngineeringMemory) -> Evaluator:
    ctx = RepoContext(root=repo, python=sys.executable)
    ev = Evaluator(ctx, mem)
    ev.register(GenericPlugin())
    ev.register(OrchestratePlugin())
    return ev


# ======================================================================
def cmd_evaluate(args) -> int:
    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"no such repository: {repo}", file=sys.stderr)
        return 1
    mem = _memory(args)
    result = _evaluator(repo, mem).run(only=set(args.only) if args.only else None)

    print(render_terminal(result))
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(result, mem), encoding="utf-8")
        print(f"\nwritten: {args.markdown}")
    return 2 if result.blockers else 0


def cmd_certify(args) -> int:
    """Stricter than evaluate: ANY finding above INFO fails the gate.

    `evaluate` answers "is this shippable". `certify` answers "is this clean".
    They are different questions and conflating them is how a MEDIUM finding
    survives ten releases."""
    repo = Path(args.repo).resolve()
    mem = _memory(args)
    result = _evaluator(repo, mem).run()
    print(render_terminal(result))

    findings = [f for r in result.results for f in r.findings
                if f.severity is not Severity.INFO]
    skipped = [r for r in result.results if r.skipped]

    print()
    print(f"CERTIFY: {len(findings)} finding(s) above INFO, "
          f"{len(result.blockers)} blocker(s), {len(skipped)} audit(s) skipped")
    for r in skipped:
        print(f"  SKIPPED  {r.audit}: {r.skipped}")
    if skipped:
        print("  A skipped audit is an UNKNOWN, not a pass.")
    if result.blockers:
        return 2
    return 3 if findings else 0


def cmd_release(args) -> int:
    """The pre-submission gate: the checks whose failure is unrecoverable
    AFTER you have submitted."""
    repo = Path(args.repo).resolve()
    mem = _memory(args)
    result = _evaluator(repo, mem).run()

    print("=" * 84)
    print(f"RELEASE GATE  ::  {repo.name}")
    print("=" * 84)
    print(render_terminal(result))

    gates = [
        ("no release blockers", not result.blockers,
         f"{len(result.blockers)} blocker(s)"),
        ("no audit silently skipped",
         not [r for r in result.results if r.skipped],
         f"{sum(1 for r in result.results if r.skipped)} skipped"),
        ("no UNKNOWN-confidence findings left unresolved",
         not result.unknowns, f"{len(result.unknowns)} unknown(s)"),
    ]
    print()
    print("GATES")
    ok = True
    for label, passed, detail in gates:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}   ({detail})")
        ok &= passed

    print()
    print("MANUAL — these cannot be automated and must not be skipped:")
    for item in (
        "Read the submission log/transcript end to end for leaked secrets.",
        "Confirm the artifact was regenerated from a FRESH CLONE, not in place.",
        "Make the authorship attestation yourself. No tool may make it for you.",
        "Re-read every numeric claim in your writeup and confirm you can source it.",
    ):
        print(f"  [ ] {item}")

    print()
    print("=" * 84)
    print(f"  {'GATES PASSED' if ok else 'GATES FAILED'} — automated portion only.")
    print("  A passing gate is evidence, not permission. The manual items above")
    print("  are the ones that have actually sunk submissions.")
    print("=" * 84)
    return 0 if ok else 2


# ======================================================================
def cmd_plugin(args) -> int:
    from .scaffold import new_plugin
    written = new_plugin(args.name, args.detect, args.category,
                         Path(args.dest), args.title or "")
    print(f"scaffolded plugin {args.name!r}:")
    for p in written:
        print(f"  {p}")
    print()
    print("The generated audit FAILS on purpose, and one test is marked xfail.")
    print("Your first run should be red. Making it green is the exercise --")
    print("a plugin whose audits have never produced a finding cannot be")
    print("trusted to produce one when it matters.")
    return 0


def cmd_selftest(args) -> int:
    from .selftest import run
    print("=" * 84)
    print("NEGATIVE CONTROL — can the evaluator actually fail?")
    print("=" * 84)
    return run()


def cmd_mentor(args) -> int:
    mem = _memory(args)
    if not mem.entries:
        print("warning: Engineering Memory is empty. Prior art will be blank.\n"
              "         run `orchestrate memory seed` first.\n", file=sys.stderr)
    advice = Mentor(mem).advise(" ".join(args.proposal))
    print(Mentor(mem).render(advice))
    return 2 if advice.verdict == "BLOCKED-BY-PRIOR-ART" else 0


def cmd_interview(args) -> int:
    from .judge.engine import run_terminal
    return run_terminal(
        persona_key=args.persona, difficulty_key=args.difficulty,
        topics=args.topics or None, n=args.questions,
        learn=args.learn, panel=args.panel, seed=args.seed)


def cmd_memory(args) -> int:
    mem = _memory(args)

    if args.sub == "seed":
        from .memory.seed import seed
        n = seed(mem)
        print(f"seeded {n} entries -> {mem.path}")
        print(f"  rejections: {len(mem.rejections())}")
        print(f"  with a reconsideration condition: "
              f"{sum(1 for e in mem.rejections() if e.reconsider_if)}/"
              f"{len(mem.rejections())}")
        return 0

    if args.sub == "list":
        if not mem.entries:
            print("empty. run `orchestrate memory seed`")
            return 0
        for e in sorted(mem.entries.values(), key=lambda x: (x.phase, x.key)):
            flag = "REJ" if e.status == "rejected" else "   "
            print(f"{flag} {e.key:<32} {e.title[:44]}")
        print(f"\n{len(mem.entries)} entries · {len(mem.rejections())} rejections")
        print("tags: " + ", ".join(f"{k}({v})" for k, v in list(mem.tags().items())[:14]))
        return 0

    if args.sub == "why-not":
        topic = " ".join(args.query)
        hits = mem.why_not(topic)
        if not hits:
            print(f"No RECORDED rejection matching {topic!r}.")
            print("That means this repository has no record — not that the idea "
                  "is good. Run `orchestrate mentor` for the risk analysis.")
            return 0
        for e in hits:
            print(f"\n{e.key}  {e.title}   [rejected]")
            print(f"  because : {e.root_cause}")
            for b in e.benchmarks:
                print(f"  measured: {b.line()}")
            if e.rejected:
                print(f"  variants tried: {'; '.join(e.rejected)}")
            if e.reconsider_if:
                print(f"  RECONSIDER IF: {e.reconsider_if}")
            if e.lesson:
                print(f"  lesson  : {e.lesson}")
        return 0

    if args.sub == "recall":
        query = " ".join(args.query)
        for e in mem.search(query, limit=args.limit):
            flag = "REJECTED" if e.status == "rejected" else "shipped"
            print(f"\n[{flag}] {e.key}  {e.title}")
            if e.problem:
                print(f"  problem : {e.problem}")
            if e.chosen:
                print(f"  chosen  : {e.chosen}")
            for b in e.benchmarks:
                print(f"  measured: {b.line()}")
            if e.lesson:
                print(f"  lesson  : {e.lesson}")
        return 0

    if args.sub == "verify":
        repo = Path(getattr(args, "repo", ".") or ".").resolve()
        report = mem.verify_files(repo)
        print(f"{report['with_files']}/{report['total_entries']} entries cite files "
              f"({report['without_files']} describe a different codebase or "
              f"have no file reference — not counted as failures)")
        if report["missing"]:
            print(f"\n{len(report['missing'])} cited path(s) do not exist:")
            for key, f in report["missing"]:
                print(f"  {key}: {f}")
            return 1
        print("all cited files exist" if report["with_files"] else
              "nothing to verify — no entry cites a file in this repo")
        return 0

    if args.sub == "add":
        entry = MemoryEntry(
            key=args.key, kind=args.kind, status=args.status,
            title=args.title or args.key, problem=args.problem,
            root_cause=args.because, chosen=args.chosen,
            evidence=args.evidence, reconsider_if=args.reconsider_if,
            tags=args.tags or [], phase=args.phase, lesson=args.lesson)
        if entry.status == "rejected" and not entry.reconsider_if:
            print("refusing: a rejection without --reconsider-if is a prejudice, "
                  "not a decision.\nState what would change the answer.",
                  file=sys.stderr)
            return 1
        mem.add(entry)
        mem.save()
        print(f"added {entry.key} -> {mem.path}")
        return 0

    return 1


def cmd_graph(args) -> int:
    mem = _memory(args)
    text = (viz.timeline(mem) if args.timeline
            else viz.decisions(mem, args.focus or ""))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        print(text)
    return 0


def cmd_viz(args) -> int:
    if args.list or not args.name:
        for key, (label, _) in viz.DIAGRAMS.items():
            print(f"  {key:<14} {label}")
        print("  decisions      Decision graph from Engineering Memory")
        print("  timeline       Engineering history by phase")
        return 0

    if args.name in ("decisions", "timeline"):
        mem = _memory(args)
        text = viz.timeline(mem) if args.name == "timeline" else viz.decisions(mem)
    elif args.name in viz.DIAGRAMS:
        text = viz.DIAGRAMS[args.name][1]()
    elif args.name == "all":
        outdir = Path(args.out or "diagrams")
        outdir.mkdir(parents=True, exist_ok=True)
        mem = _memory(args)
        written = []
        for key, (_, fn) in viz.DIAGRAMS.items():
            p = outdir / f"{key}.mmd"
            p.write_text(fn(), encoding="utf-8")
            written.append(p)
        for key, fn in (("decisions", lambda: viz.decisions(mem)),
                        ("timeline", lambda: viz.timeline(mem))):
            p = outdir / f"{key}.mmd"
            p.write_text(fn(), encoding="utf-8")
            written.append(p)
        print(f"wrote {len(written)} diagrams -> {outdir}")
        return 0
    else:
        print(f"unknown diagram: {args.name}", file=sys.stderr)
        return 1

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        print(text)
    return 0


# ======================================================================
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="orchestrate",
        description="Infrastructure for building AI systems you can defend.")
    p.add_argument("--memory", help="path to memory.json (default: bundled)")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("evaluate", help="run every applicable audit")
    e.add_argument("repo", nargs="?", default=".")
    e.add_argument("--markdown", help="also write a markdown report")
    e.add_argument("--only", nargs="*", help="restrict to these categories")
    e.set_defaults(fn=cmd_evaluate)

    c = sub.add_parser("certify", help="stricter gate: any finding fails")
    c.add_argument("repo", nargs="?", default=".")
    c.set_defaults(fn=cmd_certify)

    r = sub.add_parser("release", help="pre-submission gate")
    r.add_argument("repo", nargs="?", default=".")
    r.set_defaults(fn=cmd_release)

    pl = sub.add_parser("plugin", help="scaffold a new evaluator plugin")
    pls = pl.add_subparsers(dest="psub", required=True)
    pn = pls.add_parser("new")
    pn.add_argument("name")
    pn.add_argument("--detect", required=True,
                    help="a path whose presence identifies this domain "
                         "(SHAPE, never a repo name)")
    pn.add_argument("--category", default="evaluation")
    pn.add_argument("--title", default="")
    pn.add_argument("--dest", default="plugins")
    pl.set_defaults(fn=cmd_plugin, repo=".")

    st = sub.add_parser("selftest",
                        help="inject defects and prove the evaluator catches them")
    st.set_defaults(fn=cmd_selftest, repo=".")

    m = sub.add_parser("mentor", help='e.g. orchestrate mentor "add OCR"')
    m.add_argument("proposal", nargs="+")
    m.add_argument("--repo", default=".")
    m.set_defaults(fn=cmd_mentor)

    i = sub.add_parser("interview", help="adaptive judge simulator")
    i.add_argument("--persona", default="skeptic",
                   choices=["architect", "skeptic", "security", "practitioner"])
    i.add_argument("--difficulty", default="standard",
                   choices=["warmup", "standard", "hard", "adversarial"])
    i.add_argument("--topics", nargs="*", help="restrict to these topics")
    i.add_argument("-n", "--questions", type=int, default=8)
    i.add_argument("--learn", action="store_true",
                   help="coach after every answer")
    i.add_argument("--panel", action="store_true",
                   help="rotate all four judges")
    i.add_argument("--seed", type=int, default=None)
    i.set_defaults(fn=cmd_interview)

    mem = sub.add_parser("memory", help="institutional knowledge")
    ms = mem.add_subparsers(dest="sub", required=True)
    ms.add_parser("seed", help="write the reference corpus")
    ms.add_parser("list", help="list every entry")
    ms.add_parser("verify", help="do the files entries cite still exist?")
    for name in ("recall", "why-not"):
        s = ms.add_parser(name)
        s.add_argument("query", nargs="+")
        s.add_argument("--limit", type=int, default=5)
    add = ms.add_parser("add", help="record a decision")
    add.add_argument("key")
    add.add_argument("--kind", default="decision", choices=["decision", "finding"])
    add.add_argument("--status", default="accepted",
                     choices=["accepted", "rejected", "superseded"])
    add.add_argument("--title")
    add.add_argument("--problem", default="")
    add.add_argument("--because", default="", help="root cause")
    add.add_argument("--chosen", default="")
    add.add_argument("--evidence", default="")
    add.add_argument("--reconsider-if", dest="reconsider_if", default="",
                     help="REQUIRED for a rejection")
    add.add_argument("--tags", nargs="*")
    add.add_argument("--phase", default="")
    add.add_argument("--lesson", default="")
    mem.set_defaults(fn=cmd_memory, repo=".")

    g = sub.add_parser("graph", help="decision graph as Mermaid")
    g.add_argument("--focus", help="restrict to entries matching this topic")
    g.add_argument("--timeline", action="store_true")
    g.add_argument("--out")
    g.set_defaults(fn=cmd_graph, repo=".")

    v = sub.add_parser("viz", help="generated diagrams")
    v.add_argument("name", nargs="?")
    v.add_argument("--list", action="store_true")
    v.add_argument("--out")
    v.set_defaults(fn=cmd_viz, repo=".")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
