"""The seed corpus — a real build's institutional knowledge.

Every entry is transcribed from a measured finding. Nothing here is illustrative.

The field that matters most is `reconsider_if`. A rejection without one is a
prejudice: it tells the next engineer "no" without telling them what would
change the answer. Every rejected entry below states the condition under which
re-opening it is the *correct* engineering call.

    python -m orchestrate_kit memory seed
"""

from __future__ import annotations

from .store import Benchmark as B
from .store import MemoryEntry as M

# =====================================================================
# Phase 1 — Build: correctness and safety
# =====================================================================
BUILD = [
    M(key="D-rule-engine", kind="decision", phase="1-build",
      title="Deterministic rule engine over an LLM classifier",
      problem="A message router has to assign action + type + reason. An LLM "
              "classifier is the obvious default in 2026.",
      root_cause="Three properties of the data made the LLM the worse fit, none "
                 "of them obvious before measuring.",
      chosen="Three-tier deterministic rule engine: SAFETY > RELATIONSHIP/URGENCY "
             "> ENGAGEMENT > DEFAULT",
      rejected=["LLM classifier over raw message text",
                "hybrid LLM-with-rule-fallback"],
      evidence="(1) Labeled reasons were templated: 24 distinct strings across 30 "
               "rows -- ground truth states which RULE fired, not what the text "
               "said. (2) One labeled row was a prompt-injection attack whose "
               "correct label was mute/scam; a rule engine is structurally immune "
               "because message text never enters a decision prompt. (3) Every "
               "safety-critical signal was a structured field, not prose.",
      benchmarks=[B("distinct labeled reason strings", after="24", sample_size="30 rows",
                    note="templated => rule identity is the label")],
      blast_radius="Whole system. Every downstream decision inherits determinism.",
      impact="One output hash across 5 processes x 5 PYTHONHASHSEED values",
      reconsider_if="Reasons in the graded set turn out to be free-form prose "
                    "rather than templates, OR the type taxonomy grows past what "
                    "~40 rules can express without collisions.",
      tags=["architecture", "determinism", "llm", "rules"],
      lesson="Read the LABELS before choosing the model. The label format tells "
             "you what is actually being scored."),

    M(key="F-01-dynamic-confidence", kind="finding", phase="1-build",
      title="Dynamic confidence lost to a constant",
      problem="More matched signals 'should' mean higher confidence.",
      root_cause="Intuition substituted for measurement.",
      chosen="Static per-rule confidence; the dynamic function was DELETED",
      rejected=["signal-density scaling"],
      benchmarks=[B("MAE vs labeled confidence", before="0.0287", after="0.0263",
                    sample_size="30", note="dynamic worse on every action subset")],
      evidence="Also emitted values above the observed label band on 3/30 rows.",
      blast_radius="0 rows changed action or type; confidence column only.",
      reconsider_if="Labeled confidences ever show >0.15 spread WITHIN a single "
                    "rule -- that would mean the label depends on the message, "
                    "not the rule.",
      tags=["confidence", "calibration"], status="accepted",
      lesson="Disabling is not enough. Delete. Disabled code is a future accident."),

    M(key="F-03-handler-depth", kind="finding", phase="1-build",
      title="KeyError ran before the row-level exception handler",
      problem="A single malformed row produced zero output rows.",
      root_cause="The try/except was placed inside the loop body, below the "
                 "dictionary access that raised.",
      chosen="Guarded access above the handler; per-row isolation",
      evidence="Injected one missing column -> 0 rows written, exit 0. Silent.",
      benchmarks=[B("rows written under injected corruption", before="0", after="110")],
      blast_radius="Total. A graded run would have scored zero.",
      tags=["robustness", "error-handling"],
      lesson="Test the failure path by injecting the failure, not by reading the code."),

    M(key="F-04-strict-decoding", kind="finding", phase="1-build",
      title="BOM / invalid UTF-8 aborted the whole load",
      problem="Strict decoding on the input CSV.",
      root_cause="Default encoding assumptions on a file supplied by someone else.",
      chosen="utf-8-sig with errors='replace'",
      benchmarks=[B("rows loaded from BOM-prefixed input", before="0", after="110")],
      evidence="A UTF-8 BOM is what Excel writes by default.",
      blast_radius="Total, conditional on the grader's file encoding.",
      tags=["robustness", "encoding", "coupling"],
      lesson="You do not control the encoding of an input you are handed."),

    M(key="F-07-cwd-paths", kind="finding", phase="1-build",
      title="Media paths resolved from the working directory, not the dataset dir",
      problem="Every media file failed to open, and the failure was swallowed.",
      root_cause="Relative path resolution plus a bare except.",
      chosen="Resolve media relative to the dataset root; log every miss",
      benchmarks=[B("media files opened when run from repo root",
                    before="0%", after="100%", sample_size="33 files")],
      evidence="FileNotFoundError caught and discarded on 100% of media rows.",
      blast_radius="All 33 media rows silently degraded to text-only.",
      tags=["multimodal", "paths", "error-handling"],
      lesson="A swallowed exception turns a total failure into a plausible result."),

    M(key="F-11-vision-truncation", kind="finding", phase="1-build",
      title="Vision output universally truncated mid-word",
      problem="Every caption came back 44-71 characters and cut off.",
      root_cause="Thinking tokens were billed against the same output budget as "
                 "the visible response.",
      chosen="Raise the output budget above the reasoning allocation",
      benchmarks=[B("mean extracted characters", before="58", after="532",
                    sample_size="20 images")],
      blast_radius="All image rows.",
      tags=["multimodal", "vision", "provider"],
      lesson="A uniform output length is a budget symptom, not a content property."),

    M(key="F-16-distress-lexicon", kind="finding", phase="1-build",
      title="SELF-INFLICTED: a distress rule promoted a real-estate robocall",
      problem="A marketing call naming a hospital routed to notify/urgent.",
      root_cause="Location nouns sat in a distress lexicon -- but the REAL root "
                 "cause was methodological: blast radius was measured with "
                 "speech disabled, then shipped with speech enabled.",
      chosen="Remove location nouns; re-measure blast radius in the shipped "
             "configuration",
      benchmarks=[B("rows regressed by the change as shipped", before="0 (measured)",
                    after="1 (actual)", note="the measurement was taken in the "
                                             "wrong configuration")],
      blast_radius="1 graded row -- invisible to the harness that approved it.",
      reconsider_if="Never. The lexicon fix stands; the lesson is about method.",
      tags=["regression", "methodology", "lexicon"],
      depends_on=["D-rule-engine"],
      lesson="Measure in the configuration you SHIP. A blast radius computed with "
             "a component disabled is not a blast radius."),

    M(key="F-17-deobfuscation", kind="finding", phase="1-build",
      title="The fix disabled itself: de-obfuscation destroyed word boundaries",
      problem="Spaced-out evasions like 'Share the O T P now' bypassed detection.",
      root_cause="The de-obfuscator stripped ALL whitespace, collapsing the text "
                 "to 'SharetheOTPnow' -- which no longer matches the "
                 "word-boundary pattern the rule needs.",
      chosen="Collapse only intra-token spacing; preserve word boundaries",
      benchmarks=[B("spaced-credential evasions caught", before="0", after="5",
                    sample_size="5 crafted")],
      blast_radius="0 rows on the sample corpus; 5 on the attack battery.",
      tags=["security", "obfuscation", "regex"],
      lesson="A fix that defeats the mechanism it feeds is worse than no fix -- "
             "it looks like coverage."),

    M(key="F-19-contradictory-rules", kind="finding", phase="1-build",
      title="Two rules encoded opposite policies for the same message",
      problem="'Ma is in ICU, send money to this UPI' routed to notify.",
      root_cause="A distress rule and a payment-scam rule both matched; tier "
                 "order let distress win.",
      chosen="DELETE the distress-escalation rule. Patching its condition would "
             "have made it dead code.",
      rejected=["add an exception clause to the distress rule"],
      evidence="After deletion the row routes mute/scam. No other row changed.",
      blast_radius="1 row changed, 109 identical.",
      tags=["rules", "safety", "shadowing"],
      depends_on=["D-rule-engine"],
      lesson="When a rule needs an exception for the case that matters, the rule "
             "is wrong, not incomplete."),
]

