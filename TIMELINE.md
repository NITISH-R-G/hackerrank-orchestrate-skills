# Development Timeline — a real Orchestrate build

**Evidence tier: first-hand (August 2026).** The F-series below is transcribed from the
audit annotations in a completed submission. Numbers are measured.

**Read this for the shape, not the specifics.** Your dataset differs. The *pattern* —
what got found, when, and what it cost — repeats.

---

## An honest note on git history

The solution landed in **one commit**. F-1 through F-33 have no commit of their own —
they exist as annotations at the site of each fix and as prose in audit documents. Only
F-34 onward map to individual commits.

**If you tell a judge "my git log shows my process", check it first.** Squashed history
is normal and takes ten seconds to verify. The defensible framing:

> *"The defect log lives in the code, not the git history — every fix is numbered and
> annotated where it was made, with the measurement that justified it."*

---

## Phase 1 — Build (F-1 … F-19)

Correctness and safety. Roughly the first half of the effort.

| # | Finding | Root cause | Impact |
|---|---|---|---|
| **F-1** | Dynamic confidence lost to a constant | Intuition over measurement | MAE 0.0287 vs **0.0263**. Deleted, not disabled |
| **F-3** | `KeyError` ran *before* the row-level exception handler | Handler placed too deep | Total failure → 0 rows. Fixed with guarded access |
| **F-4** | BOM / invalid UTF-8 aborted the whole load | Strict decoding | 0 rows → **110 rows** under injected corruption |
| **F-7** | Media paths resolved from CWD, not the dataset dir | Path assumption | **100% silent** FileNotFoundError, swallowed |
| **F-8** | Dead code read a variable before assignment | Unreachable request body | Provider silently transcribed nothing |
| **F-11** | Vision output universally truncated | Thinking tokens billed against the output budget | 44–71 chars, cut mid-word |
| **F-16** | **Self-inflicted.** A distress rule promoted a real-estate robocall to `notify/urgent` because it named a hospital | Location nouns in a distress lexicon | Root cause was *methodological*: blast radius measured in one configuration, shipped in another |
| **F-17** | **The fix disabled itself.** De-obfuscation collapsed `"Share the O T P now"` → `"SharetheOTPnow"` | Destroyed the word boundaries the pattern needed | 5 evasions → **0** after correction |
| **F-19** | Contradictory rules: one routed *"Ma is in ICU, send money to this UPI"* to `notify` | Two rules encoding opposite policies | Rule deleted — patching would have made it dead code |

**Lesson from F-16:** measure in the configuration you ship. A blast radius computed
with a component disabled is not a blast radius.

---

## Phase 2 — Multimodal (F-20 … F-21, F-28)

| # | Finding | Root cause | Impact |
|---|---|---|---|
| **F-20** | *"The images carry no signal"* — **a wrong conclusion from a real observation** | Two vendors returning nothing was mistaken for a property of the corpus | A local engine extracted **10,104 chars from 19/20** images |
| **F-21** | Image MIME guessed from the filename | **19 of 33** corpus files had deliberately wrong extensions | PNG/WebP/AVIF bytes uploaded as `image/jpeg` |
| **F-28** | Audio MIME guessed from the filename | Same class, other modality | **9 of 13** uploads declared WAV/M4A as `audio/mpeg` |

**Lesson:** when a component returns nothing, prove *where* the nothing came from.

---

## Phase 3 — Auditing the audits (F-22 … F-34)

The most valuable phase. **Three audits were themselves wrong**, and each produced a
clean, confirming result.

| # | Finding | What made it dangerous |
|---|---|---|
| **F-22** | A rule was strictly unreachable — its condition implied an earlier rule's | Proven by implication, not sampling. Deleted; output hash unchanged |
| **F-23** | **ReDoS**: one 40 KB message took **40.3 s** | Unbounded quantifier. Bounded to RFC 1035's 63 octets → **0.29 s** |
| **F-25** | LLM arbitration **silently on** whenever a key existed | Put a network call and raw text into a prompt on 6/110 rows |
| **F-29** | Bare `pytest` **aborted the entire suite** | A stale root `test_*.py` ran API calls at import. 63 passing tests shown as a red run |
| **F-32** | The suite passed only by **alphabetical import order** | One file's `sys.path` insert; a single file alone failed |
| **F-33** | A determinism test asserted a **hosted service** is bit-stable | Suite time **47 s → 4 s** once hidden live calls stopped |
| **F-34** | A benchmark **overwrote the submission artifact** | Reverted a correct scam classification, silently |

