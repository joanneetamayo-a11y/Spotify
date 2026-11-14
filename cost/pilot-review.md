# Pilot review — 2026-10-23

Both API keys authenticated. Real Jev classification and Luna verification/grouping/memo requests ran. All 100 supplied pilot reviews are classified and saved with original IDs, hashes and exact quotes.

The initial cold attempt was interrupted by an OpenAI JSON-input format rejection. A logged diagnostic attempt confirmed it. Both rejected attempts retain unknown charges and spend reservations. One Jev validation retry and three memo citation failures are included in measured usage. Short evidence references fixed UUID transcription errors while preserving original IDs in validated results.

Known usage-based API subtotal: **$0.013942778 USD**. This is not a reconciled account bill; two rejected requests have no provider usage. The $1 shared cap retained their reservations.

Measured execution legs: 279.875 seconds initial cold attempt, 64.843 seconds first recovery, 5.995 seconds successful recovery. Their sum excludes intervention time and is not an uninterrupted end-to-end cold benchmark. Warm replay: **0.015320 seconds, zero API calls, zero new enrichment calls, $0 incremental API spend**.

Blind verification agreed on topic, intent and severity in 8/10 cases. Both disagreements were severity 3 versus 2 for ad complaints. This is inter-model agreement, not accuracy against human ground truth. The configured 85% agreement gate is not met.

Base reuse scenario from known usage is approximately **$8.96 per 100,000 input reviews**; conservative reuse scenario is approximately **$12.91 per 100,000** before unresolved charges. These are estimates, not executions. The conservative case exceeds the user's $10 ceiling, so no 500/10,000/full paid run was started. The full dataset remains unclassified in the final grading export. The supplied checker ran and reports the expected incomplete classification and resume evidence.

Next work: improve severity consistency and reduce prompt/verification overhead, measure another controlled pilot while retaining this experiment's evidence, reconcile rejected-request billing, then reassess the scaling gates. The live dashboard has not yet been refreshed with this pilot; it must not imply full-corpus classification.
