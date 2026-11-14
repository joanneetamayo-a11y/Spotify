# Authorized quality retest

Executed baseline compact-v2 and experimental guarded-v3 on the same 15 synthetic inputs, one worker, empty experiment result caches per arm. Seven are known regression cases and eight were authored before this run. Actual cost $0.001561476, no unknown usage, below the authorized $0.25 new-spend cap. The shared cumulative ledger includes earlier reservations. Every attempt is in calls.jsonl; a baseline validation failure used its one allowed retry and remained missing. Missing predictions count as failures.

Baseline: 5/7 known regressions and 6/8 fresh cases. Candidate: 6/7 and 7/8. Candidate fixed both original failures but misclassified the pure lyrics request as unrelated/unclear. Both arms missed the playback topic for positive playback text containing an injected developer instruction. Candidate is not promoted; full run not approved. These small synthetic results do not establish overall accuracy or fix the saved 10k labels.

Inputs contain only text and synthetic routing IDs. Expected answers are in a separate scoring file, never read by the paid runner. Human golden answers and the 12 human-reviewed cases were not sent. Original source text was not altered. Settings and prompt version differ by arm; model remains Jev 1.14.0.

Offline replay: `python3 -B evals/quality-review/retest/run.py` and `python3 -B evals/quality-review/retest/score.py`. Paid execution requires `--execute-paid`; completed results resume from saved artifacts, and a new unknown outcome stops admission. Do not modify the frozen inputs/code to re-use this experiment. A further candidate needs a new version and declared evaluation.

Next candidate should distinguish legitimate product requests from instructions aimed at the classifier. Retest the lyrics request alongside injection cases and include new tests to avoid fitting only the known examples. Keep a fresh human holdout for general quality evaluation.
