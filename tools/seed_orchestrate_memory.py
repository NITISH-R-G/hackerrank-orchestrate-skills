"""Seed Engineering Memory from the Orchestrate build.

Every entry is transcribed from a real finding with its real measurement. This
is what makes `aiev why-not` and `aiev recall` answer with evidence rather than
opinion -- and it is the artifact most repositories throw away.

    python seed_orchestrate_memory.py <repo>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aiev.core.memory import EngineeringMemory, MemoryEntry  # noqa: E402

E = [
    # ---------------------------------------------------- rejected ideas
    MemoryEntry(
        key="D-dynamic-confidence", kind="decision", status="rejected",
        title="Dynamic per-message confidence",
        problem="Static per-rule confidence felt crude; more matched signals "
                "'should' mean higher confidence.",
        root_cause="Intuition, not measurement.",
        rejected=["signal-density scaling of confidence"],
        chosen="Keep static per-rule confidence; DELETE the dynamic function",
        evidence="MAE 0.0287 dynamic vs 0.0263 static; worse on every action "
                 "subset; emitted values above the observed band on 3/30 rows",
        impact="No output change; removed a latent source of out-of-band values",
        tags=["confidence", "calibration", "rejected"],
        lesson="Disable is not enough -- delete. Disabled code is a future accident.",
    ),
    MemoryEntry(
        key="D-dense-retrieval", kind="decision", status="rejected",
        title="Dense embeddings / RRF / cross-encoder for evidence retrieval",
        problem="Lexical retrieval looks unsophisticated next to embeddings.",
        root_cause="The relation being scored is topical word overlap, not "
                   "paraphrase -- the thing bi-encoders are built for is not "
                   "the thing being asked.",
        rejected=["dense MiniLM", "reciprocal rank fusion", "cross-encoder rerank",
                  "MMR"],
        chosen="BM25 over a rule-scoped candidate pool",
        evidence="153 configurations benchmarked. Dense/RRF/cross-encoder F1 "
                 "0.479 vs 0.512 shipped. Zero configurations dominated the "
                 "shipped one on all six metrics.",
        impact="None shipped", tags=["retrieval", "embeddings", "rejected"],
        lesson="Benchmark the fashionable option; publish the number when it loses.",
    ),
    MemoryEntry(
        key="D-pool-widening", kind="decision", status="rejected",
        title="Widen the evidence candidate pool to all user history",
        problem="Rule-scoped pools cap recall at 83.9%.",
        root_cause="Extra candidates cost more precision than the recovered "
                   "recall is worth.",
        rejected=["all-user pool", "related-history pool"],
        chosen="Keep rule-scoped pools",
        evidence="Ceiling rises 83.9% -> 100%, but F1 0.512 -> 0.483, "
                 "Jaccard 0.408 -> 0.342, exact 0.167 -> 0.033",
        impact="None shipped", tags=["retrieval", "recall", "rejected"],
        lesson="A higher ceiling is not a higher score.",
    ),
    MemoryEntry(
        key="D-ece-recalibration", kind="decision", status="rejected",
        title="Recalibrate confidence to reduce Expected Calibration Error",
        problem="ECE measured 0.138 -- systematically under-confident.",
        root_cause="ECE was the wrong objective: the LABELS are deliberately "
                   "under-confident, so calibrating to correctness moves away "
                   "from the thing being scored.",
        rejected=["shift confidence +0.05 / +0.10 / +0.117 / +0.15"],
        chosen="Match the labeling policy, not textbook calibration",
        evidence="Ground truth's OWN ECE is 0.1597 (worse than ours, 0.1380). "
                 "Every ECE-improving shift made MAE worse: 0.0263 -> 0.1467",
        impact="None shipped", tags=["confidence", "calibration", "rejected"],
        lesson="Calibrate to the target, not to an ideal.",
    ),
    MemoryEntry(
        key="D-visual-model", kind="decision", status="rejected",
        title="A visual model beyond OCR",
        problem="Judges may reject submissions that only run OCR.",
        root_cause="No headroom: the rows a visual signal could reach are "
                   "already correct, or unreachable by any pixel.",
        rejected=["pixel photo/graphic classifier", "hosted vision captioning"],
        chosen="OCR only, scoped to the safety tier",
        evidence="Labeled image rows already 5/5 (headroom 0). 13/15 graded "
                 "image rows decided by rules that never read media. Best "
                 "exhaustively-tuned classifier = 19/20 and FAILS on the one "
                 "image it exists for.",
        impact="None shipped", tags=["multimodal", "vision", "ocr", "rejected"],
        lesson="Build the strongest version of the idea before rejecting it.",
    ),
    MemoryEntry(
        key="D-local-asr", kind="decision", status="rejected",
        title="Replace hosted ASR with local Whisper",
        problem="Hosted ASR forfeits determinism and needs a key.",
        root_cause="Local transcription loses the exact entity the safety rules "
                   "key on.",
        rejected=["faster-whisper small, local"],
        chosen="Hosted whisper-large-v3",
        evidence="Local hears 'Share the OTT'; hosted hears 'OTP'. Probe: OTP -> "
                 "mute/scam, OTT -> digest/personal. Both engines TIE on the "
                 "30-row labeled score -- only the entity probe sees it.",
        impact="None shipped", tags=["asr", "multimodal", "rejected"],
        lesson="An aggregate score can be blind to the failure that matters.",
    ),
    # ---------------------------------------------------- broken audits
    MemoryEntry(
        key="F-ablation-harness", kind="finding", status="accepted",
        title="Ablation harness measured nothing and reported a clean zero",
        problem="Media ablation reported '0 of 110 rows changed'.",
        root_cause="Monkeypatched module attribute, but the consumer had bound "
                   "the name into its own namespace at import time. Both arms "
                   "ran the null backend.",
        chosen="Inject through the supported parameter seam",
        rejected=["trusting the clean result"],
        evidence="Real answer after the fix: 5 rows changed",
        impact="Would have shipped a false 'media is useless' conclusion",
        tags=["audit", "testing", "false-negative"],
        lesson="A clean zero from a broken harness is the most dangerous "
               "result in engineering: it confirms what you expected.",
    ),
    MemoryEntry(
        key="F-prober-artifacts", kind="finding", status="accepted",
        title="Reachability prober reported 3 dead rules and 7 shadowed -- all false",
        problem="Rule-coverage audit claimed dead code.",
        root_cause="Randomised only fields matching a naming prefix (23 of 37 "
                   "booleans) and returned the FIRST condition match, so a "
                   "tier-1 safety rule won nearly every draw.",
        chosen="Search the full feature space; require the rule itself to win",
        evidence="After correction: 1 genuinely unreachable rule, 0 shadowed",
        impact="Would have deleted reachable safety rules",
        tags=["audit", "rules", "false-positive"],
        lesson="Distinguish 'unsatisfiable' from 'never won a random draw'.",
    ),
    MemoryEntry(
        key="F-audit-mutates", kind="finding", status="accepted",
        title="Performance benchmark overwrote the submission artifact",
        problem="output.csv silently reverted to a degraded configuration.",
        root_cause="The benchmark invoked the CLI without an output flag, three "
                   "times per run, writing to the real artifact path.",
        chosen="Benchmark writes to a temp path; regression test asserts the "
               "artifact is untouched",
        evidence="A correctly-classified scam reverted to benign between runs",
        impact="Artifact corruption invisible in any file listing",
        tags=["audit", "release", "artifact"],
        lesson="An audit must never mutate what it audits.",
    ),
    MemoryEntry(
        key="F-nondeterministic-test", kind="finding", status="accepted",
        title="Determinism test asserted a third-party service is bit-stable",
        problem="Test failed intermittently on one row.",
        root_cause="It called the pipeline twice with credentials present, "
                   "making two live ASR requests, and asserted equality.",
        chosen="Autouse fixture clearing all credentials (hermetic)",
        rejected=["retry the test", "pin the row"],
        evidence="Suite time 47s -> 4s once a dozen hidden live calls stopped",
        impact="Test now measures this system, not someone else's uptime",
        tags=["testing", "determinism", "hermetic"],
        lesson="If a test needs the network, it is testing the network.",
    ),
    MemoryEntry(
        key="F-import-order", kind="finding", status="accepted",
        title="Test suite passed only by accident of alphabetical import order",
        problem="A single test file run alone failed with ModuleNotFoundError.",
        root_cause="An earlier file performed a sys.path insert at import time.",
        chosen="Declare pythonpath in config",
        evidence="Every file now passes in isolation",
        impact="Renaming one test file would have broken every other",
        tags=["testing", "packaging"],
        lesson="Run each test file alone in CI, not only the suite.",
    ),
    MemoryEntry(
        key="F-pytest-abort", kind="finding", status="accepted",
        title="Bare `pytest` aborted the entire suite",
        problem="63 passing tests reported as a red, interrupted run.",
        root_cause="A stale exploratory script named test_*.py at the repo root "
                   "executed API calls at import during collection.",
        chosen="Scope collection with testpaths (deleted nothing)",
        evidence="Interrupted -> 63 passed",
        impact="First thing a reviewer types would have shown a broken suite",
        tags=["testing", "release", "developer-experience"],
        lesson="Run the command a reviewer runs first, not the one you run.",
    ),
    # ---------------------------------------------------- coupling
    MemoryEntry(
        key="F-id-shape", kind="finding", status="accepted",
        title="Mention detection assumed the shape of a user id",
        problem="Rules depending on @-mentions were silently dead on renamed ids.",
        root_cause="Harvested tokens matching a regex for the sample's id "
                   "convention, then compared to the real id. The comparison was "
                   "principled; the harvest was not.",
        chosen="Search for '@' + the ACTUAL recipient id, format-agnostic",
        evidence="Renaming ids broke 4 of 110 decisions; 110/110 after the fix",
        impact="No output change on this dataset; removes a hidden-data failure",
        tags=["coupling", "generalization"],
        lesson="Never encode the SHAPE of an identifier you are handed.",
    ),
    MemoryEntry(
        key="F-timestamp-sort", kind="finding", status="accepted",
        title="History ordered by raw string sort of timestamps",
        problem="Chronological only for zero-padded, most-significant-first dates.",
        root_cause="The spec fixes no timestamp format; the sample happened to "
                   "be ISO.",
        chosen="Format-agnostic sort key; falls back to lexical when ambiguous",
        evidence="Day-first dates produced different output before the fix",
        impact="No output change on this dataset",
        tags=["coupling", "generalization"],
    ),
    MemoryEntry(
        key="F-copied-wording", kind="finding", status="accepted",
        title="Lexicon contained a phrase copied from one sample sentence",
        problem="A term fired on exactly 1 of 537 corpus texts.",
        root_cause="Transcribed to make one message classify, rather than "
                   "expressing the category.",
        chosen="Express the semantic category, with a guard for the colliding "
               "domain",
        evidence="5/5 colliding phrasings now rejected (the copied version "
                 "wrongly matched 3 of them); 4/4 target phrasings matched",
        impact="No output change; strictly broader and safer",
        tags=["coupling", "overfitting", "lexicon"],
        lesson="Count how many rows each term matches. Exactly one is a smell.",
    ),
    # ---------------------------------------------------- accepted wins
    MemoryEntry(
        key="F-ocr-wrong-conclusion", kind="finding", status="accepted",
        title="'The images carry no signal' was a conclusion about two vendors",
        problem="Hosted vision extracted 0 characters on 15/15 image rows, and "
                "that was recorded as a property of the corpus.",
        root_cause="Confusing the behaviour of a remote service with the "
                   "content of the data.",
        chosen="Local OCR engine, made the default provider",
        rejected=["accepting that the images were blank"],
        evidence="Local engine extracted 10,104 characters from 19 of 20 images",
        impact="Image reasoning became real: 7/7 pixel-only scams caught, "
               "7/7 escape with OCR disabled",
        tags=["multimodal", "ocr", "vision"],
        lesson="When a component returns nothing, prove WHERE the nothing came from.",
    ),
    MemoryEntry(
        key="F-bm25", kind="finding", status="accepted",
        title="Similarity metric structurally preferred short boilerplate",
        problem="Correct evidence ranked 6th of 21.",
        root_cause="Overlap coefficient divides by min(|a|,|b|), so a short "
                   "document sharing generic terms outranks a longer one "
                   "sharing distinctive terms.",
        chosen="BM25 (IDF + document-length normalisation)",
        rejected=["tuning k1/b", "dense embeddings", "hybrid fusion"],
        evidence="Truth shared 6 distinctive terms over 18 tokens -> 0.389; five "
                 "near-duplicate 10-token messages -> 0.600 each. "
                 "Any-overlap 22/28 -> 23/28",
        impact="24 of 110 evidence cells re-ranked; action/type unchanged",
        tags=["retrieval", "bm25", "diagnosed"],
        lesson="Aggregate gain is weak evidence; a diagnosed mechanism is strong.",
    ),
    MemoryEntry(
        key="F-media-scoping", kind="finding", status="accepted",
        title="Image text was allowed to reclassify sender intent",
        problem="Enabling OCR regressed two rows from urgent to event.",
        root_cause="An unrelated calendar screenshot and a generic brochure "
                   "tripped intent lexicons. A poster is authored by a third "
                   "party and should not redefine what the SENDER meant.",
        chosen="Scope image text to the SAFETY tier only; voice participates "
               "fully because the transcript IS the message",
        rejected=["disable vision entirely", "feed OCR into all lexicons"],
        evidence="Spec: message_text empty on 8/8 voice rows, non-empty on "
                 "15/15 image rows. After scoping: both regressions gone, "
                 "7/7 pixel-only scams still caught",
        impact="Made enabling OCR a zero-regression change",
        tags=["multimodal", "ocr", "security", "design"],
        lesson="Untrusted content may escalate safety; it must not redefine intent.",
    ),
    MemoryEntry(
        key="F-redos", kind="finding", status="accepted",
        title="Catastrophic regex backtracking on adversarial input",
        problem="A single 40 KB message took 40.3 seconds to route.",
        root_cause="Unbounded quantifier on a domain-label pattern.",
        chosen="Bound the quantifier to the RFC 1035 limit of 63 octets",
        evidence="40.3s -> 0.29s (139x); output hash unchanged",
        impact="Denial-of-service path closed", tags=["security", "redos", "performance"],
        lesson="Bound every quantifier with a real-world standard, not a guess.",
    ),
]


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    mem = EngineeringMemory(repo / ".aiev" / "memory.json")
    for e in E:
        mem.add(e)
    mem.save()
    print(f"seeded {len(E)} entries -> {mem.path}")
    print(f"  rejections recorded: {len(mem.rejections())}")
    print(f"  tags: {sorted({t for e in E for t in e.tags})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
