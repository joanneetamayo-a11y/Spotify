# Cost and runtime calculator

Status: **blocked_no_completed_real_cold_pilot**.

Real provider runs are required for measured cost and runtime. Missing measurements remain unavailable, never zero. Local compute and hosting cost are unknown. Default replay does not access the network.

User ceiling: $10 per 100,000 input reviews. No scaling without a completed checkpoint and quality review.

## Saved measurements

| Run | Rows | Completed | Failed | Seconds | API USD |
|---|---:|---:|---:|---:|---:|
| cold | 100 | 99 | 1 | 52.287 | 0.010002204 |
| warm | 100 | 99 | 1 | 4.231 | 0.0 |

## Full-run scenarios

| Scenario | Reuse | API USD (estimate) | Hours (estimate) | Over budget |
|---|---|---:|---:|---|

Recovered cold execution is displayed as separate measured legs; intervention time is excluded. Unknown rejected-attempt charges keep the complete cost unresolved. Scenario known-usage estimates are partial, not confirmed totals. Target counts and editable assumptions remain in `scenarios.json`. See `report.json` for all formulas and uncertainty.

Formula: uncached input = total input − cache reads − separately reported cache writes. Sum each mutually exclusive billed unit × dated rate; output already includes reasoning tokens. Repricing changes costs, never measured time. Enrich scales by distinct texts (or nonempty rows without reuse), verification by its sample count, group/memo once, local preparation/aggregation by rows. Conservative retries, fallback and throughput are assumptions, not observations.

Runtime projections sum request durations as serial-equivalent capacity estimates, not concurrent elapsed-time predictions. Adjudication is included at the observed rate or the configured higher rate. No unmeasured concurrency speedup is claimed. Conservative fallback is a what-if; the executable runner caps stronger fallbacks at zero until measured benefit is established.
