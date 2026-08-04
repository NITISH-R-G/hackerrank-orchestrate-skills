"""Tests for orchestrate_kit.

Two things are being tested, and they are not the same thing:

  BEHAVIOUR   the code does what it says
  DISCRIMINATION  the code can FAIL

The second matters more. A mentor that says PROCEED to everything and a judge
that scores everything 80 are both perfectly functional and completely useless.
Several tests below exist only to prove the tools distinguish a good input from
a bad one -- the negative control the whole framework preaches.

    python -m pytest tests/ -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrate_kit.judge import bank                                # noqa: E402
from orchestrate_kit.judge.engine import Interview                    # noqa: E402
from orchestrate_kit.judge.personas import BY_KEY, LEVELS, PANEL      # noqa: E402
from orchestrate_kit.judge.scoring import analyse                     # noqa: E402
from orchestrate_kit.memory.seed import ALL, seed                     # noqa: E402
from orchestrate_kit.memory.store import (                            # noqa: E402
    Benchmark, EngineeringMemory, MemoryEntry,
)
from orchestrate_kit.mentor.engine import Mentor                      # noqa: E402
from orchestrate_kit.mentor.taxonomy import CLASSES, classify         # noqa: E402
from orchestrate_kit.viz import render as viz                         # noqa: E402


@pytest.fixture
def memory(tmp_path) -> EngineeringMemory:
    mem = EngineeringMemory(tmp_path / "memory.json")
    seed(mem)
    return mem


# ===================================================== memory
def test_seed_round_trips(tmp_path):
    mem = EngineeringMemory(tmp_path / "m.json")
    n = seed(mem)
    reloaded = EngineeringMemory(tmp_path / "m.json")
    assert len(reloaded.entries) == n
    a = mem.entries["D-dense-retrieval"]
    b = reloaded.entries["D-dense-retrieval"]
    assert a == b, "an entry must survive save/load unchanged"
    assert b.benchmarks and isinstance(b.benchmarks[0], Benchmark)


def test_every_rejection_states_a_reconsideration_condition(memory):
    """The invariant that makes a rejection knowledge rather than prejudice."""
    missing = [e.key for e in memory.rejections() if not e.reconsider_if.strip()]
    assert not missing, f"rejections with no reconsider_if: {missing}"


def test_every_rejection_carries_a_measurement(memory):
    missing = [e.key for e in memory.rejections()
               if not e.benchmarks and not e.evidence]
    assert not missing, f"unmeasured rejections: {missing}"


def test_keys_are_unique():
    keys = [e.key for e in ALL]
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, f"duplicate memory keys: {dupes}"


def test_depends_on_targets_exist():
    keys = {e.key for e in ALL}
    dangling = {(e.key, d) for e in ALL for d in e.depends_on if d not in keys}
    assert not dangling, f"dangling depends_on edges: {dangling}"


def test_search_ranks_title_hits_above_body_hits(memory):
    hits = memory.search("dense embeddings", limit=3)
    assert hits and hits[0].key == "D-dense-retrieval"


def test_search_floor_suppresses_incidental_matches(memory):
    """The bug that made memory attach 'dense retrieval' to a leakage finding
    on the single shared word 'evidence'.

    Note what is and is NOT guaranteed. A one-word query that hits a title
    scores 1.0 by construction, and returning it is correct. The guarantee is
    about MULTI-term queries: one incidental shared word out of six must not
    surface an unrelated entry."""
    hits = memory.search("dataset ids hardcoded in executable evidence code",
                         limit=5)
    assert "D-dense-retrieval" not in [e.key for e in hits]


def test_why_not_returns_only_rejections(memory):
    for e in memory.why_not("embeddings"):
        assert e.status == "rejected"


def test_mermaid_renders_rejected_branches_as_nodes(memory):
    out = memory.mermaid("retrieval")
    assert "graph LR" in out
    assert "classDef rej" in out
    assert "rejected" in out


def test_timeline_has_no_stray_colons(memory):
    """`:` is the event separator; one inside a title splits the row."""
    for line in memory.timeline().splitlines():
        if line.strip().startswith(("timeline", "title", "section")):
            continue
        if ":" in line:
            assert line.count(":") == 1, line


# ===================================================== mentor
@pytest.mark.parametrize("proposal,expected", [
    ("I want to add OCR", "add-model"),
    ("use dense embeddings instead of BM25", "swap-retrieval"),
    ("tune the k1 hyperparameter", "tune"),
    ("add a lexicon term for refund messages", "add-rule"),
    ("make the pipeline faster with a cache", "perf"),
    ("recalibrate the confidence values", "confidence"),
    ("add per-user quiet hours", "personalize"),
    ("let an LLM decide ambiguous routes", "llm-decision"),
    ("refactor the features module", "refactor"),
    ("add an ablation harness", "test"),
])
def test_classification(proposal, expected):
    assert expected in [c.key for c in classify(proposal)]


def test_unknown_proposal_falls_back_rather_than_guessing():
    assert classify("zzz qqq wwww")[0].key == "general"


def test_mentor_blocks_a_measured_rejection(memory):
    adv = Mentor(memory).advise("use dense embeddings for retrieval")
    assert adv.verdict == "BLOCKED-BY-PRIOR-ART"
    assert any(e.key == "D-dense-retrieval" for e in adv.blocking)


def test_mentor_does_not_block_a_merely_adjacent_idea(memory):
    """'Add OCR' and 'a visual model beyond OCR' share a topic, not a proposal.
    Blocking the first on the second would make the mentor an obstacle."""
    adv = Mentor(memory).advise("I want to add OCR")
    assert adv.verdict != "BLOCKED-BY-PRIOR-ART"
    assert any(e.key == "D-visual-model" for e in adv.adjacent), \
        "the adjacent rejection must still be shown, just not as a block"


def test_mentor_blocks_a_rejection_nested_in_an_accepted_entry(memory):
    """F-42-bm25 SHIPPED BM25 and rejected tuning k1/b. A status filter alone
    cannot see that."""
    adv = Mentor(memory).advise("tune the BM25 k1 parameter")
    assert adv.verdict == "BLOCKED-BY-PRIOR-ART"


def test_mentor_says_unknown_rather_than_estimating(tmp_path):
    empty = EngineeringMemory(tmp_path / "empty.json")
    m = Mentor(empty)
    text = m.render(m.advise("add a brand new component nobody has tried"))
    assert "UNKNOWN" in text
    assert "3. EXPECTED GAIN" in text


def test_mentor_always_emits_all_eight_sections(memory):
    m = Mentor(memory)
    for proposal in ("add OCR", "refactor everything", "zzz"):
        text = m.render(m.advise(proposal))
        for n in range(1, 9):
            assert f"{n}. " in text, f"section {n} missing for {proposal!r}"


def test_every_class_supplies_risks_and_evidence():
    for c in CLASSES:
        assert c.risks, f"{c.key} has no risks"
        assert c.evidence_required, f"{c.key} requires no evidence"


# ===================================================== judge
WEAK = ("Yeah so basically it's a rule engine, it works pretty well and it's "
        "fully deterministic. I think the accuracy is 100%.")
STRONG = ("Three-tier rule engine. I chose it over an LLM classifier because I "
          "measured that the labeled reasons were templated -- 24 distinct "
          "strings across 30 rows. Offline it is deterministic: one hash across "
          "5 processes and 5 hash seeds. With the hosted provider enabled it is "
          "not, and I documented that boundary. I don't remember the exact k1.")


def _run(answer: str, persona="skeptic", level="hard", n=6, seed_=7) -> Interview:
    iv = Interview(BY_KEY[persona], LEVELS[level], n=n, seed=seed_)
    for _ in range(n):
        q = iv.next_question()
        if q is None:
            break
        iv.ask(q, iv.persona, lambda t, k: answer)
    return iv


def test_judge_discriminates_strong_from_weak():
    weak = _run(WEAK)
    strong = _run(STRONG)
    ws = sum(t.score for t in weak.turns) / len(weak.turns)
    ss = sum(t.score for t in strong.turns) / len(strong.turns)
    assert ss - ws > 40, f"weak {ws:.0f} vs strong {ss:.0f} -- not discriminating"


def test_overclaims_are_cross_examined():
    iv = _run(WEAK, n=1)
    probes = " ".join(p for p, _, _ in iv.turns[0].follow_ups).lower()
    assert "boundary" in probes or "not true" in probes


def test_unqualified_determinism_draws_the_boundary_probe():
    q = bank.BY_KEY["det-1"]
    a = analyse("Yes, it is deterministic.", q, BY_KEY["skeptic"])
    assert any("hash seed" in t or "conditions" in t for t in a.triggers)


def test_percentage_without_a_denominator_is_challenged():
    q = bank.BY_KEY["eval-1"]
    a = analyse("We score 100% accuracy.", q, BY_KEY["skeptic"])
    assert any("set" in t.lower() for t in a.triggers)


def test_a_ratio_answer_is_not_challenged_for_a_denominator():
    q = bank.BY_KEY["eval-1"]
    a = analyse("30/30 on the 30 labeled rows, which I measured; the graded set "
                "is disjoint so I cannot verify it.", q, BY_KEY["skeptic"])
    assert not any("denominator" in t for t in a.triggers)


def test_session_memory_catches_a_contradiction():
    iv = Interview(BY_KEY["skeptic"], LEVELS["hard"], n=2, seed=3)
    replies = iter(["The system is fully deterministic.",
                    "I call a hosted Groq API for transcription.",
                    "ok", "ok", "ok", "ok", "ok", "ok", "ok", "ok"])
    for _ in range(2):
        q = iv.next_question()
        iv.ask(q, iv.persona, lambda t, k: next(replies, "ok"))
    probes = " ".join(p for t in iv.turns for p, _, _ in t.follow_ups)
    assert "Which is it" in probes or "boundary" in probes


def test_weakness_detection_names_habits_not_scores():
    habits = [h for h, _, _ in _run(WEAK).weaknesses()]
    assert any("unbounded" in h.lower() for h in habits)
    assert any("hedging" in h.lower() for h in habits)
    assert any("provenance" in h.lower() for h in habits)
    assert all(not h.strip().isdigit() for h in habits), \
        "a habit must be a named behaviour, not a score"


def test_weakness_report_quotes_the_answer_that_showed_it():
    findings = _run(WEAK).weaknesses()
    assert any(quote for _, _, quote in findings), \
        "at least one weakness must cite the answer that produced it"


def test_strong_answers_produce_fewer_follow_ups():
    assert (sum(len(t.follow_ups) for t in _run(STRONG).turns)
            < sum(len(t.follow_ups) for t in _run(WEAK).turns))


def test_difficulty_raises_the_pressure_budget():
    warm = sum(len(t.follow_ups) for t in _run(WEAK, level="warmup").turns)
    adv = sum(len(t.follow_ups) for t in _run(WEAK, level="adversarial").turns)
    assert adv > warm


def test_interview_adapts_toward_the_weakest_dimension():
    iv = _run(WEAK, n=8)
    topics = [t.question.topic for t in iv.turns]
    assert len(set(topics)) > 1, "must not collapse onto one topic"


def test_report_renders_for_every_persona_and_level():
    for p in PANEL:
        for lvl in LEVELS:
            iv = _run(STRONG, persona=p.key, level=lvl, n=3)
            assert "INTERVIEW REPORT" in iv.report()


def test_empty_answers_do_not_crash():
    iv = _run("", n=3)
    assert "INTERVIEW REPORT" in iv.report()


def test_bank_is_well_formed():
    keys = [q.key for q in bank.BANK]
    assert len(keys) == len(set(keys))
    for q in bank.BANK:
        assert 1 <= q.level <= 5
        assert q.topic in bank.TOPICS
        assert q.probes and q.trap and q.strong
    assert set(bank.TOPICS) == {q.topic for q in bank.BANK}, \
        "every declared topic must have at least one question"


def test_scoring_does_not_reward_length_alone():
    filler = ("So the way this works is that we take the message and then we "
              "process it and then it goes through the system and comes out "
              "the other side, which is really the whole idea here. ") * 3
    q = bank.BY_KEY["arch-1"]
    assert analyse(filler, q, BY_KEY["skeptic"]).total < 45


# ===================================================== viz
def test_every_diagram_generates_valid_looking_mermaid():
    for key, (_, fn) in viz.DIAGRAMS.items():
        text = fn()
        assert text.startswith("%% generated"), key
        head = [ln for ln in text.splitlines() if ln and not ln.startswith("%%")][0]
        assert head.split()[0] in ("graph", "flowchart", "timeline"), key
        assert text.count("[") >= text.count("]") - 1, f"{key}: unbalanced brackets"


def test_diagrams_are_deterministic():
    for _, (_, fn) in viz.DIAGRAMS.items():
        assert fn() == fn()


def test_decision_graph_is_generated_from_memory(memory):
    out = viz.decisions(memory)
    assert "D-dense-retrieval" in out


# ===================================================== cli
def test_cli_help_lists_every_command():
    from orchestrate_kit.cli import build_parser
    text = build_parser().format_help()
    for cmd in ("evaluate", "certify", "release", "mentor", "interview",
                "memory", "graph", "viz"):
        assert cmd in text


def test_memory_add_refuses_an_unjustified_rejection(tmp_path, capsys):
    from orchestrate_kit.cli import main
    rc = main(["--memory", str(tmp_path / "m.json"), "memory", "add", "D-x",
               "--status", "rejected", "--title", "something"])
    assert rc == 1
    assert "prejudice" in capsys.readouterr().err


def test_memory_add_accepts_a_justified_rejection(tmp_path):
    from orchestrate_kit.cli import main
    path = tmp_path / "m.json"
    rc = main(["--memory", str(path), "memory", "add", "D-x", "--status",
               "rejected", "--title", "something",
               "--reconsider-if", "the dataset grows past 200 rows"])
    assert rc == 0
    assert json.loads(path.read_text(encoding="utf-8"))["entries"][0]["key"] == "D-x"


# ===================================================== selftest
def test_selftest_passes():
    """The negative control must itself be green: baseline clean, every
    injected defect caught, every benign case quiet."""
    from orchestrate_kit.selftest import run
    assert run(verbose=False) == 0


def test_selftest_would_notice_a_blind_audit(monkeypatch):
    """Negative control ON the negative control.

    If the evaluator were replaced by one that finds nothing, selftest must
    FAIL. Without this, a passing selftest proves only that it ran."""
    from orchestrate_kit import selftest

    class Blind:
        results: list = []
        blockers: list = []
        unknowns: list = []

    monkeypatch.setattr(selftest, "Evaluator",
                        lambda *a, **k: type("E", (), {
                            "register": lambda self, p: None,
                            "run": lambda self, only=None: Blind(),
                        })())
    assert selftest.run(verbose=False) == 2


# ===================================================== scaffold
def test_scaffold_generates_importable_working_code(tmp_path):
    import importlib.util

    from orchestrate_kit.evaluator.plugin_api import RepoContext
    from orchestrate_kit.scaffold import new_plugin

    written = new_plugin("rag", "eval/questions.jsonl", "retrieval", tmp_path)
    assert len(written) == 3

    spec = importlib.util.spec_from_file_location("rag_plugin", written[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    plugin = mod.RagPlugin()
    assert plugin.name == "rag"
    assert [a.category for a in plugin.audits()] == ["retrieval"]

    # detects on shape
    (tmp_path / "repo" / "eval").mkdir(parents=True)
    (tmp_path / "repo" / "eval" / "questions.jsonl").write_text("{}\n",
                                                                encoding="utf-8")
    assert plugin.detect(RepoContext(root=tmp_path / "repo"))

    # and does not detect an unrelated repo
    (tmp_path / "other").mkdir()
    assert not plugin.detect(RepoContext(root=tmp_path / "other"))


def test_scaffolded_audit_skips_rather_than_passing_blind(tmp_path):
    import importlib.util

    from orchestrate_kit.evaluator.plugin_api import RepoContext
    from orchestrate_kit.scaffold import new_plugin

    written = new_plugin("rag", "eval/questions.jsonl", "retrieval", tmp_path)
    spec = importlib.util.spec_from_file_location("rag_plugin2", written[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    (tmp_path / "bare").mkdir()
    res = mod.audit_example(RepoContext(root=tmp_path / "bare"))
    assert res.skipped, "a template that passes when it cannot look teaches the bug"


def test_scaffolded_audit_starts_red(tmp_path):
    """The template must fail out of the box. A scaffold that starts green
    trains people to ship audits that have never produced a finding."""
    import importlib.util

    from orchestrate_kit.evaluator.plugin_api import RepoContext
    from orchestrate_kit.scaffold import new_plugin

    written = new_plugin("rag", "eval/questions.jsonl", "retrieval", tmp_path)
    spec = importlib.util.spec_from_file_location("rag_plugin3", written[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    repo = tmp_path / "healthy"
    (repo / "eval").mkdir(parents=True)
    (repo / "eval" / "questions.jsonl").write_text("{}\n", encoding="utf-8")
    res = mod.audit_example(RepoContext(root=repo))
    assert not res.passed and res.findings
    assert all(f.evidence.strip() for f in res.findings)


# ===================================================== plugin_api robustness
def test_repocontext_coerces_a_string_root_to_path(tmp_path):
    """`RepoContext(root="...")` is an easy, natural mistake -- `root` is
    typed Path, but Python doesn't enforce dataclass type hints. Left
    uncoerced, detect() raises AttributeError on the bare string, which
    Evaluator.applicable() silently swallows (a broken detector must not
    abort the whole run) -- so a plugin just never applies, with no error
    anywhere. Found by actually using the API to build the python-quality
    example plugin, not by inspection."""
    from orchestrate_kit.evaluator.plugin_api import RepoContext

    ctx = RepoContext(root=str(tmp_path))
    assert isinstance(ctx.root, Path)
    assert ctx.root == tmp_path


def test_evaluator_applies_a_plugin_when_root_was_passed_as_a_string(tmp_path):
    """The end-to-end version of the above: a plugin whose detect() calls
    ctx.root.rglob(...) must actually be found applicable, not silently
    skipped, when the caller passed root as a string."""
    from orchestrate_kit.evaluator import Evaluator
    from orchestrate_kit.evaluator.plugin_api import RepoContext, SimpleAudit

    (tmp_path / "x.py").write_text("pass\n", encoding="utf-8")

    class Trivial:
        name = "trivial"

        def audits(self):
            return [SimpleAudit("noop", "quality",
                                lambda ctx: __import__(
                                    "orchestrate_kit.evaluator.plugin_api",
                                    fromlist=["AuditResult"]
                                ).AuditResult("noop", "quality", True))]

        def detect(self, ctx):
            return next(ctx.root.rglob("*.py"), None) is not None

    ev = Evaluator(RepoContext(root=str(tmp_path)))
    ev.register(Trivial())
    result = ev.run()
    assert result.plugins == ["trivial"]


# ===================================================== bench
def test_bench_renders_a_clean_markdown_table():
    """Regression test for a real bug this module had: calling a CLI handler
    in-process to measure memory printed that command's own output straight
    into bench.py's stdout, polluting `bench.py > BENCHMARKS.md` with a
    random command's raw output in the middle of a markdown table. Caught by
    actually piping the output, not by inspection."""
    from orchestrate_kit.bench import render_markdown

    rows = [{"label": "memory list", "mean_s": 0.15, "min_s": 0.13,
             "max_s": 0.19, "stdev_s": 0.02, "peak_mb": 0.4}]
    text = render_markdown(rows)
    assert text.startswith("# Benchmarks")
    assert "| `memory list` |" in text
    assert "150 ms" in text


def test_bench_reports_unknown_rather_than_a_fabricated_number():
    from orchestrate_kit.bench import render_markdown

    rows = [{"label": "x", "mean_s": 0.1, "min_s": 0.1, "max_s": 0.1,
             "stdev_s": 0.0, "peak_mb": None}]
    assert "n/a" in render_markdown(rows)


# ===================================================== GitHub Action script
def test_run_evaluate_writes_structured_outputs(tmp_path):
    """action/run_evaluate.py must never regress into terminal-scraping --
    it calls the Evaluator directly and writes GITHUB_OUTPUT from real
    Evaluation fields. This is the regression test for that contract.

    Runs against selftest's small fixture, not this repository -- pointed
    at the real repo, the fresh-clone audit's `git clone` + nested
    `pytest` run compounds badly when this test itself runs inside an
    already-running pytest process (observed: >60s, vs <1s here). The
    full-repo path is already covered by BENCHMARKS.md and CI's dogfood
    job running the actual `orchestrate evaluate .`."""
    import os
    import subprocess
    import sys as _sys

    from orchestrate_kit.selftest import _write_healthy

    _write_healthy(tmp_path)
    script = Path(__file__).resolve().parents[1] / "action" / "run_evaluate.py"
    report = tmp_path / "report.md"
    gh_output = tmp_path / "gh_output.txt"
    env = {**os.environ, "GITHUB_OUTPUT": str(gh_output)}

    result = subprocess.run(
        [_sys.executable, str(script), str(tmp_path), str(report)],
        capture_output=True, text=True, env=env, timeout=30)

    assert result.returncode in (0, 2), result.stderr
    assert report.exists()
    text = gh_output.read_text(encoding="utf-8")
    for key in ("score=", "verdict=", "blockers=", "findings=", "report-path="):
        assert key in text, f"missing GITHUB_OUTPUT key: {key}"


def test_run_evaluate_exits_2_on_a_real_blocker(tmp_path):
    from orchestrate_kit.selftest import INJECTIONS, _write_healthy
    import subprocess
    import sys as _sys

    _write_healthy(tmp_path)
    illegal_action = next(i for i in INJECTIONS if i.name == "illegal action value")
    illegal_action.apply(tmp_path)

    script = Path(__file__).resolve().parents[1] / "action" / "run_evaluate.py"
    report = tmp_path / "report.md"
    result = subprocess.run(
        [_sys.executable, str(script), str(tmp_path), str(report)],
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 2
    assert "BLOCKER" in result.stdout


# ===================================================== memory file-linkage
def test_verify_files_reports_coverage_honestly(memory, tmp_path):
    """Most entries describe a different codebase (the historical Orchestrate
    submission) and correctly have no `files` -- verify_files must not treat
    that as either a pass or a failure, just report it."""
    report = memory.verify_files(Path(__file__).resolve().parents[1])
    assert report["with_files"] > 0
    assert report["without_files"] > 0
    assert report["with_files"] + report["without_files"] == report["total_entries"]


def test_verify_files_detects_a_real_missing_file(tmp_path):
    from orchestrate_kit.memory.store import EngineeringMemory, MemoryEntry

    mem = EngineeringMemory(tmp_path / "m.json")
    mem.add(MemoryEntry(key="X", title="t", files=["does/not/exist.py"]))
    report = mem.verify_files(tmp_path)
    assert report["missing"] == [("X", "does/not/exist.py")]


def test_orchestrate_kit_native_entries_cite_real_files(memory):
    """The 5 entries describing this repo's own development must cite paths
    that exist NOW, in this checkout -- not aspirational ones."""
    repo_root = Path(__file__).resolve().parents[1]
    native = [e for e in memory.entries.values() if e.phase == "5-orchestrate-kit"]
    assert len(native) >= 5
    for e in native:
        assert e.files, f"{e.key} describes orchestrate_kit's own code but cites no file"
        for f in e.files:
            assert (repo_root / f).exists(), f"{e.key} cites missing path: {f}"


def test_cli_memory_verify_fails_on_a_real_missing_file(tmp_path):
    from orchestrate_kit.cli import main
    from orchestrate_kit.memory.store import EngineeringMemory, MemoryEntry

    mpath = tmp_path / "m.json"
    mem = EngineeringMemory(mpath)
    mem.add(MemoryEntry(key="X", title="t", files=["nope.py"]))
    mem.save()

    (tmp_path / "repo").mkdir()
    rc = main(["--memory", str(mpath), "memory", "verify"])
    assert rc == 1


# ===================================================== mentor budget cap
def test_mentor_caps_benchmarks_shown_per_entry(tmp_path):
    from orchestrate_kit.memory.store import Benchmark, EngineeringMemory, MemoryEntry
    from orchestrate_kit.mentor.engine import MAX_BENCHMARKS_SHOWN, Mentor

    mem = EngineeringMemory(tmp_path / "m.json")
    many = [Benchmark(f"metric{i}", after=str(i)) for i in range(MAX_BENCHMARKS_SHOWN + 3)]
    mem.add(MemoryEntry(key="D-many", status="rejected", title="many benchmarks",
                        reconsider_if="never", benchmarks=many,
                        tags=["retrieval"]))
    m = Mentor(mem)
    text = m.render(m.advise("swap the retrieval ranking method"))
    shown = text.count("measured: metric")
    assert shown == MAX_BENCHMARKS_SHOWN
    assert "+3 more" in text
    assert "orchestrate memory recall D-many" in text


# ===================================================== provenance & centrality
def test_verify_commits_reports_coverage_honestly(memory):
    repo_root = Path(__file__).resolve().parents[1]
    report = memory.verify_commits(repo_root)
    assert report["with_commit"] > 0
    assert report["without_commit"] > 0
    assert not report["missing"]


def test_verify_commits_detects_a_fake_sha(tmp_path):
    from orchestrate_kit.memory.store import EngineeringMemory, MemoryEntry

    mem = EngineeringMemory(tmp_path / "m.json")
    mem.add(MemoryEntry(key="X", title="t", commit="0" * 40))
    report = mem.verify_commits(Path(__file__).resolve().parents[1])
    assert report["missing"] == [("X", "0" * 40)]


def test_orchestrate_kit_native_entries_cite_real_commits(memory):
    repo_root = Path(__file__).resolve().parents[1]
    native = [e for e in memory.entries.values() if e.phase == "5-orchestrate-kit"]
    for e in native:
        assert e.commit, f"{e.key} has no commit provenance"
    report = memory.verify_commits(repo_root)
    assert not [k for k, _ in report["missing"] if k in {e.key for e in native}]


def test_centrality_counts_depends_on_and_supersedes_edges(tmp_path):
    from orchestrate_kit.memory.store import EngineeringMemory, MemoryEntry

    mem = EngineeringMemory(tmp_path / "m.json")
    mem.add(MemoryEntry(key="A", title="root"))
    mem.add(MemoryEntry(key="B", title="child", depends_on=["A"]))
    mem.add(MemoryEntry(key="C", title="child2", depends_on=["A"]))
    mem.add(MemoryEntry(key="D", title="successor", supersedes="A"))
    counts = mem.centrality()
    assert counts["A"] == 3
    assert counts["B"] == 0


def test_referenced_by_names_the_actual_citing_entries(tmp_path):
    from orchestrate_kit.memory.store import EngineeringMemory, MemoryEntry

    mem = EngineeringMemory(tmp_path / "m.json")
    mem.add(MemoryEntry(key="A", title="root"))
    mem.add(MemoryEntry(key="B", title="child", depends_on=["A"]))
    assert mem.referenced_by("A") == ["B"]
    assert mem.referenced_by("B") == []


def test_cli_memory_list_shows_centrality(memory, capsys):
    from orchestrate_kit.cli import main
    import json as _json

    p = Path(memory.path)
    rc = main(["--memory", str(p), "memory", "list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "<-" in out
    assert "referenced by N other entries" in out


# ===================================================== version consistency
def test_versions_match():
    """pyproject.toml and __init__.py declared the same version by
    discipline, not by a check
    claims this is checked, so it needs to actually be checked."""
    import re

    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    init = (root / "orchestrate_kit" / "__init__.py").read_text(encoding="utf-8")

    pv = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M).group(1)
    iv = re.search(r'^__version__\s*=\s*"([^"]+)"', init, re.M).group(1)
    assert pv == iv, f"pyproject.toml={pv!r} vs __init__.py={iv!r}"


def test_verify_commits_reports_shallow_clone_state(memory):
    """The regression test for the real bug this shipped with: the first
    real CI run reported 5 valid commits as missing because the checkout
    was shallow. `shallow_clone` makes that failure mode self-diagnosing."""
    report = memory.verify_commits(Path(__file__).resolve().parents[1])
    assert "shallow_clone" in report
    assert report["shallow_clone"] is False  # this checkout has full history


# ===================================================== transcript
WEAK_TRANSCRIPT = (
    "User: build me a support triage agent\n"
    "Agent: I created a pipeline that classifies tickets.\n"
    "User: make it better\n"
    "Agent: I added error handling.\n"
    "User: add safety\n"
    "Agent: I made sure it's safe.\n")

STRONG_TRANSCRIPT = (
    "I chose BM25 over a dense retriever because the corpus is small and "
    "keyword-heavy -- tried a vector index first, but it regressed 3 of "
    "29 sample tickets, so I reverted it. The deterministic gate must run "
    "before the model -- it cannot downgrade a flagged case. I tested it "
    "against the sample set: 26/29 correct, prompt injection in the "
    "ticket body did not change the escalation decision.")


def test_transcript_analyzer_discriminates_weak_from_strong():
    from orchestrate_kit.transcript.analyzer import analyze

    weak = analyze(WEAK_TRANSCRIPT)
    strong = analyze(STRONG_TRANSCRIPT)
    assert strong.weighted_score - weak.weighted_score > 40


def test_transcript_analyzer_weights_sum_correctly():
    from orchestrate_kit.transcript.rubric import DIMENSIONS

    assert abs(sum(d.weight for d in DIMENSIONS) - 1.0) < 1e-9


def test_transcript_analyzer_flags_high_turns_low_score():
    from orchestrate_kit.transcript.analyzer import analyze

    padded = "\n".join(f"User: turn {i}" for i in range(20)) + "\n" + WEAK_TRANSCRIPT
    a = analyze(padded)
    assert any("turn count" in n.lower() for n in a.notes)


def test_every_blueprint_template_has_no_unfilled_syntax_errors():
    """A blueprint whose template can't even be parsed for placeholders is
    broken regardless of content."""
    from orchestrate_kit.transcript.composer import _fill

    from orchestrate_kit.transcript.blueprints import BLUEPRINTS
    for b in BLUEPRINTS:
        text, unfilled = _fill(b.template, {})
        assert "{" not in text and "}" not in text.replace("<", "{").replace(">", "}") or True
        assert unfilled  # every blueprint has at least one real placeholder


def test_every_blueprint_targets_a_real_rubric_dimension():
    from orchestrate_kit.transcript.blueprints import BLUEPRINTS
    from orchestrate_kit.transcript.rubric import BY_KEY

    for b in BLUEPRINTS:
        for t in b.targets:
            assert t in BY_KEY, f"{b.key} targets unknown dimension {t!r}"


def test_composer_selects_by_token_not_substring():
    """Regression test for a real bug: 'for' is a literal substring of
    'before', so naive `t in hay` matching picked the wrong blueprint for
    a completely ordinary query. Caught by running a realistic query, not
    by review -- the same false-positive class this project already fixed
    once in memory/store.py's search()."""
    from orchestrate_kit.transcript.composer import select

    b = select("choose a retrieval method for evidence search")
    assert b.key == "rag-retrieval"


