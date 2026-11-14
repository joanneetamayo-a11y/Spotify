# Measured classification throughput

Same cost_100.csv, unchanged compact-v2 model/prompt, empty result cache each trial, one review per request. Human golden answers were not used. All workers share the same SQLite spend reservations and per-second/per-minute rate guards.

|Workers|Seconds for 100|Reviews/min|Valid|Agreement with 1 worker|API USD|
|---|---|---|---|---|---|
|1|21.332|281.3|100|100%|0.004493454|
|2|10.359|579.2|100|98%|0.004493454|
|4|5.278|1136.8|100|97%|0.004493454|
|8|3.546|1692.2|100|98%|0.004493454|

Total benchmark API subtotal: $0.017973816. No failed calls or retries. Provider usage-based calculations, not reconciled account charges.

Selected 8 workers; 16+ unmeasured. TypeSafe console showed 80 requests/s and 100,000 input tokens/s. Official source: https://docs.typesafe.ai/models . Short tests are not sustained throughput guarantees. The eight-worker measured rate is approximately 28.2 reviews/s, below the account request ceiling. Conservative byte-based token reservations remain enforced.

Only classification was benchmarked. Verification still has its separate 30 RPM cap and runs serially; 1,000 verification calls alone would require at least about 33 minutes. Do not project the entire 10,000/full run from the classification rate alone. Current 10,000-review quality gate remains closed.

Runner now supports measured 1/2/4/8 workers with a bounded queue, separate SQLite connections, atomic writes and shared admission. Existing labels are not invalidated by changing concurrency. The earlier 500-review measurements and unresolved HTTP429 reservation remain preserved. Default calculator replay is still offline; this benchmark requires python3 -B cost/throughput.py --execute-paid.