# =====================================================================
# Phase 2 — Multimodal
# =====================================================================
MULTIMODAL = [
    M(key="F-20-ocr-wrong-conclusion", kind="finding", phase="2-multimodal",
      title="'The images carry no signal' was a conclusion about two vendors",
      problem="Hosted vision extracted 0 characters on 15/15 image rows, and that "
              "was recorded as a property of the corpus.",
      root_cause="Confusing the behaviour of a remote service with the content of "
                 "the data.",
      chosen="Local OCR engine (RapidOCR), made the default vision provider",
      rejected=["accepting that the images were blank",
                "a third hosted vendor"],
      benchmarks=[B("characters extracted", before="0", after="10,104",
                    sample_size="20 images", note="19 of 20 non-empty")],
      evidence="7/7 pixel-only scams caught with OCR on; 7/7 escape with it off.",
      blast_radius="0 of 110 output rows changed -- the channel is live and "
                   "redundant on THIS corpus.",
      reconsider_if="A corpus where image text is the sole safety signal on rows "
                    "the rules do not already catch.",
      tags=["multimodal", "ocr", "vision"],
      lesson="When a component returns nothing, prove WHERE the nothing came from."),

    M(key="F-21-image-mime", kind="finding", phase="2-multimodal",
      title="Image MIME type guessed from the filename extension",
      problem="Uploads declared image/jpeg for PNG, WebP and AVIF payloads.",
      root_cause="Extensions in the corpus were deliberately wrong.",
      chosen="Sniff magic bytes; fall back to extension only when bytes are "
             "inconclusive",
      benchmarks=[B("files with a misleading extension", after="19",
                    sample_size="33 media files")],
      blast_radius="19 of 33 media files were being mislabeled on the wire.",
      tags=["multimodal", "coupling", "provider"],
      lesson="A filename is a hint from an untrusted party."),

    M(key="F-28-audio-mime", kind="finding", phase="2-multimodal",
      title="Audio MIME guessed from the filename -- same class, other modality",
      problem="WAV and M4A payloads declared as audio/mpeg.",
      root_cause="The image fix was applied to images only.",
      chosen="Shared byte-sniffing helper across both modalities",
      benchmarks=[B("audio files mislabeled", before="9", after="0", sample_size="13")],
      blast_radius="9 of 13 audio uploads.",
      tags=["multimodal", "coupling", "provider"],
      depends_on=["F-21-image-mime"],
      lesson="When you find a class of bug, grep for the class -- not the instance."),

    M(key="D-media-scoping", kind="decision", phase="2-multimodal",
      title="Image text may escalate safety but must not redefine intent",
      problem="Enabling OCR regressed two rows from urgent to event.",
      root_cause="An unrelated calendar screenshot and a generic brochure tripped "
                 "intent lexicons. A poster is authored by a THIRD PARTY; it "
                 "should not redefine what the sender meant.",
      chosen="Scope image text to the SAFETY tier only. Voice participates fully, "
             "because the transcript IS the message.",
      rejected=["disable vision entirely", "feed OCR into every lexicon"],
      evidence="Spec-grounded asymmetry: message_text is empty on 8/8 voice rows "
               "and non-empty on 15/15 image rows.",
      benchmarks=[B("regressions from enabling OCR", before="2", after="0"),
                  B("pixel-only scams caught", after="7", sample_size="7")],
      blast_radius="Turned enabling OCR into a zero-regression change.",
      reconsider_if="A dataset where images ARE the message -- e.g. rows with "
                    "empty message_text and an image attachment.",
      tags=["multimodal", "ocr", "security", "design"],
      depends_on=["F-20-ocr-wrong-conclusion"],
      lesson="Untrusted content may escalate safety. It must never redefine intent."),
]

