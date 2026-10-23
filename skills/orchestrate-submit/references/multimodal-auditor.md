---
name: orchestrate-multimodal-auditor
description: Prove that image and audio content actually changes routing decisions, rather than merely being loaded. Use whenever a submission claims multimodal reasoning. The test is the counterfactual: disable the modality and show the decision changes.
---

# Orchestrate: Multimodal Auditor

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Calling an OCR or ASR API is not multimodal reasoning. Media must materially change
the final decision, and you prove it by turning the modality OFF.**

To claim modality X drives outcome Y, show **both**:
1. with X enabled, Y happens, **and**
2. with X disabled, Y **stops** happening.

Only (1) is compatible with X being decorative.

## What this caught in a real build

Two findings, opposite directions:

**The pipeline was dark.** Hosted vision returned **0 characters on 15/15** image
rows, and that was written down as "the images carry no signal". Wrong — it was a
statement about two *remote services*, not the corpus. A local engine extracted
**10,104 characters from 19 of 20** images.

**The proof it was live.** Generated posters whose scam text existed **only in
pixels**, with innocuous accompanying message text:

```
                  OCR ON        OCR OFF
otp harvest       mute/scam     digest/unknown
wallet + shortlink mute/scam    digest/unknown
...
                  7/7 caught    7/7 escaped
```

Both halves hold, so image content determines the verdict.

## Do not let media reclassify intent

Measured: feeding OCR text into *intent* lexicons regressed two rows — an unrelated
calendar screenshot and a generic brochure flipped them from `urgent` to `event`.

The scoping rule that fixed it, derived from the spec itself: **message_text is empty
on 8/8 voice rows** (so the transcript *is* the message and participates fully) and
**non-empty on 15/15 image rows** (so the poster is a supplementary artifact — it may
escalate a safety signal, but must not redefine what the sender meant).

## The checklist

- [ ] Per-item table: id, extraction, routing **with** media, routing **without**
- [ ] Counterfactual proven for **each** modality separately
- [ ] Adversarial media: scam text only in pixels/audio, harmless surrounding text
- [ ] False-positive controls: an anti-fraud awareness poster must NOT become a scam
- [ ] Failure paths: missing file, corrupt file, empty extraction, wrong MIME
- [ ] Format detected by **magic bytes**, never by extension

## Failure modes

- **"It's wired up" as evidence.** It is not.
- **Concluding from a vendor's silence.** Prove *where* the nothing came from.
- **Letting a poster outvote the sender.** Untrusted content escalates safety; it
  does not redefine intent.
