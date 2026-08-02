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
