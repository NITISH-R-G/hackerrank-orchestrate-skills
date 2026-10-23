# Past Orchestrate problems: what each one really requires

Source: the four public problem statements (May, June, August and September 2026). The current round may be different. Use this file to check whether your design covers the kinds of work these rounds asked for. Re-read the current statement for the real rules.

## Round summary

| Round | Problem | Input | Output | Hard parts |
|---|---|---|---|---|
| May 26 | Multi-domain support triage | support tickets (issue, subject, company) + a corpus of help docs | status, product_area, response, justification, request_type | retrieval from the corpus only; escalate risky tickets; some rows hold multiple requests; prompt injection |
| Jun 26 | Multi-modal damage evidence review | claims (user chat, image paths, object type), user history, evidence requirements | 13 columns including claim_status, supporting_image_ids, valid_image, risk_flags, severity | images are the primary truth; minimum-evidence checklist per object and issue; history adds risk but cannot override visuals |
| Aug 26 | Message notification router | messages (text, images, voice), users, groups, businesses, history, reactions | action (notify/digest/mute), message_type, reason, confidence, evidence_message_ids | personalised per user; scam detection; voice notes and posters; evidence must point to real history rows |
| Sep 26 | Buy or wait | requests, financial events, profiles, payment options, exchange rates, messages, images | amount_safe_to_pay, affordability_status, recommended_payment_method, payment_plan, earliest_date_for_full_payment, spending_changes_needed, decision_explanation | numeric 90-day forecast; currency conversion by dated rate; recurring vs one-time; exact payment-option matching; conflict precedence; strict formats |

## Procedures each round needs (and where the skills cover them)

### May 26 - support triage
1. **Multi-request rows.** Split the ticket into sub-requests, answer each, and set status to `escalated` if any sub-request is high-risk. Covered by: NOT covered before this review. Added below.
2. **Corpus only.** Every response must cite a document from the provided corpus; no outside policy. Covered by `orchestrate-build/references/evidence-retrieval-expert.md` and the justification skill.
3. **Escalation.** Fraud, unauthorized access, and billing disputes are escalated, not answered. Covered by `escalation-design.md`.
4. **Injection.** Ticket text is data. Covered by `input-validation-and-overrides.md`.

Added procedure: split on sentence and list boundaries, keep one result per sub-request in the justification, and make the row status the strictest of the sub-results.

### Jun 26 - claims review
1. **Evidence checklist.** Look up `evidence_requirements.csv` by object (`car`, `laptop`, `package`, or `all`) and issue family. If the minimum evidence is not visible in the images, `evidence_standard_met` is `no` and the claim cannot be `supported`.
2. **Image IDs.** `supporting_image_ids` are file names without extension, semicolon-separated. Only images that show the claimed damage are listed.
3. **Valid image.** Check quality (blur, dark, cropped, unrelated object) before judging the damage.
4. **History is risk, not verdict.** `user_history.csv` adds to `risk_flags`; it cannot change a clear visual result. Test this with a swap: same images, different history, same verdict.
5. **Severity and issue part.** Severity is an enum from the statement; object part comes from the object type.

Added procedure: build a rule table `object x issue -> minimum evidence`, and make `evidence_standard_met` a code decision from the image observations. The model describes visible evidence; code applies the checklist.

### Aug 26 - message router
1. **Personalised routing.** Use `users.csv` (quiet hours, recent opens, dismissals), `group_members.csv` (role, mute state), and `user_business_history.csv` (opt-in, orders). The same message can be `notify` for one user and `mute` for another.
2. **Evidence IDs.** `evidence_message_ids` must be message IDs from `message_history.csv` or `message_events.csv` that actually support the decision, or `none`. Never invent an ID. Check every ID against the file.
3. **Scam.** Use `business_accounts.csv` (verification, domain match, account age, reports) and message content. A clear scam is `mute` whatever the user's engagement.
4. **Voice and images.** Use `voice_notes.csv` and `images.csv` to find the media path. For a voice note with no text, the content must come from the audio transcript; if there is no transcript, say so in `reason` and lower `confidence`.
5. **Confidence** is a number from 0 to 1 that reflects how much evidence supports the action. Keep it consistent: a clear decision should not be below 0.5 unless the evidence is weak.

