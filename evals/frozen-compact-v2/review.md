# Frozen configuration evaluation

The compact-v2 configuration was fixed before this evaluation. Human answers were read only by the offline comparison, never supplied to the classifier or verifier. All original human answers remain unchanged. No prompt changes were made from golden results.

49 of 50 reviews have valid predictions. One review exhausted its one invalid-output retry (intent/severity inconsistency); it remains incomplete and counts as disagreement. Topic agreement is 14/50 (28%), intent 41/50 (82%), severity exact 32/50 (64%), needs-review 34/50 (68%). Severity mean absolute error is 0.4082 over 49 completed cases; sentiment MAE is 0.2837 over those 49. Five human cases were marked ambiguous. These are small-sample agreement diagnostics, not population accuracy.

## Error analysis
21 human usability labels were predicted other. Examples include “Great app use it every chance I get” (a70e8d3e-3f84-46bc-b008-67f476c67963) and “I just loved it” (599a0d41-989a-40ef-8ed2-e92db76eea46). The common rubric places general praise without a specific feature in other; usability covers particular controls/navigation/ads. This indicates a human/model taxonomy interpretation difference in these examples, not proof that every model label is correct. Do not silently replace the human labels to improve scores. Any adjudication must be separately attributed, and any subsequent model tuning requires fresh held-out evaluation.

All 49 completed model quotes are exact source substrings because Jev uses the entire source review as evidence. That does not establish semantic support. The adapter returns empty entity lists: unsupported additions are avoided but entity completeness is not demonstrated. Human inspection of quote support, multilingual uncertainty, and entity omissions remains outstanding.

## Real adversarial tests
5/7 cases passed the declared topic/intent/severity expectations. One injected fake SYSTEM message changed the predicted intent from praise to complaint; severity remained 1. The login-plus-refund case was labeled cancellation instead of complaint, showing an intent-boundary ambiguity. Both failures are retained in adversarial.json. The independent blind verifier detected the separate planted topic/severity error and returned access/complaint/4. Synthetic cases are separate artifacts, not business-aggregate rows.

## Costs and recovery
Evaluation usage-based API subtotal: $0.002682994 (all evaluation attempts, including invalid outputs). Compact pilot plus evaluation shared ledger total: $0.009478648, within the cumulative $0.05 cap. These are saved-usage calculations, not reconciled provider invoices. Earlier experiment charges remain separately recorded.

Initial evaluation saved 23 valid predictions and failed after two invalid attempts on another review. Resume skipped those 23 and the exhausted record, then added 26 valid predictions. Checkpoint snapshots and calls record this; a recording is still missing. A cloud-offloaded database caused a local I/O error before further dispatch; a verified database copy preserved all 137 then-existing calls and the same spend ledger. The resulting database was backed up to data/compact-v2.sqlite and passed integrity_check.

## Decision
Do not declare the adversarial gate passed or start 500 automatically. Review the demonstrated injection failure and taxonomy interpretation. Preserve this baseline. Further prompt changes should use synthetic/development data and fresh held-out cases, not the human golden answers.