# =====================================================================
# Phase 3 — Auditing the audits
# =====================================================================
META = [
    M(key="F-ablation-harness", kind="finding", phase="3-meta-audit",
      title="Ablation harness measured nothing and reported a clean zero",
      problem="Media ablation reported '0 of 110 rows changed'.",
      root_cause="It monkeypatched a module attribute, but the consumer had bound "
                 "that name into its own namespace at import time. BOTH ARMS ran "
                 "the null backend.",
      chosen="Inject through the supported parameter seam",
      rejected=["trusting the clean result"],
      benchmarks=[B("rows changed by disabling media", before="0 (reported)",
                    after="5 (real)", sample_size="110")],
      blast_radius="Would have shipped a false 'media is useless' conclusion into "
                   "the writeup.",
      tags=["audit", "testing", "false-negative"],
      lesson="A clean zero from a broken harness is the most dangerous result in "
             "engineering, because it confirms what you already believed."),

    M(key="F-prober-artifacts", kind="finding", phase="3-meta-audit",
      title="Reachability prober reported 3 dead rules and 7 shadowed -- all false",
      problem="A rule-coverage audit claimed dead code in the safety tier.",
      root_cause="It randomised only fields matching a naming prefix (23 of 37 "
                 "booleans) and returned the FIRST matching condition, so a "
                 "tier-1 rule won nearly every draw.",
      chosen="Search the full feature space; require the rule ITSELF to win",
      benchmarks=[B("unreachable rules", before="3 (reported)", after="1 (real)"),
                  B("shadowed rules", before="7 (reported)", after="0 (real)")],
      blast_radius="Would have deleted reachable safety rules.",
      tags=["audit", "rules", "false-positive"],
      lesson="Distinguish 'unsatisfiable' from 'never won a random draw'."),

    M(key="F-leakage-false-blocker", kind="finding", phase="3-meta-audit",
      title="Label-leakage audit fired a BLOCKER on a healthy repository",
      problem="A confident release blocker on a repo with no leakage.",
      root_cause="Three bugs at once: it scanned root exploratory scripts as "
                 "production, matched synthetic fixture variables as dataset ids, "
                 "and treated docstrings as executable code.",
      chosen="AST docstring stripping, production-glob scoping, assignment "
             "exclusion. Postmortem preserved in the module docstring.",
      evidence="A fourth bug surfaced alongside: Engineering Memory attached "
               "'dense retrieval' as prior art to 'dataset ids in code' on the "
               "single shared word 'evidence'. Fixed with a recall floor.",
      blast_radius="Would have blocked a correct release.",
      tags=["audit", "false-positive", "memory"],
      lesson="Your audit tooling needs a negative control as much as your model does."),

    M(key="F-23-redos", kind="finding", phase="3-meta-audit",
      title="Catastrophic regex backtracking on adversarial input",
      problem="A single 40 KB message took 40.3 seconds to route.",
      root_cause="An unbounded quantifier on a domain-label pattern.",
      chosen="Bound the quantifier to RFC 1035's 63-octet DNS label limit",
      rejected=["a timeout wrapper", "an arbitrary {1,100} bound"],
      benchmarks=[B("worst-case single-row latency", before="40.3s", after="0.29s",
                    note="139x; output hash unchanged")],
      blast_radius="0 rows changed. Denial-of-service path closed.",
      tags=["security", "redos", "performance"],
      lesson="Bound every quantifier with a real-world standard, not a guess -- "
             "then the bound is defensible under questioning."),

    M(key="F-25-silent-arbitration", kind="finding", phase="3-meta-audit",
      title="LLM arbitration was silently ON whenever any key was present",
      problem="A network call and raw message text entered a prompt on 6/110 rows "
              "without any explicit opt-in.",
      root_cause="Feature-gated on credential presence rather than on intent.",
      chosen="Explicit ARBITRATION=on opt-in; default off",
      rejected=["removing arbitration entirely"],
      evidence="On the labeled rows where it could fire, the deterministic verdict "
               "was already correct, and escalation was its only possible action "
               "-- every intervention it could make there was a guaranteed "
               "regression.",
      blast_radius="6 of 110 rows eligible; 0 improved.",
      reconsider_if="A row class appears where the deterministic tiers genuinely "
                    "tie and the tie is resolvable from prose.",
      tags=["llm", "determinism", "security", "arbitration"],
      depends_on=["D-rule-engine"],
      lesson="A capability gated on credential presence is a capability with no "
             "off switch."),

    M(key="F-29-pytest-abort", kind="finding", phase="3-meta-audit",
      title="Bare `pytest` aborted the entire suite",
      problem="63 passing tests displayed as a red, interrupted run.",
      root_cause="A stale exploratory script named test_*.py at the repo root made "
                 "API calls at import time, during collection.",
      chosen="Scope collection with testpaths",
      benchmarks=[B("bare pytest result", before="INTERRUPTED", after="63 passed")],
      blast_radius="The first command a reviewer types.",
      tags=["testing", "release", "developer-experience"],
      lesson="Run the command a REVIEWER runs first, not the one you run."),

    M(key="F-32-import-order", kind="finding", phase="3-meta-audit",
      title="The suite passed only by accident of alphabetical import order",
      problem="One test file, run alone, failed with ModuleNotFoundError.",
      root_cause="An earlier-sorting file performed a sys.path insert at import.",
      chosen="Declare pythonpath in configuration",
      evidence="Every file now passes in isolation.",
      blast_radius="Renaming any test file would have broken every other.",
      tags=["testing", "packaging"],
      lesson="Run each test file alone in CI, not only the suite."),

    M(key="F-33-nondeterministic-test", kind="finding", phase="3-meta-audit",
      title="A determinism test asserted that a hosted service is bit-stable",
      problem="Intermittent failure on one row.",
      root_cause="The test called the pipeline twice with credentials present, "
                 "making two live ASR requests, and asserted equality.",
      chosen="Autouse fixture clearing all credentials -- hermetic by default",
      rejected=["retry the test", "pin the offending row"],
      benchmarks=[B("suite wall time", before="47s", after="4s",
                    note="a dozen hidden live calls stopped")],
      blast_radius="The suite now measures this system, not someone else's uptime.",
      tags=["testing", "determinism", "hermetic"],
      lesson="If a test needs the network, it is testing the network."),

    M(key="F-34-audit-mutates", kind="finding", phase="3-meta-audit",
      title="A performance benchmark overwrote the submission artifact",
      problem="output.csv silently reverted to a degraded configuration.",
      root_cause="The benchmark invoked the CLI without an output flag, three "
                 "times per run, writing to the real artifact path.",
      chosen="Benchmarks write to a temp path; a regression test asserts the "
             "artifact is untouched",
      evidence="A correctly-classified scam reverted to benign between runs.",
      blast_radius="Artifact corruption invisible in any file listing.",
      tags=["audit", "release", "artifact"],
      lesson="An audit must never mutate what it audits."),
]