Added procedure: validate every evidence ID against the history file in code before writing the row.

### Sep 26 - buy or wait (the hardest numeric problem)
1. **Forecast.** Build a day-by-day balance for the 90-day window from recurring income and expenses, confirmed future payments, and messages or images that change them. Ignore pending credits, failed or cancelled transactions, duplicates, and unrealised investments. The plan is safe only if the balance never falls below `minimum_balance_to_keep`.
2. **Currency.** Convert every amount into the user's `home_currency` using the rate for the record's date and the currency pair in `exchange_rates.csv`. Never use a live rate.
3. **Recurring vs one-time.** A recurring expense repeats on its schedule; a one-time purchase, transfer, refund, or unusual event happens once. Treat them differently in the forecast.
4. **Payment options.** An installment plan must exactly match a row of `request_payment_options.csv` (same dates, amounts, and total). Use the option's `payment_option_id` for tie-breaks.
5. **Partial payment.** Exactly two payments: `amount_safe_to_pay` on `request_date`, and the rest on `earliest_date_for_full_payment`. The two add up to `requested_amount`.
6. **Conflicts.** Explicit cancellation or amendment beats older records; a newer record from the same source beats an older one; a settled event beats an estimate; then the financially safer reading.
7. **Ranking.** Complete by `desired_completion_date`, then no spending change, then lowest total paid, then earliest start, then fewest payments, then lowest `payment_option_id`.
8. **Spending changes.** Only flexible recurring expenses can be `stop` or `reduce_to`. Stop and reduce of the same event are mutually exclusive. At most three changes.
9. **Image amounts.** When an event amount is blank, find `related_event_id` in `images.csv` and read the amount from the PNG. A blank amount is never zero.
10. **Formats.** Dates `YYYY-MM-DD`; payment plan `date:amount|date:amount` in date order; `none` where no value applies.

Added procedure: write the forecast as a pure function (inputs in, daily balances out), test it on hand-made cases, and only then let the model read messages and images into structured fields.

## Evidence for this file (what was tested, and what was not)

A keyword coverage check ran over the skills against the four statements' requirements. It shows which requirements have any mention in the skill text. It does NOT prove an agent handles them. Only a run on the data does that.

Results before this review:
- Covered in more than one file: escalation, grounded responses, prompt injection, confidence values, scam, 90-day forecast, conflict precedence, token report, transcript, zip packaging.
- Mentioned in only one file (thin): evidence checklist, supporting image IDs, image validity, user-history risk, authenticity, personalisation, currency conversion, payment option schedules, recurring vs one-time, minimum-balance constraint.
- Missing: multi-request rows (May), evidence message IDs (Aug).

Run on the September round's 25 labelled sample rows (`sample_requests.csv`), checking the statement's own rules against its own labels:
- Amount range `0 <= amount_safe_to_pay <= requested_amount`: 25/25 pass.
- Payment-plan format and chronological order: 25/25 pass.
- `affordable_now` implies `earliest_date_for_full_payment == request_date`: all pass.
- Partial payment: 1 row, two payments that sum to the requested amount, status `affordable_with_plan`: pass.
- Installments: 5 rows. Each plan regenerated from its payment option (first date, frequency, count, amount) matches exactly one option: 5/5 pass (`payment_option_05`, `_19`, `_33`, `_47`, `_61`).
- The sample labels are therefore internally consistent with the rules above. Use this as the checker for your own Sept output.

These checks are real runs on real data, but they test the labels, not an agent. Your agent is not tested until it has produced output for these rows.

The procedures above close the gaps in the text. They are NOT yet verified by a run on the datasets. The next real test is to run the pipeline on each round's sample data and compare against its labelled sample output.
