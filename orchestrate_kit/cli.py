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


def cmd_transcript(args) -> int:
    from .transcript.analyzer import analyze
    from .transcript.composer import compose, render

    if args.tsub == "analyze":
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
        a = analyze(text)

        print(f"ENGINEERING TRANSCRIPT AUDIT   [{a.overall_verdict}]")
        print(f"  ({a.word_count} words, {a.turn_count} turn(s), "
              f"{a.causal_connectives} causal connective(s))")
        print()
        print("COVERAGE")
        for d in a.dimensions:
            filled = int(d.score // 10)
            bar = "█" * filled + "░" * (10 - filled)
            print(f"  {d.dimension.label:<38} {bar} {d.score:>3.0f}%  "
                  f"weight {d.dimension.weight:.0%}")
        print()

        passed = [d for d in a.dimensions if d.verdict == "PASS"]
        warned = [d for d in a.dimensions if d.verdict == "WARNING"]
        failed = [d for d in a.dimensions if d.verdict == "FAIL"]
        if passed:
            print("PASS")
            for d in passed:
                print(f"  ✓ {d.dimension.label}")
        if warned:
            print("WARNING")
            for d in warned:
                print(f"  • {d.dimension.label}"
                      + (f" -- missing: {', '.join(d.missing)}" if d.missing else ""))
        if failed:
            print("FAIL")
            for d in failed:
                print(f"  ✗ {d.dimension.label}"
                      + (f" -- missing: {', '.join(d.missing)}" if d.missing else ""))

        print()
        print("EVIDENCE CHAIN  (Problem -> Hypothesis -> Implementation -> "
              "Measurement -> Regression -> Decision -> Verification)")
        chain_str = "  ".join(
            (f"✓{n.name}" if n.present else f"✗{n.name}")
            for n in a.chain.nodes)
        print(f"  {chain_str}")
        print(f"  {a.chain.present_count}/7 present"
              + (", in plausible order" if a.chain.in_order and a.chain.present_count > 1
                 else ""))
        print("  Presence-plus-order, not a real causal graph -- this checks "
              "whether the vocabulary for each link appears in a plausible "
              "sequence, not that the reasoning genuinely connects them.")

        if a.notes:
            print()
            print("NOTES")
            for n in a.notes:
                print(f"  • {n}")

        print()
        print("This scores the SHAPE of the transcript -- ownership "
              "language, named alternatives, reported measurements, named "
              "risk mechanisms, causal connectives -- not whether the "
              "underlying claims are true, and it is NOT a prediction of "
              "your real HackerRank score (no ground-truth graded "
              "transcript exists to calibrate against). Use it as a "
              "self-review checklist, not a scoreboard.")
        return 0

    if args.tsub == "compose":
        mem = _memory(args)
        cp = compose(" ".join(args.goal), stage=args.stage or "", memory=mem)
        print(render(cp))
        return 0

    if args.tsub == "blueprints":
        from .transcript.blueprints import BLUEPRINTS
        for b in BLUEPRINTS:
            print(f"{b.key:<22} {b.stage:<14} {b.label}")
        return 0

    return 1


def cmd_interview(args) -> int:
    from .judge.engine import run_terminal
    return run_terminal(
        persona_key=args.persona, difficulty_key=args.difficulty,
        topics=args.topics or None, n=args.questions,
        learn=args.learn, panel=args.panel, seed=args.seed,
        save_path=args.save)


def _load_interview_answers(interview_path: Path | None) -> list[str] | None:
    if interview_path is None or not interview_path.exists():
        return None
    import json
    try:
        record = json.loads(interview_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return [a.get("text", "") for a in record.get("answers", [])] or None


def cmd_score(args) -> int:
    from .score.scoreboard import build_scorecard, counterfactual, render_scoreboard

    repo_root = Path(args.repo)
    transcript_path = Path(args.transcript) if args.transcript else None
    interview_path = Path(args.interview_result) if args.interview_result else None

    if getattr(args, "audit", False):
        from .score.health import render_health_report
        print(render_health_report())
        return 0

    card = build_scorecard(repo_root, python=args.python,
                           transcript_path=transcript_path,
                           interview_result_path=interview_path)
    if args.official_score is not None:
        card.official_score = args.official_score

    if getattr(args, "what_if", None):
        sig, delta_s = args.what_if
        result = counterfactual(card, sig, float(delta_s))
        if "error" in result:
            print(result["error"])
            return 1
        if result["impact"] is None:
            print(f"{result['reason']}")
            return 0
        print(f"CURRENT: {result['label']} = {result['current_score']:.1f}/100")
        print(f"IF IT CHANGES BY {result['delta_requested']:+.1f}:")
        print(f"  EXPECTED WEIGHTED IMPACT ON OVERALL SCORE: "
             f"{result['weighted_impact']:+.2f}")
        print(f"  (signal weight: {result['weight'] * 100:.0f}%; this "
             "assumes the change is achievable -- it is not a prediction "
             "that it will happen)")
        return 0

    interview_answers = _load_interview_answers(interview_path)
    print(render_scoreboard(card, repo_root, save_history=not args.no_history,
                           transcript_path=transcript_path,
                           interview_answers=interview_answers))
    return 0


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
        central = mem.centrality()
        for e in sorted(mem.entries.values(), key=lambda x: (x.phase, x.key)):
            flag = "REJ" if e.status == "rejected" else "   "
            cited = f" <-{central[e.key]}" if central.get(e.key) else ""
            print(f"{flag} {e.key:<32} {e.title[:44]}{cited}")
        print(f"\n{len(mem.entries)} entries · {len(mem.rejections())} rejections "
              f"· '<-N' = referenced by N other entries (depends_on/supersedes)")
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
        ok = True

        files_report = mem.verify_files(repo)
        print(f"{files_report['with_files']}/{files_report['total_entries']} entries "
              f"cite files ({files_report['without_files']} describe a different "
              f"codebase or have no file reference — not counted as failures)")
        if files_report["missing"]:
            ok = False
            print(f"  {len(files_report['missing'])} cited path(s) do not exist:")
            for key, f in files_report["missing"]:
                print(f"    {key}: {f}")

        commits_report = mem.verify_commits(repo)
        print(f"{commits_report['with_commit']}/{commits_report['total_entries']} "
              f"entries cite a commit ({commits_report['without_commit']} have no "
              f"provenance recorded — not counted as failures)")
        if commits_report["missing"]:
            ok = False
            if commits_report["shallow_clone"]:
                print("  NOTE: this is a shallow git clone — a cited commit "
                      "reported missing below may simply not be fetched, not "
                      "invalid. Run `git fetch --unshallow` and retry before "
                      "treating this as a real provenance failure.")
            print(f"  {len(commits_report['missing'])} cited commit(s) not found "
                  f"in this repository's history:")
            for key, c in commits_report["missing"]:
                print(f"    {key}: {c}")

        if ok:
            print("clean" if (files_report["with_files"] or commits_report["with_commit"])
                  else "nothing to verify — no entry cites a file or commit in this repo")
        return 0 if ok else 1

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
    i.add_argument("--save", default=None,
                   help="write the final score to this JSON path, so "
                        "`orchestrate score --interview-result <path>` "
                        "can report it instead of UNKNOWN")
    i.set_defaults(fn=cmd_interview)

    sc = sub.add_parser("score",
                        help="estimated Orchestrate scoreboard (4 published signals)")
    sc.add_argument("--repo", default=".")
    sc.add_argument("--python", default="python")
    sc.add_argument("--transcript", default=None,
                    help="chat transcript file for the Chat Transcript signal")
    sc.add_argument("--interview-result", default=None,
                    help="JSON saved by `orchestrate interview --save <path>`")
    sc.add_argument("--official-score", type=float, default=None,
                    help="your real HackerRank score, if you have one, for "
                         "calibration comparison only")
    sc.add_argument("--no-history", action="store_true",
                    help="do not record this run in the local score history")
    sc.add_argument("--what-if", nargs=2, metavar=("SIGNAL", "DELTA"),
                    help="e.g. --what-if output +5 -- shows the weighted "
                         "impact IF that signal moved by DELTA points; "
                         "does not predict whether it's achievable")
    sc.add_argument("--audit", action="store_true",
                    help="run the score engine's own health check "
                         "(adversarial self-test) instead of scoring a repo")
    sc.set_defaults(fn=cmd_score)

    t = sub.add_parser("transcript",
                       help="chat-transcript scoring, prompt blueprints, composer")
    ts = t.add_subparsers(dest="tsub", required=True)
    ta = ts.add_parser("analyze",
                       help="score a transcript file against the published rubric")
    ta.add_argument("file")
    tc = ts.add_parser("compose",
                       help="generate a prompt from a blueprint + Engineering Memory")
    tc.add_argument("goal", nargs="+")
    tc.add_argument("--stage", default="",
                    choices=["", "understanding", "design", "planning",
                             "implementation", "verification", "release"])
    ts.add_parser("blueprints", help="list every available blueprint")
    t.set_defaults(fn=cmd_transcript, repo=".")

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