# =====================================================================
# Phase 4 — Hardening, coupling, generalisation
# =====================================================================
HARDENING = [
    M(key="F-41-unsubscribe", kind="finding", phase="4-hardening",
      title="A marketing unsubscribe footer was not treated as promotional",
      problem="The last remaining labeled miss.",
      root_cause="The promotional lexicon covered offer language but not the "
                 "regulatory footer that legally accompanies bulk marketing.",
      chosen="Add the unsubscribe footer as a promotional signal, explicitly "
             "excluding the near-identical phrase that scams mimic",
      benchmarks=[B("labeled message_type", before="29/30", after="30/30"),
                  B("footer precision on labeled rows", after="3/3")],
      blast_radius="1 graded row -- whose text is byte-identical to a labeled row "
                   "carrying that exact answer.",
      tags=["lexicon", "late-fix"],
      lesson="A good late fix keys on a REGULATORY invariant, not on a phrasing, "
             "and states its blast radius in rows."),

    M(key="F-42-bm25", kind="finding", phase="4-hardening",
      title="Similarity metric structurally preferred short boilerplate",
      problem="Correct evidence ranked 6th of 21 candidates.",
      root_cause="The overlap coefficient divides by min(|a|,|b|), so a short "
                 "document sharing generic terms outranks a longer one sharing "
                 "distinctive terms.",
      chosen="BM25 with canonical k1=1.5, b=0.75 -- deliberately untuned",
      rejected=["tune k1/b", "dense embeddings", "hybrid fusion"],
      benchmarks=[B("evidence any-overlap", before="22/28", after="23/28"),
                  B("truth score vs rival", before="0.389 vs 0.600",
                    note="truth shared 6 distinctive terms over 18 tokens; five "
                         "near-duplicate 10-token messages scored 0.600 each")],
      blast_radius="24 of 110 evidence cells re-ranked; action and type unchanged.",
      reconsider_if="A labeled evidence set large enough (>200 rows) that tuning "
                    "k1/b would not simply overfit.",
      tags=["retrieval", "bm25", "diagnosed"],
      lesson="Aggregate gain is weak evidence. A diagnosed MECHANISM is strong."),

    M(key="F-43-id-shape", kind="finding", phase="4-hardening",
      title="Mention detection assumed the SHAPE of a user id",
      problem="Rules depending on @-mentions were silently dead under renamed ids.",
      root_cause="It harvested tokens matching a regex for the sample's id "
                 "convention, then compared to the real id. The comparison was "
                 "principled; the harvest was not.",
      chosen="Search for '@' followed by the ACTUAL recipient id -- format-agnostic",
      benchmarks=[B("decisions broken by renaming ids", before="4", after="0",
                    sample_size="110")],
      blast_radius="0 rows on this dataset. Removes a hidden-data failure mode.",
      tags=["coupling", "generalization"],
      lesson="Never encode the shape of an identifier someone else generates."),

    M(key="F-44-timestamp-sort", kind="finding", phase="4-hardening",
      title="History ordered by raw string sort of timestamps",
      problem="Chronological only for zero-padded, most-significant-first dates.",
      root_cause="The spec fixes no timestamp format; the sample happened to be ISO.",
      chosen="Format-agnostic sort key, falling back to lexical when ambiguous",
      evidence="Day-first dates produced different output before the fix.",
      blast_radius="0 rows on this dataset.",
      tags=["coupling", "generalization"],
      depends_on=["F-43-id-shape"],
      lesson="'The sample happened to be X' is the definition of coupling."),

    M(key="F-45-copied-wording", kind="finding", phase="4-hardening",
      title="A lexicon term was copied verbatim from one sample sentence",
      problem="The term fired on exactly 1 of 537 corpus texts.",
      root_cause="Transcribed to make one message classify, rather than to express "
                 "the category.",
      chosen="Express the semantic category, guarded by transport context",
      benchmarks=[B("colliding phrasings correctly rejected", before="2/5", after="5/5"),
                  B("target phrasings matched", after="4/4"),
                  B("corpus texts matched by the copied term", after="1",
                    sample_size="537", note="a match count of exactly 1 is the smell")],
      blast_radius="0 rows changed; strictly broader and safer.",
      tags=["coupling", "overfitting", "lexicon"],
      lesson="Count how many rows each lexicon term matches. Exactly one is a smell."),

    M(key="F-48-ocr-cost", kind="finding", phase="4-hardening",
      title="Local OCR cost 0.25s -> 45s and 7 MB -> 500 MB of heap",
      problem="Making OCR the default provider made the run 180x slower.",
      root_cause="A local detection+recognition model loads into the process.",
      chosen="Ship it anyway, and DOCUMENT the trade rather than hiding it",
      rejected=["lazy-load OCR per row", "hosted OCR provider",
                "disable OCR by default"],
      benchmarks=[B("full-corpus wall time", before="0.25s", after="45s",
                    sample_size="110 rows"),
                  B("peak heap", before="7 MB", after="500 MB")],
      blast_radius="0 output rows. Pure cost.",
      reconsider_if="A submission with a wall-clock or memory limit. Then the "
                    "correct move is documented degradation, not silent removal.",
      tags=["performance", "multimodal", "tradeoff"],
      depends_on=["F-20-ocr-wrong-conclusion"],
      lesson="Document the trade you made. A hidden 180x is a defect; a stated "
             "180x is a decision."),
]

