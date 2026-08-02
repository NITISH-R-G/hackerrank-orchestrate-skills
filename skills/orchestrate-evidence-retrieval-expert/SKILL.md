---
name: orchestrate-evidence-retrieval-expert
description: Design and defend the evidence column. Use when building retrieval or considering a ranker change. Covers the ceiling analysis that tells you whether a gain is possible at all, and why the fashionable option often loses.
---

# Orchestrate: Evidence Retrieval Expert

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Compute the ceiling before you optimise. Then benchmark the fashionable option and
publish the number when it loses.**

## Step 1 — the pool bounds everything

No ranker can retrieve an id that is not in the pool it ranks. Measure this first:

```
rule-scoped pool  26/31 = 83.9%   <- what ships
all-user pool     31/31 = 100%    <- higher ceiling
```

Tempting. But measured end to end, the wider pool scored **F1 0.483 vs 0.512** — the
extra candidates cost more precision than the recovered recall was worth.

**A higher ceiling is not a higher score.**

## Step 2 — benchmark the fashionable option

153 configurations (3 pools × 17 rankers × 3 values of k), scored only on labeled rows:

| ranker | F1 |
|---|---|
| BM25 | **0.512** |
| tf-idf / jaccard / hybrid | 0.496 |
| dense embeddings, RRF, cross-encoder | **0.479** |
| recency only | 0.336 |

**Every neural method lost to plain lexical matching.** The relation being scored was
topical word overlap, not paraphrase — bi-encoders are built for the wrong thing here.

Also measured: temporal, metadata and behaviour re-ranking produced **byte-identical**
metrics. The pools were already scoped by conversation and relationship, so applying
those signals again was a no-op.

## Step 3 — prefer a diagnosed mechanism over an aggregate wiggle

One ranker change *was* adopted, because it had a mechanism:

The correct evidence ranked 6th of 21. Cause: the similarity function divided by
`min(|a|,|b|)`, so a **short** boilerplate message sharing generic terms outranked a
**longer** one sharing distinctive terms. Five near-duplicate 10-token messages scored
0.600; the truth, with 6 distinctive terms across 18 tokens, scored 0.389.

BM25's IDF weighting plus document-length normalisation is the standard correction.
Any-overlap **22/28 → 23/28**.

*Aggregate improvement is weak evidence. A diagnosed mechanism plus an aggregate
improvement is strong evidence.*

## On k (how many ids to cite)

Measure it; do not guess. In the real build the labeled distribution was ~1 id per row,
yet k=3 won recall and any-overlap while k=1 won exact-match and Jaccard, with the F1
difference **one third of one row** and all confidence intervals overlapping. That is a
coin flip on an unknown grading metric — and the honest move is to say so.

## The checklist

- [ ] Pool recall ceiling measured before any ranker work
- [ ] At least one lexical and one semantic ranker benchmarked
- [ ] k swept and reported
- [ ] Every cited id verified to exist, belong to the right user, not self-reference
- [ ] Misses diagnosed: unreachable (not in pool) vs mis-ranked (in pool)
- [ ] Rejections recorded with numbers
