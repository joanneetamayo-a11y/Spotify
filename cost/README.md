# Offline calculator and explicit paid pilot

Run from the project root using Python 3.10+ (no packages required):

```sh
python3 cost/calculator.py
# Also defaults to replay, never paid:
python3 cost/pilot.py
```

Default replay now uses `cost/experiments/compact-v2/`; its `rates.csv` is editable and dated. Root cost files preserve the older experiment. Use `--folder cost` only to replay that historical experiment. Prices use USD per token; source links are official. `scenarios.json` separates modeled full-run assumptions from measured runs. `usage.csv` is regenerated from raw usage in call logs. `report.json` and `report.md` preserve unknowns when no pilot exists. No measurements have been fabricated.

Only the following commands can call the model. Save `OPENAI_API_KEY` and `TYPESAFE_API_KEY` in the local project-root `.env`. The paid runner loads them into environment variables without logging values; offline replay never loads them. Never paste a key into chat or a command argument. Budget is a cumulative cap on the shared database, including unresolved reservations.

```sh
python3 -B cost/pilot.py --execute-paid --budget 1 --config config.jev-pilot.json --db data/pilot.sqlite
```

This verifies the unchanged supplied pilot checksum, starts with an empty result cache, runs all stages, saves actual provider inputs/outputs/usage, then measures a warm run with zero enrichment calls. Failed cold runs can be resumed explicitly using the runner; they do not magically become a completed cold measurement. Use a clean, separately recorded experiment for a new cold comparison. Do not delete evidence to conceal failed calls.

Reprice without changing measured timing:

```sh
python3 cost/calculator.py --rate-multiplier 2
```

Estimates refresh from the largest successful measured checkpoint (100, then 500, then 10,000), while the recorded 100-review measurements remain fixed. Each scenario models enrichment, observed capped adjudication, verification, one group call, one memo call, retries, hypothetical fallbacks, and local work separately. All saved attempts are repriced, including runs outside the main run table. Unknown usage remains unavailable. Runtime is a serial-equivalent capacity estimate, not concurrent elapsed time. The conservative stronger-fallback scenario is a what-if; the current executable cap is zero. Maximum budget is editable but scaling must respect the user's $10-per-100,000 ceiling. A same-input cold-cache 1/2/4/8-worker comparison is saved in `cost/throughput/`. The recovered 10k checkpoint used four workers after timeouts.

Current compact-v2 pilot records and calls contain real saved results. Earlier root artifacts are retained for audit; use the compact-v2 report for the current checkpoint. Infrastructure and local-compute costs remain unknown. Account-dashboard reconciliation has not been performed.

## Current execution configuration

The real Jev + Luna pilot uses `config.jev-pilot.json` and the isolated `data/pilot.sqlite` result cache and spend ledger. Keep that same ledger when continuing checkpoint measurements; do not start parallel copies with independent spending caps. API access was verified on 2026-10-23. Consult the saved run and call files for completion, actual usage, and failures; the old pending placeholders do not supersede measured results.