# =====================================================================
# The nine measured rejections
# =====================================================================
REJECTIONS = [
    M(key="D-dense-retrieval", kind="decision", status="rejected", phase="4-hardening",
      title="Dense embeddings / RRF / cross-encoder for evidence retrieval",
      problem="Lexical retrieval looks unsophisticated next to embeddings.",
      root_cause="The relation being scored is topical word OVERLAP, not "
                 "paraphrase. Bi-encoders are built for the thing that is not "
                 "being asked.",
      rejected=["dense MiniLM", "reciprocal rank fusion", "cross-encoder rerank", "MMR"],
      chosen="BM25 over a rule-scoped candidate pool",
      benchmarks=[B("evidence F1", after="0.479", baseline="0.512",
                    sample_size="28 labeled", note="153 configurations swept"),
                  B("configs dominating the shipped one on all 6 metrics", after="0",
                    sample_size="153")],
      blast_radius="None shipped.",
      reconsider_if="The evidence relation becomes paraphrase-based -- e.g. graded "
                    "evidence that shares NO tokens with the query. Test for this "
                    "by measuring token overlap between query and gold evidence; "
                    "if median overlap drops below 2 terms, re-open.",
      tags=["retrieval", "embeddings", "rejected"],
      depends_on=["F-42-bm25"],
      lesson="Benchmark the fashionable option. Publish the number when it loses."),

    M(key="D-pool-widening", kind="decision", status="rejected", phase="4-hardening",
      title="Widen the evidence candidate pool to all user history",
      problem="Rule-scoped pools cap recall at 83.9%.",
      root_cause="Extra candidates cost more precision than the recovered recall "
                 "is worth.",
      rejected=["all-user pool", "related-history pool"],
      chosen="Keep rule-scoped pools",
      benchmarks=[B("retrieval ceiling", before="83.9%", after="100%"),
                  B("evidence F1", before="0.512", after="0.483"),
                  B("Jaccard", before="0.408", after="0.342"),
                  B("exact match", before="0.167", after="0.033")],
      blast_radius="None shipped.",
      reconsider_if="Scoring changes from set-F1 to recall-at-k, where a higher "
                    "ceiling would actually pay.",
      tags=["retrieval", "recall", "rejected"],
      lesson="A higher CEILING is not a higher score. Measure the metric you are "
             "graded on."),

    M(key="D-rerank-signals", kind="decision", status="rejected", phase="4-hardening",
      title="Temporal / metadata / behaviour re-ranking of evidence",
      problem="Recency and sender-relationship 'obviously' matter for relevance.",
      root_cause="The signals are constant or near-constant within a candidate "
                 "pool, so they reorder nothing.",
      rejected=["recency decay weighting", "sender-metadata boost",
                "read-behaviour boost"],
      chosen="Pure BM25",
      benchmarks=[B("all six evidence metrics", before="unchanged", after="unchanged",
                    note="byte-identical output across every weighting tried")],
      blast_radius="None shipped. Literally zero bytes changed.",
      reconsider_if="Candidate pools become heterogeneous in time -- e.g. pools "
                    "spanning months rather than one conversation.",
      tags=["retrieval", "ranking", "rejected"],
      lesson="A signal that is constant within the comparison set carries no "
             "information, however predictive it is globally."),

    M(key="D-quiet-hours", kind="decision", status="rejected", phase="4-hardening",
      title="Per-user quiet-hours personalisation",
      problem="Routing 'should' respect when a user actually reads messages.",
      root_cause="No association exists in the data between hour-of-day and the "
                 "labeled action.",
      rejected=["per-user active-hour model", "global quiet-hours window"],
      chosen="No temporal personalisation",
      benchmarks=[B("Cramer's V (hour bucket vs action)", after="0.000",
                    sample_size="110 rows",
                    note="not weak -- zero to three decimals")],
      blast_radius="None shipped.",
      reconsider_if="A dataset that includes per-user read receipts or "
                    "notification-dismissal events. The signal is absent here, "
                    "not merely weak.",
      tags=["personalization", "temporal", "rejected"],
      lesson="Measure the association before building the feature. Cramer's V "
             "costs ten lines."),

    M(key="D-ece-recalibration", kind="decision", status="rejected", phase="4-hardening",
      title="Recalibrate confidence to reduce Expected Calibration Error",
      problem="ECE measured 0.138 -- systematically under-confident.",
      root_cause="ECE was the wrong objective. The LABELS are deliberately "
                 "under-confident, so calibrating to correctness moves away from "
                 "the thing being scored.",
      rejected=["shift +0.05", "shift +0.10", "shift +0.117", "shift +0.15"],
      chosen="Match the labeling policy, not textbook calibration",
      benchmarks=[B("our ECE", after="0.1380"),
                  B("ground truth's OWN ECE", after="0.1597",
                    note="the labels are worse-calibrated than we are"),
                  B("MAE under the best ECE-improving shift", before="0.0263",
                    after="0.1467")],
      blast_radius="None shipped.",
      reconsider_if="A rubric that scores calibration directly rather than "
                    "scoring distance to a labeled confidence value.",
      tags=["confidence", "calibration", "rejected"],
      lesson="Calibrate to the TARGET, not to an ideal. Measure the ground "
             "truth's own calibration first."),

    M(key="D-visual-model", kind="decision", status="rejected", phase="4-hardening",
      title="A visual model beyond OCR",
      problem="Judges may reject submissions that only run OCR.",
      root_cause="No headroom. The rows a visual signal could reach are already "
                 "correct, or unreachable by any pixel.",
      rejected=["pixel photo/graphic classifier", "hosted vision captioning",
                "CLIP-style scene tagging"],
      chosen="OCR only, scoped to the safety tier",
      benchmarks=[B("labeled image rows already correct", after="5/5",
                    note="headroom = 0"),
                  B("graded image rows decided without reading media", after="13/15"),
                  B("best exhaustively-tuned pixel classifier", after="19/20",
                    note="and it FAILS on the single image it would exist for")],
      blast_radius="None shipped.",
      reconsider_if="Rows appear where message_text is empty AND the image is not "
                    "text-bearing -- a photograph carrying the whole meaning.",
      tags=["multimodal", "vision", "ocr", "rejected"],
      depends_on=["D-media-scoping"],
      lesson="Build the STRONGEST version of the idea before rejecting it. "
             "'19/20 and wrong on the one that matters' is a real answer; "
             "'I didn't try' is not."),

    M(key="D-local-asr", kind="decision", status="rejected", phase="4-hardening",
      title="Replace hosted ASR with local Whisper",
      problem="Hosted ASR forfeits determinism and requires a key.",
      root_cause="Local transcription loses the exact entity the safety rules key on.",
      rejected=["faster-whisper small (local)"],
      chosen="Hosted whisper-large-v3, with a documented determinism boundary",
      benchmarks=[B("30-row labeled score", before="30/30", after="30/30",
                    note="a TIE -- the aggregate is blind to this"),
                  B("entity probe", before="'OTP' -> mute/scam",
                    after="'OTT' -> digest/personal",
                    note="one substituted consonant flips a graded row")],
      blast_radius="None shipped.",
      reconsider_if="A local model whose entity-level accuracy on credential terms "
                    "is verified, OR a submission that forbids network calls -- in "
                    "which case ship local AND state the degradation.",
      tags=["asr", "multimodal", "determinism", "rejected"],
      lesson="An aggregate score can be completely blind to the failure that "
             "matters. Probe entities, not averages."),

    M(key="D-evidence-cap", kind="decision", status="rejected", phase="4-hardening",
      title="Cap evidence at k=1 or k=2 instead of the shipped policy",
      problem="Fewer citations might raise precision.",
      root_cause="The metrics disagree with each other and the confidence "
                 "intervals overlap -- there is no measurement that decides it.",
      rejected=["k=1", "k=2"],
      chosen="Keep the shipped cap",
      benchmarks=[B("winner by metric", after="metric-dependent coin flip",
                    sample_size="28", note="Wilson CIs overlap for every pair")],
      blast_radius="None shipped.",
      reconsider_if="A labeled evidence set large enough for the intervals to "
                    "separate. At n=28 no cap is distinguishable.",
      tags=["retrieval", "evidence", "rejected"],
      lesson="'The measurement does not decide it' is a legitimate result. Do not "
             "manufacture a winner from noise."),

    M(key="D-dynamic-confidence-rejected", kind="decision", status="rejected",
      phase="1-build",
      title="Dynamic per-message confidence scaling",
      problem="More matched signals 'should' mean higher confidence.",
      root_cause="Intuition, not measurement.",
      rejected=["signal-density scaling"],
      chosen="Static per-rule confidence",
      benchmarks=[B("MAE", after="0.0287", baseline="0.0263", sample_size="30")],
      blast_radius="None shipped.",
      reconsider_if="Labeled confidence varies by more than 0.15 within a single "
                    "rule's rows.",
      tags=["confidence", "calibration", "rejected"],
      supersedes="", depends_on=["F-01-dynamic-confidence"],
      lesson="The decision record and the finding are separate artifacts: one "
             "says what happened, the other says what not to re-propose."),
]

