---
name: orchestrate-security-auditor
description: Attack your own submission across injection, unicode evasion, regex denial of service, path traversal, and malformed media. Use before release. Every failure path must degrade to a valid output rather than crash.
---

# Orchestrate: Security Auditor

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The rule

**Every hostile input must produce a valid output row. A crash is a lost row; a
swallowed exception is a silent wrong answer.**

## The attack surface, with what each one found

**Regex denial of service.** An unbounded quantifier on a domain-label pattern took
**40.3 seconds** on a single 40 KB message. Bounded to the RFC 1035 limit of 63
octets: **0.29s**, a 139× improvement, output hash unchanged. Bound every quantifier
with a real standard, not a guess.

**Prompt injection.** A rule engine is structurally immune when message text never
enters a decision-making prompt. If any component *does* put user text in a prompt —
an arbitration step, a re-ranker — that component is your injection surface, and you
should be able to name it.

**Unicode evasion.** Homoglyph, fullwidth, zero-width, RTL override, combining marks,
punycode, emoji-splitting, leetspeak, letter-spacing. Each must be neutralised for
**lexicon matching only** — never let de-obfuscation corrupt user-visible output.

A real trap: a de-obfuscation fix that collapsed `"Share the O T P now"` into
`"SharetheOTPnow"` **destroyed the word boundaries** the credential pattern needed.
The fix disabled the match it existed to enable.

**CSV/formula injection.** If attacker text can reach an output cell beginning `=`,
`+`, `-`, or `@`, a spreadsheet will execute it. Templated reason strings avoid this
by construction.

**Path traversal.** A media id of `../../../etc/passwd` must not resolve outside the
dataset directory.

**Malformed media.** Missing, empty, corrupt, unsupported format, wrong MIME, wrong
extension — all must yield a valid row.

## The checklist

- [ ] Pathological regex inputs timed; every quantifier bounded
- [ ] Injection payloads (prompt, control token, chat template) routed correctly
- [ ] Unicode evasion battery, including letter-spacing and bidi
- [ ] No attacker text reaches an output cell that a spreadsheet would execute
- [ ] Traversal ids resolve inside the dataset or not at all
- [ ] Corrupt/missing/wrong-type media each produce a valid row
- [ ] Resource scaling measured **inside** the reachable input range
- [ ] No secrets in tree, package, or git history

## Failure modes

- **Benchmarking outside the envelope.** A scaling check at 64× the maximum possible
  input measures your memory subsystem, not your code.
- **Broad excepts that swallow.** Degrade deliberately, and log the reason.
