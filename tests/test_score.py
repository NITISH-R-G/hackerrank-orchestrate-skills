from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrate_kit.score.code_zip import score_code
from orchestrate_kit.score.interview_signal import score_interview
from orchestrate_kit.score.output_csv import score_output
from orchestrate_kit.score.scoreboard import build_scorecard, render_scoreboard
from orchestrate_kit.score.signals import Confidence, ScoreCard, SignalScore
from orchestrate_kit.score.transcript_signal import score_transcript


# --------------------------------------------------------------- signals.py

def test_weighted_estimate_ignores_unknown_signals_rather_than_zeroing():
    known = SignalScore("code", "Code ZIP", 80.0, 0.30, Confidence.HEURISTIC)
    unknown = SignalScore("interview", "AI Judge Interview", None, 0.30,
                          Confidence.UNKNOWN)
    card = ScoreCard(signals=[known, unknown])
    # only the known 30% weight counts -- not 80*0.30 over 100%, and not 0
    # for the missing signal either.
    assert card.weighted_estimate == pytest.approx(24.0)
    assert card.known_weight_fraction == pytest.approx(0.30)


def test_weakest_and_strongest_ignore_unknown_signals():
    a = SignalScore("code", "Code ZIP", 40.0, 0.30, Confidence.HEURISTIC)
    b = SignalScore("output", "Output CSV", 90.0, 0.30, Confidence.MEASURED)
    u = SignalScore("interview", "AI Judge Interview", None, 0.30,
                    Confidence.UNKNOWN)
    card = ScoreCard(signals=[a, b, u])
    assert card.weakest_known_signal.name == "code"
    assert card.strongest_known_signal.name == "output"


def test_all_unknown_signals_yields_no_weighted_estimate():
    u1 = SignalScore("code", "Code ZIP", None, 0.30, Confidence.UNKNOWN)
    u2 = SignalScore("output", "Output CSV", None, 0.30, Confidence.UNKNOWN)
    card = ScoreCard(signals=[u1, u2])
    assert card.weighted_estimate is None
    assert card.weakest_known_signal is None


# --------------------------------------------------------------- code_zip.py

_AGENT_SRC = '''
import json

SYSTEM_PROMPT = "You are a triage agent."

TOOLS = {"lookup": {"type": "object", "properties": {}}}

MAX_ITERATIONS = 5


def classify(ticket: dict) -> dict:
    for step in range(MAX_ITERATIONS):
        response = call_llm(ticket)
        if response.get("done"):
            break
    return validate(response)


def validate(response: dict) -> dict:
    if "status" not in response:
        raise ValueError("missing status")
    return response


def call_llm(ticket):
    try:
        return _do_call(ticket)
    except TimeoutError:
        return _do_call(ticket)  # retry


def _do_call(ticket):
    return {"status": "open", "done": True}
'''

_HARDCODED_SECRET_SRC = '''
API_KEY = "sk-live-abcdefghijklmnopqrstuvwx1234567890"

def call():
    return API_KEY
'''


def test_code_zip_scores_a_recognizable_agent_pattern_reasonably_high(tmp_path):
    (tmp_path / "agent.py").write_text(_AGENT_SRC, encoding="utf-8")
    score = score_code(tmp_path)
    assert score.estimated_score is not None
    assert score.estimated_score > 20


def test_code_zip_negative_control_hardcoded_secret_tanks_rigor(tmp_path):
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "agent.py").write_text(_AGENT_SRC, encoding="utf-8")
    clean_score = score_code(clean)

    dirty = tmp_path / "dirty"
    dirty.mkdir()
    (dirty / "agent.py").write_text(_AGENT_SRC, encoding="utf-8")
    (dirty / "secret.py").write_text(_HARDCODED_SECRET_SRC, encoding="utf-8")
    dirty_score = score_code(dirty)

    assert dirty_score.estimated_score < clean_score.estimated_score


def test_code_zip_empty_repo_does_not_crash(tmp_path):
    score = score_code(tmp_path)
    assert score.name == "code"


# ------------------------------------------------------------- output_csv.py

def _write_clean_submission(root: Path) -> None:
    (root / "dataset").mkdir(parents=True, exist_ok=True)
    (root / "dataset" / "output.csv").write_text(
        "message_id,action,message_type,reason,confidence,evidence_message_ids\n"
        "M1,notify,personal,\"a friend asked a direct question\",0.9,none\n",
        encoding="utf-8")
    (root / "dataset" / "messages.csv").write_text(
        "message_id,message\nM1,hey are you free this weekend?\n",
        encoding="utf-8")
    (root / "problem_statement.md").write_text(
        "# Problem\nClassify messages.\n", encoding="utf-8")