# =====================================================================
# Process decisions — the ones that are hardest to reconstruct later
# =====================================================================
PROCESS = [
    M(key="D-golden-hash", kind="decision", phase="3-meta-audit",
      title="Pin the output hash, and keep a RE-PIN LOG",
      problem="Any change can silently alter 110 rows.",
      root_cause="Without a pin, a regression is invisible until scoring.",
      chosen="A test asserting one sha256 over the full output, plus a log "
             "recording every re-pin with its cause, effect and score delta",
      rejected=["row-count assertions", "spot-checking a few rows"],
      evidence="The re-pin log is the artifact: it turns 'the hash changed' into "
               "'the hash changed because F-41 fixed the last labeled miss, "
               "29/30 -> 30/30'.",
      blast_radius="Every subsequent change.",
      tags=["release", "testing", "process"],
      lesson="A pinned hash without a re-pin log trains you to update the pin "
             "reflexively. The log is what makes the pin mean something."),

    M(key="D-constants-provenance", kind="decision", phase="4-hardening",
      title="Every constant carries a provenance tag",
      problem="An interviewer asked for a retrieval hyperparameter and it could "
              "not be recalled.",
      root_cause="Constants had values but no recorded justification.",
      chosen="CONSTANTS.md with a provenance column: MEASURED / SPEC / STANDARD / "
             "BOUND / JUDGEMENT",
      rejected=["claiming every constant was tuned"],
      evidence="STANDARD is the load-bearing tag: 'k1=1.5, b=0.75 are the "
               "canonical Robertson/Sparck Jones defaults and I deliberately did "
               "NOT tune them' is stronger than a fabricated sweep, and survives "
               "the follow-up 'show me the sweep'.",
      blast_radius="Documentation only. Zero code change.",
      tags=["process", "interview", "documentation"],
      lesson="Owning a number means knowing where it came from -- including "
             "'I took the standard value on purpose'."),

    M(key="D-hermetic-default", kind="decision", phase="3-meta-audit",
      title="Tests clear credentials by default",
      problem="Tests behaved differently depending on the operator's environment.",
      root_cause="Any test that can reach the network eventually does.",
      chosen="An autouse fixture that pops every known API key variable",
      rejected=["documenting 'unset your keys before testing'"],
      benchmarks=[B("suite wall time", before="47s", after="4s")],
      blast_radius="Whole suite. Network-dependent tests must now opt in explicitly.",
      tags=["testing", "hermetic", "process"],
      depends_on=["F-33-nondeterministic-test"],
      lesson="Make the safe configuration the default, not the documented one."),
]

