# Cost and runtime calculator

Status: **measured_with_recovery**.

Real provider runs are required for measured cost and runtime. Missing measurements remain unavailable, never zero. Local compute and hosting cost are unknown. Default replay does not access the network.

User ceiling: $10 per 100,000 input reviews. No scaling without a completed checkpoint and quality review.

## Saved measurements

| Run | Rows | Completed | Failed | Seconds | API USD |
|---|---:|---:|---:|---:|---:|
| warm | 100 | 100 | 0 | 0.030 | 0.0 |
| resume | 100 | 100 | 0 | 5.995 | 0.0004665 |
| cold | 100 | 100 | 0 | 279.875 | None |
| warm | 100 | 100 | 0 | 0.015 | 0.0 |
| resume | 100 | 100 | 0 | 64.843 | 0.00352988 |

## Full-run scenarios

| Scenario | Reuse | API USD (estimate) | Hours (estimate) | Over budget |
|---|---|---:|---:|---|
| base | True | None | 446.18 | None |
| base | False | None | 585.65 | None |
| conservative | True | None | 1115.51 | None |
| conservative | False | None | 1422.35 | None |

Recovered cold execution is displayed as separate measured legs; intervention time is excluded. Unknown rejected-attempt charges keep the complete cost unresolved. Scenario known-usage estimates are partial, not confirmed totals. Target counts and editable assumptions remain in `scenarios.json`. See `report.json` for all formulas and uncertainty.

Formula: uncached input = total input − cache reads − separately reported cache writes. Sum each mutually exclusive billed unit × dated rate; output already includes reasoning tokens. Repricing changes costs, never measured time. Enrich scales by distinct texts (or nonempty rows without reuse), verification by its sample count, group/memo once, local preparation/aggregation by rows. Conservative retries, fallback and throughput are assumptions, not observations.

Throughput projections use one worker. No unmeasured concurrency speedup is claimed. Conservative fallback is a what-if; the executable runner caps stronger fallbacks at zero until measured benefit is established.