def test_output_csv_unknown_when_no_output_file(tmp_path):
    score = score_output(tmp_path)
    assert score.is_unknown
    assert score.confidence == Confidence.UNKNOWN


def test_output_csv_negative_control_illegal_status_drops_score(tmp_path):
    _write_clean_submission(tmp_path)
    clean = score_output(tmp_path)

    out = tmp_path / "dataset" / "output.csv"
    original = out.read_text(encoding="utf-8")
    out.write_text(original.replace(",notify,", ",ESCALATE,"),
                   encoding="utf-8")
    try:
        broken = score_output(tmp_path)
    finally:
        out.write_text(original, encoding="utf-8")

    assert not clean.is_unknown
    assert broken.estimated_score < clean.estimated_score


# ------------------------------------------------------------ transcript.py

def test_transcript_unknown_when_no_file_given():
    score = score_transcript(None)
    assert score.is_unknown


def test_transcript_negative_control_empty_transcript_scores_low(tmp_path):
    rich = tmp_path / "rich.txt"
    rich.write_text(
        "I chose BM25 over embeddings because embeddings needed a model "
        "download the eval sandbox blocked; I verified this by timing a "
        "cold start that failed after 30s. I measured precision at 92% "
        "against 40 hand-labeled tickets and rejected a pure keyword "
        "approach because it missed paraphrased complaints.",
        encoding="utf-8")
    empty = tmp_path / "empty.txt"
    empty.write_text("ok sounds good", encoding="utf-8")

    rich_score = score_transcript(rich)
    empty_score = score_transcript(empty)
    assert rich_score.estimated_score > empty_score.estimated_score


# ---------------------------------------------------------- interview_signal.py

def test_interview_signal_unknown_without_a_saved_result(tmp_path):
    assert score_interview(None).is_unknown
    assert score_interview(tmp_path / "missing.json").is_unknown


def test_interview_signal_reads_a_saved_result(tmp_path):
    p = tmp_path / "result.json"
    p.write_text(json.dumps({
        "score": 72, "persona": "skeptic", "difficulty": "standard",
        "questions_answered": 5, "questions_requested": 5,
        "saved_at": "2026-08-12T00:00:00+00:00",
    }), encoding="utf-8")
    score = score_interview(p)
    assert score.estimated_score == 72.0
    assert score.confidence == Confidence.HEURISTIC


def test_interview_signal_flags_an_early_ended_session(tmp_path):
    p = tmp_path / "result.json"
    p.write_text(json.dumps({
        "score": 40, "questions_answered": 2, "questions_requested": 8,
    }), encoding="utf-8")
    score = score_interview(p)
    assert any("ended early" in f.label for f in score.findings)


def test_interview_signal_unknown_on_corrupt_json(tmp_path):
    p = tmp_path / "result.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert score_interview(p).is_unknown


# -------------------------------------------------------------- scoreboard.py

def test_scoreboard_combines_all_four_signals(tmp_path):
    _write_clean_submission(tmp_path)
    (tmp_path / "agent.py").write_text(_AGENT_SRC, encoding="utf-8")
    card = build_scorecard(tmp_path)
    assert len(card.signals) == 4
    assert card.weighted_estimate is not None
    text = render_scoreboard(card, tmp_path, save_history=False)
    assert "ESTIMATED ORCHESTRATE SCORE" in text
    assert "not official" in text.lower()


def test_scoreboard_history_records_delta_across_runs(tmp_path):
    _write_clean_submission(tmp_path)
    card1 = build_scorecard(tmp_path)
    render_scoreboard(card1, tmp_path, save_history=True)

    card2 = build_scorecard(tmp_path)
    text2 = render_scoreboard(card2, tmp_path, save_history=True)
    assert "Previous estimate:" in text2
    assert "Delta:" in text2


def test_scoreboard_reports_unknown_overall_when_nothing_is_measurable(tmp_path):
    card = build_scorecard(tmp_path)
    # code_zip always returns a number (even 0-ish) for an empty dir, but
    # output/interview/transcript are all UNKNOWN here -- overall should
    # still degrade gracefully rather than crash.
    text = render_scoreboard(card, tmp_path, save_history=False)
    assert "UNKNOWN" in text
