"""What KIND of change is being proposed, and what does that kind cost?

The mentor does not know your codebase. It knows something more durable: that
proposals fall into a small number of classes, and each class has a
characteristic failure mode that engineers rediscover every time.

Nothing here is a number. Numbers come from Engineering Memory (measured) or
from the evaluation plan (to be measured). A class contributes RISKS and
REQUIRED EVIDENCE -- never a predicted gain. A tool that predicts your gain
without running anything is a horoscope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Risk:
    name: str
    why: str
    detect: str          # how to find out whether it applies to YOU
    severity: str = "high"   # blocker | high | medium | low


@dataclass
class ProposalClass:
    key: str
    label: str
    patterns: list[str]
    risks: list[Risk] = field(default_factory=list)
    evidence_required: list[str] = field(default_factory=list)
    ceiling_question: str = ""
    tags: list[str] = field(default_factory=list)

    def matches(self, text: str) -> int:
        return sum(1 for p in self.patterns if re.search(p, text, re.I))


# --------------------------------------------------------------------------
NONDETERMINISM = Risk(
    "non-determinism",
    "A hosted model is not bit-stable. Two runs of the same input can differ, "
    "which breaks golden-hash pinning and makes every later regression test "
    "advisory rather than binding.",
    "Run the pipeline twice with the component enabled and diff the artifacts "
    "byte-for-byte. Then run it 5x with 5 different PYTHONHASHSEED values.",
    "blocker")

INJECTION = Risk(
    "prompt-injection surface",
    "Putting untrusted message text into a prompt that influences a decision "
    "means the message can rewrite the decision. This is not hypothetical for "
    "an adversarial corpus.",
    "Grep for every path where input text reaches a prompt string. Then craft a "
    "row containing an explicit instruction and check the output.",
    "blocker")

NETWORK_IN_TESTS = Risk(
    "network dependency leaks into the test suite",
    "Any test that can reach the network eventually does, and then the suite "
    "measures someone else's uptime.",
    "Run the suite with every credential variable unset. If timing drops "
    "sharply, you had hidden live calls.",
    "high")

BLAST_UNMEASURED = Risk(
    "blast radius measured in the wrong configuration",
    "A change measured with a neighbouring component disabled has no measured "
    "blast radius at all. This is the single most expensive mistake in the "
    "reference build (F-16).",
    "Diff full outputs before/after with EVERY component in its SHIPPED state, "
    "not its convenient one.",
    "blocker")

OVERFIT = Risk(
    "overfitting to the visible sample",
    "A term, threshold or rule tuned until one specific row classifies is "
    "coupling, not coverage.",
    "Count how many rows in the FULL corpus each new term matches. Exactly one "
    "is the smell (F-45).",
    "high")

COUPLING = Risk(
    "coupling to the shape of the sample data",
    "Id format, timestamp format, row order, folder layout and file extensions "
    "are all things the sample happened to have and the graded set may not.",
    "Mutate the input: rename ids, reformat timestamps, shuffle rows, corrupt "
    "extensions. Any output change is coupling.",
    "high")

COST = Risk(
    "unstated runtime or memory cost",
    "A local model can turn a 0.25s run into a 45s run and a 7 MB heap into "
    "500 MB. That is a legitimate trade -- but only if it is stated.",
    "Time the full run and sample peak RSS before and after.",
    "medium")

NO_HEADROOM = Risk(
    "no headroom for the change to act on",
    "If the rows the change could reach are already correct, the best possible "
    "outcome is zero and the realistic outcome is a regression.",
    "Count the rows where the target signal is present AND the current output "
    "is wrong. That number is your ceiling.",
    "high")

DEAD_SIGNAL = Risk(
    "the signal may carry no information",
    "A feature that is constant within the comparison set reorders nothing, "
    "however predictive it seems globally.",
    "Compute association with the label (Cramer's V for categorical, or diff "
    "the outputs with the signal zeroed). 0.000 means stop.",
    "high")

TRUST_BOUNDARY = Risk(
    "third-party content redefining first-party intent",
    "Text inside an image or a forwarded payload was authored by someone other "
    "than the sender. Letting it set intent lets a stranger speak for them.",
    "Enable the channel and diff. Every row that changes CLASS (not just "
    "escalates on safety) is a trust-boundary violation.",
    "high")

METRIC_MISMATCH = Risk(
    "optimising a metric you are not graded on",
    "Improving calibration error, or recall ceiling, or any proxy, can move you "
    "AWAY from the scored quantity.",
    "Write down the exact scored quantity first. Then measure your proxy's "
    "correlation with it on labeled rows.",
    "high")

HARNESS_LIES = Risk(
    "the measurement harness may not be measuring anything",
    "A monkeypatch that the consumer already bound at import means both arms "
    "run the same code and report a clean zero.",
    "Negative control: deliberately break the component and confirm the harness "
    "reports a DIFFERENCE. If a broken component measures clean, the harness is "
    "broken.",
    "blocker")

# --------------------------------------------------------------------------
CLASSES = [
    ProposalClass(
        "add-model", "Add or enable a model-based component",
        [r"\bocr\b", r"\basr\b", r"\bvision\b", r"\bwhisper\b", r"transcri",
         r"\bllm\b", r"\bgpt\b", r"\bcaption", r"speech", r"multimodal",
         r"\bimage\b", r"\baudio\b", r"\bvoice\b"],
        [NONDETERMINISM, NO_HEADROOM, TRUST_BOUNDARY, COST, BLAST_UNMEASURED,
         NETWORK_IN_TESTS],
        ["Row count where the modality is present AND the current output is wrong "
         "(the ceiling).",
         "Counterfactual: disable the component and show which rows STOP being "
         "correct. If none, say so.",
         "Full-output diff with every other component in its shipped state.",
         "Two identical runs, byte-compared."],
        "How many rows can this component possibly fix? Count them before you "
        "build it.",
        ["multimodal", "model", "llm"]),

    ProposalClass(
        "swap-retrieval", "Change the retrieval or ranking method",
        [r"embedding", r"\bbm25\b", r"tf.?idf", r"\brrf\b", r"rerank",
         r"cross.?encoder", r"\bfaiss\b", r"vector", r"semantic search",
         r"retriev", r"similarity", r"\bmmr\b", r"hybrid search"],
        [METRIC_MISMATCH, OVERFIT, NO_HEADROOM],
        ["The scored metric, named exactly, before any code is written.",
         "A ceiling analysis: with a perfect ranker over the current candidate "
         "pool, what score is achievable?",
         "Head-to-head on the SAME pool, reporting every metric -- not the one "
         "that improved.",
         "Confidence intervals. Overlapping CIs on n<50 mean the comparison did "
         "not decide anything."],
        "Is the relation you are scoring lexical overlap or paraphrase? Bi-encoders "
        "answer the second question.",
        ["retrieval", "ranking"]),

    ProposalClass(
        "tune", "Tune a hyperparameter or threshold",
        [r"\btune\b", r"tuning", r"hyper.?param", r"\bsweep\b", r"grid search",
         r"optimi[sz]e the (threshold|constant|parameter)", r"\bk1\b", r"\bb=",
         r"adjust the threshold"],
        [OVERFIT, METRIC_MISMATCH],
        ["Size of the set you are tuning against. Under ~100 labeled rows, "
         "two-parameter tuning is overfitting with extra steps.",
         "A held-out split, or an explicit statement that none exists.",
         "The value you would have used untuned, and its score."],
        "Would you be able to defend this number to someone who asks 'show me the "
        "sweep'? If not, take the standard value ON PURPOSE and say so.",
        ["tuning", "constants"]),

    ProposalClass(
        "add-rule", "Add a rule, lexicon term, or heuristic",
        [r"add a rule", r"new rule", r"lexicon", r"keyword", r"add .*\bterm\b",
         r"\bregex\b", r"pattern for", r"detect .* messages", r"heuristic"],
        [OVERFIT, COUPLING, Risk(
            "rule shadowing",
            "A new rule in an ordered engine can be strictly unreachable, or can "
            "shadow an existing one, without any test failing.",
            "Search the full feature space and require the new rule ITSELF to "
            "win a draw. Prove reachability, do not sample for it.",
            "high")],
        ["Corpus match count for every new term. Report the number.",
         "Which existing rules the new one shadows or is shadowed by.",
         "Full-output diff. Name the rows that changed and why each is correct.",
         "An adversarial phrasing that SHOULD NOT match, and proof it does not."],
        "Does this express a CATEGORY, or does it express one sentence you read?",
        ["rules", "lexicon"]),

    ProposalClass(
        "perf", "Performance or resource optimisation",
        [r"\bfaster\b", r"speed ?up", r"latenc", r"\bcache\b", r"parallel",
         r"memory", r"optimi[sz]e (the )?(run|performance|speed)", r"\bslow\b"],
        [Risk("optimising before measuring",
              "Most perceived hot paths are not hot. Optimisation adds state, and "
              "state adds failure modes.",
              "Profile first. Report the share of total time the target actually "
              "consumes.", "medium"),
         Risk("caching changes determinism",
              "A cache that persists across runs makes run N depend on run N-1.",
              "Delete the cache and re-run. The output must be identical.",
              "high")],
        ["A profile showing the target's share of wall time.",
         "Byte-identical output before and after.",
         "Behaviour on a cold cache."],
        "What fraction of total runtime is this? Below ~20% the best possible "
        "win is not worth a new failure mode.",
        ["performance"]),

    ProposalClass(
        "confidence", "Change confidence values or calibration",
        [r"confidence", r"calibrat", r"\bece\b", r"probabilit", r"uncertainty"],
        [METRIC_MISMATCH,
         Risk("calibrating to an ideal rather than to the target",
              "If the labels are themselves under-confident, every "
              "calibration-improving shift moves you away from the score.",
              "Measure the GROUND TRUTH's own calibration error first. If it is "
              "worse than yours, you are already matching the policy.",
              "high")],
        ["The ground truth's own ECE, computed before you change anything.",
         "MAE against the labeled confidence, before and after.",
         "Whether any emitted value leaves the observed label band."],
        "Are you scored on calibration, or on distance to a labeled number? "
        "They are different objectives.",
        ["confidence", "calibration"]),

    ProposalClass(
        "personalize", "Add a personalisation or context signal",
        [r"personali[sz]", r"per.?user", r"quiet hours", r"time of day",
         r"user preference", r"behaviou?r", r"history.?based", r"recency"],
        [DEAD_SIGNAL, OVERFIT],
        ["Association between the signal and the label. Cramer's V, or an output "
         "diff with the signal zeroed.",
         "Whether the signal varies WITHIN the comparison set, not just across "
         "the corpus."],
        "Does this signal vary within the set of things you are comparing? If it "
        "is constant there, it reorders nothing.",
        ["personalization", "features"]),

    ProposalClass(
        "llm-decision", "Put an LLM into the decision path",
        [r"llm.*(decide|classif|route|arbitrat)", r"(decide|classif|route).*llm",
         r"ask (the )?(model|gpt|claude)", r"prompt.*(classif|decid)",
         r"arbitrat", r"agent.*decid"],
        [NONDETERMINISM, INJECTION, NETWORK_IN_TESTS, BLAST_UNMEASURED],
        ["Count of rows where the deterministic path is WRONG and the LLM could "
         "act. If the deterministic verdict is already correct everywhere the "
         "LLM is eligible, every intervention is a guaranteed regression.",
         "An injection probe: a row whose text instructs the model to misroute.",
         "Whether the feature is gated on INTENT or merely on credential presence."],
        "On how many rows is the deterministic answer actually wrong? That is the "
        "entire upside.",
        ["llm", "determinism", "security"]),

    ProposalClass(
        "refactor", "Restructure without changing behaviour",
        [r"refactor", r"clean ?up", r"reorgani[sz]", r"rename", r"extract",
         r"split .*(module|file)", r"tidy"],
        [Risk("behaviour change disguised as a refactor",
              "The definition of a refactor is that output does not change. "
              "Without a pinned artifact you cannot claim that.",
              "Byte-compare the full output artifact before and after. If it "
              "differs, this is not a refactor.", "high")],
        ["Byte-identical output artifact.",
         "Every test file passing IN ISOLATION, not only as a suite."],
        "Do you have a pinned output hash? Without one, 'no behaviour change' is "
        "an assertion, not a claim.",
        ["refactor"]),

    ProposalClass(
        "test", "Add or change tests / evaluation harness",
        [r"\btest\b", r"\btests\b", r"harness", r"benchmark", r"ablation",
         r"evaluat", r"\bcoverage\b", r"assert"],
        [HARNESS_LIES, NETWORK_IN_TESTS,
         Risk("an audit that mutates what it audits",
              "A benchmark that invokes the CLI without an output flag "
              "overwrites the real artifact (F-34).",
              "Hash the artifact before and after running the new harness.",
              "blocker")],
        ["A NEGATIVE CONTROL: break the thing deliberately and confirm the "
         "harness reports the break. A harness that has never failed has never "
         "been tested.",
         "The artifact hash, unchanged, after the harness runs.",
         "The harness's behaviour with credentials cleared."],
        "If you deliberately broke the component, would this harness notice?",
        ["testing", "audit"]),
]

DEFAULT_CLASS = ProposalClass(
    "general", "General change",
    [],
    [BLAST_UNMEASURED, COUPLING, OVERFIT],
    ["Full-output diff, in the shipped configuration.",
     "The metric this change improves, named before the change is written."],
    "What number gets better, and by how much, and how would you know?",
    [])


def classify(proposal: str) -> list[ProposalClass]:
    """Return every matching class, best first. Multi-class is normal --
    'use a local Whisper model' is both add-model and perf."""
    scored = [(c.matches(proposal), c) for c in CLASSES]
    hits = sorted([(s, c) for s, c in scored if s], key=lambda x: -x[0])
    return [c for _, c in hits] or [DEFAULT_CLASS]
