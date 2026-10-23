# Recorded run: August sample, deterministic baseline

Command (from the repo root):

```bash
python skills/orchestrate-build/scripts/run_pipeline.py \
  --input past-august26/dataset/sample_messages.csv --output aug_baseline_output.csv \
  --decider baseline_aug_router:decide \
  --columns message_id,action,message_type,reason,confidence,evidence_message_ids \
  --allowed action=notify,digest,mute --failure-default action=digest \
  --failure-default message_type=unknown --checkpoint aug_ckpt.jsonl
```

## Result
- Rows: 30. Row or column failures handled: 0.
- **Action accuracy: 21/30 = 70.0%.**
- **message_type accuracy: 15/30 = 50.0%.**
- Resume test: a second run from the checkpoint produced a byte-identical file.

## Caveat that matters
The rules in `baseline_aug_router.py` were written after reading these same sample labels. So 70% is an **optimistic** figure, not a held-out score. It shows the pipeline runs, validates, checkpoints and resumes. It does not show generalisation.

## Misses (action)
| Message | Predicted | Gold | Why |
|---|---|---|---|
| sample_msg_005 | digest | notify | health update rule missing |
| sample_msg_009 | mute | digest | "Good morning" greeting treated as mute; gold says digest |
| sample_msg_010 | notify | digest | "tonight" triggered the urgent rule |
| sample_msg_042 | digest | notify | voice note, no transcript |
| sample_msg_043 | digest | mute | voice note, no transcript |
| sample_msg_045 | digest | mute | image-only context |
| sample_msg_046 | digest | notify | school circular: image context |
| sample_msg_048 | mute | digest | safety advisory from a verified brand was muted as scam |
| sample_msg_050 | notify | digest | "Don't call now" triggered the urgent rule on "call" |

## What this tells the build phase
1. Negation breaks keyword rules ("Don't call now" -> notify). Add a negation check before the urgent rule.
2. Voice and image rows need a media step: transcript or vision. The baseline cannot read them, so those rows are guesses.
3. A verified brand safety advisory must not be muted by the scam rule. Use the business-verification field, not keywords alone.
4. Message type needs its own classifier. Action accuracy is higher than type accuracy here, so type is the weaker part.

## Next step
Replace the keyword rules with the model-plus-code design from `DESIGN.md`, then score it on data the rules were not written from. The challenge's own dataset is the only true held-out set.