# =====================================================================
# Phase 5 -- orchestrate_kit's OWN development, not the submission story
# =====================================================================
# Everything above documents a DIFFERENT, historical codebase (the original
# Orchestrate submission's message router, code/router/*.py -- not present
# in this repository). These entries are the first to describe
# orchestrate_kit's own source, and are the only ones where `files` is
# honest to populate: the paths below are real and were verified to exist
# at the time each entry was written. `orchestrate memory verify` checks
# that they still do.
ORCHESTRATE_KIT_ITSELF = [
    M(key="F-package-data-outside-package", kind="finding", phase="5-orchestrate-kit",
      title="package-data pointed outside the package, dropped from a real wheel",
      problem="pyproject.toml declared package-data as '../data/memory.json' "
              "-- a path reaching outside orchestrate_kit/, unsupported by "
              "setuptools.",
      root_cause="It worked locally only by two compounding accidents: an "
                 "editable install's directory layout happened to coincide "
                 "with where the resulting wheel placed the file, AND "
                 "default_path()'s parents[2] calculation coincidentally "
                 "landed on the same spot.",
      chosen="Move the seed corpus to orchestrate_kit/data/memory.json -- "
             "inside the package -- and resolve it with parents[1]",
      rejected=["leaving the accidental layout as-is since it 'worked'"],
      evidence="Built a real wheel, installed it into a clean venv with no "
               "local checkout present: the bundled memory seed corpus was "
               "silently missing.",
      blast_radius="Would have broken the first real PyPI install -- "
                   "invisible in every local test run before that.",
      files=["orchestrate_kit/memory/store.py", "pyproject.toml"],
      tags=["packaging", "pypi", "orchestrate-kit"],
      lesson="Measure in the configuration you SHIP -- an editable install "
             "is not the configuration a real user runs."),

    M(key="F-repocontext-string-root", kind="finding", phase="5-orchestrate-kit",
      title="RepoContext(root=<str>) silently broke plugin detection",
      problem="root is typed Path, but Python doesn't enforce dataclass type "
              "hints -- a plain string is an easy, natural mistake.",
      root_cause="str has no .rglob(); detect() raised AttributeError, which "
                 "Evaluator.applicable() catches and discards BY DESIGN (a "
                 "broken detector must not abort the whole run) -- so a "
                 "plugin just never applied, with no error anywhere.",
      chosen="__post_init__ coerces root to Path",
      evidence="Found while building examples/python-quality-plugin and "
               "actually using the API, not by reading it.",
      blast_radius="Any plugin author who wrote root=\"...\" instead of "
                   "root=Path(\"...\") -- silently, not loudly.",
      files=["orchestrate_kit/evaluator/plugin_api.py"],
      tags=["robustness", "api-design", "orchestrate-kit"],
      lesson="A type hint is documentation, not enforcement. A catch-all "
             "exception handler on a detector needs a matching test proving "
             "the input it's meant to tolerate doesn't ALSO hide a bug."),

    M(key="F-memory-search-substring-match", kind="finding", phase="5-orchestrate-kit",
      title="Memory search matched substrings, not tokens",
      problem="'dataset ids ... in executable code' matched a retrieval "
              "decision entry on the word 'code' alone.",
      root_cause="'code' in 'cross-encoder' is true -- plain substring "
                 "containment, not token equality.",
      chosen="Tokenize with a 4-suffix stemmer before comparing",
      evidence="Caught by a test asserting a multi-term query does NOT "
               "surface an entry sharing only one incidental word.",
      blast_radius="Every prior-art search in the mentor and the CLI's "
                   "why-not/recall commands.",
      files=["orchestrate_kit/memory/store.py"],
      tags=["search", "false-positive", "orchestrate-kit"],
      depends_on=["F-leakage-false-blocker"],
      lesson="The same false-positive class this project already recorded "
             "once (matching inside the wrong boundary) recurred in a "
             "completely different module. A lesson learned once needs a "
             "test, not just a memory entry, or it recurs."),

    M(key="F-bench-stdout-pollution", kind="finding", phase="5-orchestrate-kit",
      title="bench.py's memory measurement leaked a command's stdout into its own report",
      problem="Measuring peak memory by calling a CLI handler in-process let "
              "that handler's print() output land in bench.py's own stdout.",
      root_cause="contextlib.redirect_stdout was missing around the "
                 "in-process call.",
      chosen="Redirect stdout during the in-process measurement",
      evidence="Found by actually piping `bench.py > BENCHMARKS.md` and "
               "reading the file, not by reviewing the code.",
      blast_radius="Every regenerated BENCHMARKS.md until fixed -- a random "
                   "command's raw output in the middle of a markdown table.",
      files=["orchestrate_kit/bench.py"],
      tags=["tooling", "false-positive", "orchestrate-kit"],
      lesson="A tool that reports on other commands needs to be tested by "
             "running it, not by reading it -- the bug was invisible in the "
             "source and obvious in the output."),

    M(key="F-mutable-default-incomplete-detector", kind="finding", phase="5-orchestrate-kit",
      title="A new static-analysis audit's own docstring claimed a false scope boundary",
      problem="The mutable-default-argument audit's first draft claimed "
              "`list()`/`set()`/`dict()` calls were 'deliberately not "
              "flagged' -- stated as a scope decision.",
      root_cause="That claim was simply wrong: a no-arg constructor call "
                 "shares the exact same evaluate-once-at-def-time bug as a "
                 "literal [] or {}. It was an oversight, not a defensible "
                 "boundary.",
      chosen="Detect literals AND no-arg list()/dict()/set() calls; keep "
             "calls-WITH-arguments out of scope on a stated, honest "
             "precision tradeoff instead",
      evidence="A test written to confirm the false-positive guard instead "
               "caught the false-negative before the audit shipped.",
      blast_radius="Would have shipped an audit that missed half of its own "
                   "named bug class.",
      files=["examples/python-quality-plugin/python_quality.py"],
      tags=["audit-quality", "orchestrate-kit"],
      lesson="Write the test for the boundary you claim BEFORE trusting the "
             "docstring that states it."),
]

ALL = (BUILD + MULTIMODAL + META + HARDENING + REJECTIONS + PROCESS
       + ORCHESTRATE_KIT_ITSELF)


def seed(memory) -> int:
    for entry in ALL:
        memory.add(entry)
    memory.save()
    return len(ALL)
