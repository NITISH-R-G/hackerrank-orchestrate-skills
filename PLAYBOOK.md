# The AI Engineering Playbook

**How to build AI systems whose correctness you can prove — and how to know when
to stop.**

This is a methodology, not a framework. There is no library to install. Every
principle below is stated as a rule, justified, and then demonstrated with a
real failure that the rule would have caught. The failures are real: they come
from a system built under competition constraints and audited to destruction.

> Its usefulness is not that the system scored well. It is that **nine
> plausible improvements were measured and rejected**, and that **three of the
> audits were themselves wrong** in ways that produced clean-looking passes.

---

## Who this is for

You are building something where "it looks right" is not good enough:

- an AI product going to production
- a competition submission graded against labels you cannot see
- a research artifact someone will try to reproduce
- an interview take-home someone will try to break

## The one-sentence version

> **Measure before you ship, measure the blast radius, prove the counterfactual,
> and attack your own measurement before you trust it.**

---

# Part I — Evidence discipline

## P1. A change is not an improvement until a number moves

**Rule.** Every change must name the metric it improves, the measurement that
proved it, and the metric it costs. "Cleaner", "more robust", "should help" are
not admissible.

**Why.** Intuition about AI systems is unusually bad, because the failure modes
are statistical and the feedback is delayed. Your prior is not evidence.