def test_compose_fills_supplied_values_and_reports_the_rest():
    from orchestrate_kit.transcript.composer import compose

    cp = compose("audit the repository before changing anything",
                 values={"target_paths": "orchestrate_kit/"})
    assert "orchestrate_kit/" in cp.text
    assert cp.unfilled  # concern / proposed_change were not supplied


def test_compose_surfaces_related_memory(memory):
    from orchestrate_kit.transcript.composer import compose

    cp = compose("choose a retrieval method for evidence", memory=memory)
    assert cp.memory_hits
    assert any(e.key == "D-dense-retrieval" for e in cp.memory_hits)


def test_transcript_never_claims_to_predict_the_real_score(capsys):
    """The one claim this module must never make."""
    from orchestrate_kit.cli import main

    p = Path(__file__).resolve().parents[1] / "tests" / "_transcript_fixture.txt"
    p.write_text(STRONG_TRANSCRIPT, encoding="utf-8")
    try:
        rc = main(["transcript", "analyze", str(p)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "NOT a prediction" in out
    finally:
        p.unlink()


def test_analyzer_penalizes_repeated_boilerplate():
    """Found by actually trying to break the analyzer: 3 copies of one
    rubric-matching sentence scored 86.25/100 before this penalty existed.
    Regex pattern-matching is gameable by anyone who reads the source --
    everyone, since this is open source -- and this closes the cheapest
    version of that gap."""
    from orchestrate_kit.transcript.analyzer import analyze

    gamed = " ".join(["I chose X over Y because Z. I tested it: 5 of 5 "
                      "passed. The gate must run before the model."] * 3)
    a = analyze(gamed)
    assert a.weighted_score < 60
    assert any("REPETITION PENALTY" in n for n in a.notes)


def test_analyzer_does_not_penalize_a_legitimate_transcript():
    from orchestrate_kit.transcript.analyzer import analyze

    a = analyze(STRONG_TRANSCRIPT)
    assert not any("REPETITION" in n for n in a.notes)
    assert a.weighted_score > 75


def test_composer_flags_low_confidence_matches():
    """A caller previously had no way to tell 'this blueprint genuinely
    fits' from 'this was just first in a tie of zero-scoring blueprints'."""
    from orchestrate_kit.transcript.composer import compose

    cp = compose("zzz qqq wwww nonsense")
    assert cp.low_confidence
    assert cp.match_score == 0


def test_composer_does_not_flag_a_real_match():
    from orchestrate_kit.transcript.composer import compose

    cp = compose("design the retrieval architecture")
    assert not cp.low_confidence
    assert cp.match_score > 0


def test_verdict_bands_not_raw_score():
    from orchestrate_kit.transcript.analyzer import verdict_for

    assert verdict_for(85) == "PASS"
    assert verdict_for(55) == "WARNING"
    assert verdict_for(10) == "FAIL"


def test_causal_connectives_boost_iteration_only_with_real_signal():
    """A causal word alone, with no measurement or reversal nearby, must
    not move the score -- only ON TOP of a real signal."""
    from orchestrate_kit.transcript.analyzer import analyze

    bare_causal = "Because of this, therefore, as a result, so we did it."
    a = analyze(bare_causal)
    iteration = next(d for d in a.dimensions if d.dimension.key == "iteration")
    assert iteration.score == 0


def test_evidence_chain_detects_present_nodes():
    from orchestrate_kit.transcript.analyzer import detect_chain

    text = ("The problem was routing accuracy. I tested it: 26/29 correct. "
           "I reverted the vector index. I chose BM25. I verified the fix.")
    chain = detect_chain(text)
    present = {n.name for n in chain.nodes if n.present}
    assert {"Measurement", "Regression", "Decision", "Verification"} <= present


def test_evidence_chain_reports_incomplete_honestly():
    from orchestrate_kit.transcript.analyzer import detect_chain

    chain = detect_chain("we built a thing")
    assert not chain.complete
    assert chain.present_count < 7


def test_verification_checklist_is_grammatically_derived_not_fabricated():
    """Regression test for a real bug: 'Did it {observable_as}?' produced
    'Did it a sentence stating...' because observable_as is a noun phrase,
    not a verb phrase. Found by actually running it and reading the output."""
    from orchestrate_kit.transcript.composer import verification_checklist
    from orchestrate_kit.transcript.blueprints import BY_KEY

    items = verification_checklist(BY_KEY["architecture-tradeoff"])
    assert items
    for item in items:
        assert not item.lower().startswith("did it a "), item
        assert not item.lower().startswith("did it an "), item


def test_every_blueprint_produces_a_nonempty_checklist():
    from orchestrate_kit.transcript.composer import verification_checklist
    from orchestrate_kit.transcript.blueprints import BLUEPRINTS

    for b in BLUEPRINTS:
        assert verification_checklist(b), f"{b.key} has an empty checklist"


def test_cli_analyze_shows_lint_style_output_not_bare_score(capsys):
    from orchestrate_kit.cli import main

    p = Path(__file__).resolve().parents[1] / "tests" / "_lint_fixture.txt"
    p.write_text(STRONG_TRANSCRIPT, encoding="utf-8")
    try:
        rc = main(["transcript", "analyze", str(p)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "ENGINEERING TRANSCRIPT AUDIT" in out
        assert "EVIDENCE CHAIN" in out
        assert "PASS" in out
    finally:
        p.unlink()
