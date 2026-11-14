# Cost and runtime calculator

Status: **measured_with_recovery**.

Real provider runs are required for measured cost and runtime. Missing measurements remain unavailable, never zero. Local compute and hosting cost are unknown. Default replay does not access the network.

User ceiling: $10 per 100,000 input reviews. No scaling without a completed checkpoint and quality review.

## Saved measurements

| Run | Rows | Completed | Failed | Seconds | API USD |
|---|---:|---:|---:|---:|---:|
| resume | 10000 | 9877 | 123 | 4654.962 | 0.34291822 |
| resume | 660622 | 157489 | 503120 | 17016.452 | None |
| resume | 10000 | 2757 | 7243 | 745.040 | None |
| resume | 660622 | 185381 | 475228 | 1510.395 | None |
| resume | 660622 | 213574 | 447035 | 3645.905 | None |
| resume | 660622 | 192404 | 468205 | 1210.822 | None |
| resume | 660622 | 198436 | 462173 | 1350.649 | None |
| resume | 500 | 162 | 338 | 133.724 | 0.00766552 |
| resume | 500 | 500 | 0 | 11.549 | 0.0008522 |
| resume | 500 | 427 | 73 | 185.478 | 0.0139342 |
| resume | 660622 | 220546 | 440063 | 1373.373 | None |
| warm | 100 | 100 | 0 | 0.044 | 0.0 |
| cold | 100 | 100 | 0 | 78.464 | 0.00539426 |
| resume | 10000 | 10000 | 0 | 15.370 | 0.000941 |

## Full-run scenarios

| Scenario | Reuse | API USD (estimate) | Hours (estimate) | Over budget |
|---|---|---:|---:|---|
| base | True | None | 97.24 | None |
| base | False | None | 124.65 | None |
| conservative | True | None | 253.19 | None |
| conservative | False | None | 313.48 | None |

Recovered cold execution is displayed as separate measured legs; intervention time is excluded. Unknown rejected-attempt charges keep the complete cost unresolved. Scenario known-usage estimates are partial, not confirmed totals. Target counts and editable assumptions remain in `scenarios.json`. See `report.json` for all formulas and uncertainty.

Formula: uncached input = total input − cache reads − separately reported cache writes. Sum each mutually exclusive billed unit × dated rate; output already includes reasoning tokens. Repricing changes costs, never measured time. Enrich scales by distinct texts (or nonempty rows without reuse), verification by its sample count, group/memo once, local preparation/aggregation by rows. Conservative retries, fallback and throughput are assumptions, not observations.

Runtime projections sum request durations as serial-equivalent capacity estimates, not concurrent elapsed-time predictions. Adjudication is included at the observed rate or the configured higher rate. No unmeasured concurrency speedup is claimed. Conservative fallback is a what-if; the executable runner caps stronger fallbacks at zero until measured benefit is established.
