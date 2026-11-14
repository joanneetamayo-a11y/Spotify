# Cost and runtime calculator

Status: **measured_with_recovery**.

Real provider runs are required for measured cost and runtime. Missing measurements remain unavailable, never zero. Local compute and hosting cost are unknown. Default replay does not access the network.

User ceiling: $10 per 100,000 input reviews. No scaling without a completed checkpoint and quality review.

## Saved measurements

| Run | Rows | Completed | Failed | Seconds | API USD |
|---|---:|---:|---:|---:|---:|
| resume | 500 | 500 | 0 | 10.385 | 0.0007795 |
| resume | 10000 | 10000 | 0 | 917.216 | 0.05772336 |
| resume | 10000 | 3255 | 6745 | 272.842 | None |
| resume | 500 | 497 | 3 | 71.855 | 0.0035164 |
| resume | 500 | 497 | 3 | 724.600 | None |
| resume | 500 | 168 | 332 | 72.809 | 0.00242046 |
| warm | 100 | 100 | 0 | 0.009 | 0.0 |
| cold | 100 | 100 | 0 | 233.494 | 0.006795654 |
| resume | 10000 | 9845 | 155 | 961.145 | None |

## Full-run scenarios

| Scenario | Reuse | API USD (estimate) | Hours (estimate) | Over budget |
|---|---|---:|---:|---|
| base | True | None | 57.60 | None |
| base | False | None | 70.57 | None |
| conservative | True | None | 173.09 | None |
| conservative | False | None | 201.63 | None |

Recovered cold execution is displayed as separate measured legs; intervention time is excluded. Unknown rejected-attempt charges keep the complete cost unresolved. Scenario known-usage estimates are partial, not confirmed totals. Target counts and editable assumptions remain in `scenarios.json`. See `report.json` for all formulas and uncertainty.

Formula: uncached input = total input − cache reads − separately reported cache writes. Sum each mutually exclusive billed unit × dated rate; output already includes reasoning tokens. Repricing changes costs, never measured time. Enrich scales by distinct texts (or nonempty rows without reuse), verification by its sample count, group/memo once, local preparation/aggregation by rows. Conservative retries, fallback and throughput are assumptions, not observations.

Runtime projections sum request durations as serial-equivalent capacity estimates, not concurrent elapsed-time predictions. Adjudication is included at the observed rate or the configured higher rate. No unmeasured concurrency speedup is claimed. Conservative fallback is a what-if; the executable runner caps stronger fallbacks at zero until measured benefit is established.