**Two broken harnesses, disclosed:**

- An ablation reported a clean **"0 of 110 rows changed"**. It monkeypatched a name the
  consumer had already bound at import, so **both arms ran the null backend**. Real
  answer: **5 rows**.
- A reachability prober reported **3 dead rules and 7 shadowed** — all false. It
  randomised 23 of 37 boolean fields and returned the *first* condition match. After
  correction: **1 unreachable, 0 shadowed**.

> A clean, confirming result from a broken audit is the most dangerous output in
> engineering.

---

## Phase 4 — Hardening and generalisation (F-35 … F-48)

| # | Finding | Impact |
|---|---|---|
| **F-35** | Image text was allowed to reclassify **sender intent** | Scoped to safety only; 2 regressions eliminated, 7/7 pixel-only scams still caught |
| **F-37** | Local OCR made the default vision provider | Image reading became real in the shipped run; **0 of 110** rows changed |
| **F-41** | A marketing *unsubscribe footer* was not a promotional signal | Last labeled miss fixed: **29/30 → 30/30** |
| **F-42** | Similarity metric structurally preferred short boilerplate | `min(|a|,|b|)` normalisation. BM25 → any-overlap **22/28 → 23/28** |
| **F-43** | Mention detection assumed the **shape** of a user id | Renaming ids broke **4 of 110** decisions |
| **F-44** | History sorted timestamps as raw **strings** | Day-first dates produced different output |
| **F-45** | A lexicon term copied verbatim from one sentence | Fired on **1 of 537** texts |
| **F-48** | Local OCR cost **0.25 s → 45 s**, heap 7 MB → 500 MB | Real trade, documented rather than hidden |

**F-41 is the model for a good late fix:** it keys on a *regulatory footer* (3/3
precision on labeled rows) and deliberately excludes a near-identical phrase that
**scams mimic**. Blast radius: 1 graded row — whose text is byte-identical to a labeled
row with that exact answer.

---

## The nine rejections

More valuable than the fixes. Each was built, measured, and **not shipped**.

| Idea | Killed by |
|---|---|
| Dynamic confidence | MAE 0.0287 vs 0.0263 |
| Dense embeddings / RRF / cross-encoder | F1 **0.479** vs 0.512 |
| Temporal / metadata / behaviour re-ranking | **byte-identical** metrics |
| Widening the retrieval pool | ceiling 84%→100%, F1 0.512→**0.483** |
| User quiet-hours personalisation | Cramér's V = **0.000** |
| ECE recalibration | ground truth's own ECE **worse** than ours |
| A visual model beyond OCR | best possible classifier **fails on the one image it exists for** |
| Local ASR | transcribes `OTP` as `OTT` — flips a graded row |
| Evidence cap k=1 / k=2 | metric-dependent coin flip; CIs overlap |

---

## Final state

| Metric | Value |
|---|---|
| Labeled action / type / joint | **30/30** each |
| Evidence any-overlap | 23/28 |
| Tests | 81 |
| Generalization battery | 58/58, 23 attack families |
| Determinism | one hash across 5 processes × 5 hash seeds |
| Rules | 41 — 0 dead, 0 shadowed |
| Defects logged | **48** |
| Optimisations rejected | **9** |

**UNKNOWN:** whether any of this predicts the hidden-label score. The labeled set is 30
rows with an id space disjoint from the graded set. That information is *absent from the
data*, not merely unexamined.

---

## What to take from this

1. **Half the defects were in the verification, not the system.** Budget for it.
2. **The most dangerous results were the clean ones.** Attack every green check.
3. **Rejections are the deliverable.** Nine measured rejections say more about
   engineering judgement than any accuracy number.
4. **Late findings were coupling, not correctness.** F-43/44/45 were found in the final
   hours and none changed a single output row — they were about *hidden* data.