**Case study — the confidence function that felt right.**
A dynamic per-message confidence score ("more matched signals ⇒ higher
confidence") is obviously better than a fixed per-rule constant. Measured
against ground truth: **MAE 0.0287 dynamic vs 0.0263 static** — worse overall,
and worse on *every* action subset. It also emitted values outside the observed
band on 3/30 rows, masked only by a clamp.
**It was deleted, not disabled.** Disabled code is a future accident.

**How to apply.** Before writing the change, write down: *what number will move,
by how much, and how will I know?* If you cannot answer, you are not ready to
write it.

**Failure mode.** Metric shopping — running five metrics and reporting the one
that moved. Fix: name the metric *first*.

---

## P2. Measure the blast radius, not just the win

**Rule.** Alongside "what does this improve", always compute **how many outputs
change**. A one-row gain that rewrites 21% of your output is not a one-row
change.

**Case study — the retrieval swap that looked free.**
An alternative ranker scored **+1 row** on any-overlap and **+0.5** on recall.
Tempting. Blast radius: **12 of 110 output cells changed set, 11 more
re-ordered — 23 cells, 21% of the submission** — to buy a one-row gain whose
95% CI spanned roughly ±0.17. Rejected.

Later, a *different* ranker change was accepted — because it was **diagnosed**,
not aggregate. The correct evidence ranked 6th of 21; five near-duplicate
10-token boilerplate messages outranked it because the similarity function
divided by `min(|a|,|b|)`, structurally preferring short documents. That is a
defect with a mechanism, not a wiggle.

**The distinction that matters:** *aggregate improvement* is weak evidence;
*a diagnosed mechanism plus an aggregate improvement* is strong evidence.

---

## P3. Prove the counterfactual, or you have proven nothing

**Rule.** To claim component X drives outcome Y, show **both**:
1. with X enabled, Y happens, and
2. with X disabled, Y **stops** happening.

Only (1) is compatible with X being decorative.

**Case study — is the image pipeline real?**
Claiming "we do OCR" is unfalsifiable. The test that isn't: generate posters
whose scam text exists **only in pixels**, with innocuous accompanying text.

```
                     OCR ON              OCR OFF
otp-harvest          mute/scam           digest/unknown
wallet + bit.ly      mute/scam           digest/unknown
refund + bank a/c    mute/scam           digest/unknown
...
                     7/7 caught          7/7 escaped
```

Both halves hold ⇒ image content *determines* the verdict. Had the second column
also shown `mute`, something else was doing the work.

**Apply it to:** retrieval (shuffle the index), memory (clear it), a
re-ranker (bypass it), a guardrail (remove it), any RAG component at all.

---

## P4. Compute the ceiling before you optimise

**Rule.** Before improving a component, compute the **maximum achievable gain**.
Often it is zero, and you save yourself a week.

**Case study — the vision model that was never needed.**
Question: does this need real visual understanding beyond OCR? Instead of
building a model and hoping:

1. **Headroom.** On the only image rows with ground truth, the system was
   already **5/5**. Maximum possible gain: **0 rows**.
2. **Reachability.** Of 15 graded image rows, **13** were decided by rules that
   never read media at all. Reachable: 2.
3. **Build the thing anyway.** An exhaustively-tuned pixel classifier (searched
   over every threshold on every feature pair — a maximally overfit upper bound)
   reached 19/20 and **failed on precisely the one image it existed to serve**.

Three independent proofs of "no", obtained in an afternoon. Note step 3: the
strongest possible version of the idea was built, not a strawman.

---

## P5. Rejection is a deliverable

**Rule.** Keep a written record of every idea you tested and rejected, with the
number that killed it. This is more valuable than your feature list.

Real rejection log from one system:

| Idea | Killed by |
|---|---|
| dynamic confidence | MAE 0.0287 vs 0.0263 |
| dense embeddings / RRF / cross-encoder | F1 0.479 vs 0.512 |
| temporal / metadata / behaviour re-ranking | **byte-identical** metrics |
| widening the retrieval pool | ceiling 84%→100%, but F1 0.512→0.483 |
| user quiet-hours personalisation | Cramér's V = **0.000** |
| ECE recalibration | ground truth's own ECE was *worse* than ours |
| a visual model | best possible classifier fails on the one image that matters |

**Why it matters.** "We use embeddings" is a claim anyone can make. "We measured
embeddings at F1 0.479 against 0.512 for lexical and did not ship them" cannot
be faked, and it is the single most credible thing you can say in a review.

---

# Part II — Auditing the audit

*This is the part most teams skip, and it is where the real defects were.*

## P6. A passing test proves nothing until the test itself is attacked

**Rule.** When a check reports a clean result, ask: *what would this check do if
the thing it measures were broken?* If you cannot answer, the check is decoration.

**Case study — the harness that measured nothing.**
An ablation reported a beautifully clean **"0 of 110 rows changed"**. It was
wrong. The harness monkeypatched `media.build_media_backend`, but the pipeline
had already bound that name into its own namespace at import:

```python
from .media import build_media_backend      # bound at import time
...
media = media or build_media_backend()      # patch never observed
```

Both arms silently ran the null backend. Real answer: **5 rows**. A clean zero
from a broken harness is the most dangerous result in engineering, because it
*confirms* what you expected.

**Case study — the reachability prober that lied twice.**
A tool searching for unreachable rules reported "3 rules are DEAD CODE" and "7
are shadowed". Both false:
- it randomised only the fields matching a naming prefix — 23 of 37 booleans —
  so rules gated on the others could never be satisfied;
- it returned the *first* match and reported whoever won, and since it
  randomised safety flags at p=0.5, a safety rule won almost every draw.

After correction: **1 genuinely unreachable rule, 0 shadowed.**

**How to apply.** For every audit, write a *negative control*: deliberately
break the property and confirm the audit screams. If it stays green, fix the
audit before trusting any of its output.

---

## P7. An audit must never mutate what it audits

**Rule.** Verification is read-only. If it must write, it writes to a temp path.

**Case study.** A performance benchmark invoked the pipeline's CLI without an
output flag — so it overwrote the **submission artifact**, three times per run,
with a degraded configuration. It silently reverted a correctly-classified scam
back to benign. Discovered only because a later check compared hashes.

**How to apply.** Run your full verification suite, then diff every artifact.
Anything that changed, changed because a verifier wrote to it.

---

## P8. Measure the right thing, at the right scale

**Rule.** When a metric is unstable across runs, suspect the metric before the code.

**Case study.** A scaling check reported growth exponents of 1.01, then 1.34,
then 1.60, then 1.53 — **on identical code**. Cause: a two-point endpoint
estimate from single timings, measured at 64× the maximum input the system can
ever receive. At that size the data no longer fits in cache, so it was measuring
the memory subsystem. Corrected to the reachable range with best-of-3 and a
least-squares fit over all points: **exponent 1.01, stable.**

**The general trap:** benchmarking outside the operating envelope, then
"fixing" a problem that cannot occur.

---

# Part III — Regression engineering

## P9. Pin the output, not the intention

**Rule.** Keep a golden hash of your system's full output. Any change to it must
be a *decision with a recorded cause*, never a silenced test.

```
RE-PIN LOG
  5b1a8012 -> acf8c51c
    Cause : "unsubscribe" added to the promotional lexicon
    Effect: exactly ONE row changes
    Why right: that row's text is byte-identical to a LABELED row,
               from the same sender, labeled digest/promotion
    Score : labeled set 29/30 -> 30/30
```

The log is the artifact. A golden test with no re-pin log is a test people
learn to overwrite.

**Pin the deterministic core, not the environment-dependent artifact.** If your
output depends on which credentials are present, pin the offline configuration —
otherwise the test fails for correct runs and passes for wrong ones.

---

## P10. Tests must be hermetic or they are lying about something

**Rule.** A test's result must not depend on what happens to be in your
environment.

**Case study.** A determinism test called the pipeline twice and asserted the
outputs matched. With an API key present it made **two independent network
calls** and asserted a third-party speech service is bit-stable. It is not — it
failed on one row. The test was not measuring the system's determinism; it was
measuring someone else's uptime.

Fix: an autouse fixture clearing every credential. Side effect: the suite went
from 47 s to 4 s, because a dozen other tests had been quietly making live calls.

**Corollary — order-independence.** The same suite passed only by *accident of
alphabetical import order*: an earlier file performed a `sys.path` insert, so
later files could import the package. Running one file alone failed outright.
**Always run each test file in isolation as part of CI.**

---

## P11. State the boundary of every guarantee

**Rule.** Unqualified guarantees are false. Say exactly where each one stops.

Bad: *"The system is deterministic."*
Good: *"Offline it is byte-identical across 5 processes and 5 hash seeds. With
the hosted speech provider it is not, because that model is not bit-stable — I
have observed the specific row where it varied. The submitted artifact is a file
generated once, so this does not affect it."*

The second version is the one that survives cross-examination, and it is the one
a reviewer trusts.

---

# Part IV — Robustness against data you cannot see

## P12. Hunt for accidental coupling to your sample

**Rule.** Assume the evaluation data differs from your sample in every way the
specification does not explicitly fix. Then go looking.

**A concrete taxonomy** — for each, ask: *is this fixed by the spec, or by my sample?*

| Coupling | Test |
|---|---|
| ID **format** | rename all IDs to a different scheme; do decisions survive? |
| Timestamp format | rewrite dates day-first; does ordering survive? |
| Row order | shuffle every context file; does output survive? |
| Directory layout | rename the media folder; does resolution survive? |
| Filename ↔ content | verify format by magic bytes, never extension |
| Exact wording | which lexicon terms fire on exactly **one** sample row? |

**Case study — three real couplings, all found late.**

1. **ID shape.** Mention detection harvested tokens matching `@u_\d+`, then
   compared them to the recipient's ID. The comparison was principled; the
   harvest pattern was not. Renaming IDs to `user-NNN` broke **4 of 110
   decisions** — two rules went silently dead. Fixed by searching for `@` +
   *the actual recipient ID*, assuming no format.

2. **Timestamp format.** History was sorted with a raw **string** sort —
   chronological only for zero-padded ISO. Rewriting dates as `DD/MM/YYYY`
   produced different output.

3. **Copied wording.** A lexicon contained `price is` — a copula fragment
   transcribed from one sentence, firing on exactly **1 of 537** texts. Replaced
   with the underlying category (a resale listing states a collection point and
   a price), which is broader *and* correctly rejects "school bus pickup is…",
   which the copied version wrongly matched.

**The tell for overfitting a lexicon:** count how many corpus rows each term
matches. Terms matching *exactly one* are suspects. Terms matching *zero* are
usually fine — they are generalisation cover and cannot overfit data they never
touch.

---

## P13. Distinguish "specified" from "observed"

**Rule.** Every constant is one of: fixed by the spec, measured by experiment, a
standard from the literature, a bound from an external standard, or a judgement
call. **Know which, for every number you ship.**

This matters in review. "Chosen after evaluation" applied to a value you took
from a textbook is a fabrication that collapses under one follow-up.

The honest posture: *"I tuned what I could score. Everything else is a
documented judgement call, and I know which is which."*

Ship a `CONSTANTS.md` with a provenance column. It takes an hour and it is the
difference between owning a system and having assembled one.

---

## P14. Match the target, not your intuition about the target

**Rule.** When calibrating against a labeled set, calibrate to **the labeling
policy**, not to an abstract ideal.

**Case study.** A system showed Expected Calibration Error of 0.138 —
systematically under-confident. An obvious fix. Before applying it: what is the
**ground truth's own ECE**? Answer: **0.1597 — worse**. The labels are
deliberately under-confident. Every ECE-improving shift made error against the
actual target strictly worse (0.026 → 0.147).

Optimising a textbook metric moved the system *away* from the thing being scored.

---

# Part V — Release engineering

## P15. Simulate the consumer, from nothing

**Rule.** Clone to an empty directory, install nothing, and follow only your own
README. Every deviation you have to make is a defect.

Real defects this found:
- `pytest` from the repo root **aborted the entire suite** — a stale exploratory
  script named `test_*.py` executed API calls at import. 63 passing tests
  reported as a red, interrupted run.
- The clone had **2 files** under `code/` — essentially nothing was committed.
  Locally everything worked. `git status` had been reporting untracked files for
  hours and nobody read it.
- Documentation recommended a flag that **disabled the product's headline
  feature**.

**Automate it.** A `cert_fresh_clone` script that clones, runs, and diffs is
~150 lines and catches an entire class of "works on my machine".

---

## P16. Stale artifacts are the default state

**Rule.** Any generated artifact is stale until proven current, *in the same
breath* as the code that generates it.

**How.** Regenerate to a temp path, hash both, compare. Do this in your release
gate, not by memory. An artifact three commits behind its code looks identical
in a file listing.

---

## P17. Documentation is production code

Stale docs are defects. Real examples found in one release pass:

- runtime claim off by **180×** (a dependency change had made it slower)
- a recommended command that turned off a required capability
- scores from three commits earlier
- a test count that had grown from 63 to 81

**Put doc claims in the release gate.** If the README states a number, something
should verify it.

---

# Part VI — Reporting honestly

## P18. Separate fact, measurement, inference, and unknown

Label them explicitly. In writing, and out loud.

- **VERIFIED** — I executed this and here is the output
- **MEASURED** — here is the number and the script that produced it
- **INFERENCE** — I concluded this; here is the reasoning
- **UNKNOWN** — this cannot be determined with the information available

The instinct to blur these is strong under pressure. Resist it. A reviewer who
catches one overstatement re-examines everything else you said.

## P19. Name the limitation before you are asked

State the ceiling, the residual risk, and what you could not test. Volunteering
a limitation converts it from an accusation into evidence of rigour.

## P20. Know when to stop

Stop when **either**:

1. everything fixable has been fixed and re-verified, **or**
2. the only remaining uncertainty depends on information you cannot access.

Condition 2 is a real, respectable stopping point — but only if you can *name*
the missing information precisely. "Hidden labels" is not precise. "The
evidence-ID scoring function; the output artifact ships without the label
column; the sample IDs are disjoint from the graded set — this information is
absent from the data, not merely unexamined" is.

---

# The loop

```
   ┌────────────────────────────────────────────────┐
   │  1. State the claim and the metric FIRST       │
   │  2. Compute the CEILING — is a gain possible?  │
   │  3. Build the strongest version of the idea    │
   │  4. Measure: gain, cost, blast radius          │
   │  5. Prove the COUNTERFACTUAL                   │
   │  6. Attack your own measurement (P6)           │
   │  7. Ship or reject — log the number either way │
   │  8. Pin the output; record the cause           │
   └────────────────────────────────────────────────┘
```

Step 6 is the one that separates this from ordinary rigour. Three of the audits
described here were wrong on first execution, and each produced a *clean,
confirming* result. Two would have shipped a false conclusion.

---

# Appendix: the twenty rules

1. A change is not an improvement until a number moves
2. Measure the blast radius, not just the win
3. Prove the counterfactual, or you have proven nothing
4. Compute the ceiling before you optimise
5. Rejection is a deliverable
6. A passing test proves nothing until the test itself is attacked
7. An audit must never mutate what it audits
8. Measure the right thing, at the right scale
9. Pin the output, not the intention
10. Tests must be hermetic or they are lying about something
11. State the boundary of every guarantee
12. Hunt for accidental coupling to your sample
13. Distinguish specified from observed
14. Match the target, not your intuition about the target
15. Simulate the consumer, from nothing
16. Stale artifacts are the default state
17. Documentation is production code
18. Separate fact, measurement, inference, and unknown
19. Name the limitation before you are asked
20. Know when to stop

---

*Every case study is drawn from a real system. The numbers are measured, not
illustrative.*
