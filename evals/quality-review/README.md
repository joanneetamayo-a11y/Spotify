# Development quality review — no new model executions

The exact deterministic 1,000-review verification sample contains 748 agreements and 252 disagreements on topic/intent/severity. Field disagreements overlap: 142 topic, 92 severity, 72 intent. Counts are model comparisons, not accuracy.

Open worksheet.html. Twelve cases were selected in deterministic review-ID hash order, taking the first short review (at most 700 characters) for each distinct field/direction disagreement pattern. This deliberately varied development selection is not a representative accuracy estimate. Original text and IDs are preserved. Human fields start blank; model suggestions are hidden until requested. Export the completed CSV. Do not feed human judgments into model prompts or overwrite the original golden set.

The injection case returned complaint despite praise and severity 1. This is consistent with instruction text contaminating intent, but the saved response alone cannot establish the model's internal cause. The refund case inferred cancellation without explicit departure; the intended rubric outcome is complaint. These are two regression cases, not a comprehensive robustness test.

A proposed instruction revision is saved in candidate-instructions.md. It has NOT been executed or shown to improve quality. Existing predictions and model configuration are unchanged. Any tuned configuration requires a new version/cache identity and a bounded explicit paid test. Test known regressions and separately authored fresh synthetic examples; report them separately, and assess a fresh human-reviewed holdout before claiming general accuracy improvement. Do not reuse this diagnostic worksheet as an unbiased test set.
