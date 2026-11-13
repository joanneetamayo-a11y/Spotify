> **Submitted scope (2026-10-26):** Partial dataset submission, accepted by the professor according to the student. 220,546 of 660,609 nonempty reviews are classified; 440,063 remain unclassified and 13 empty texts are quarantined. Further paid processing is stopped at the student’s request. This does not claim full-corpus completion or a clean pass against the original full-corpus grading contract. See SUBMISSION_STATUS.md for limitations.

# Spotify Review Observatory — Final Assignment

The submitted partial run contains **220,546 classified reviews**. All 660,622 source rows were ingested; 440,063 nonempty texts remain unfinished and 13 empty texts are quarantined. Paid processing is stopped. The historical checkpoint findings below describe 10,000 reviews, not all submitted classifications.

## Results and limitations

- 10,000 saved classifications; blind verification agreed on 748 of 1,000 reviews (74.8%). This is model agreement, not human accuracy.
- 155 difficult records needed capped Luna adjudication. Original failed attempts and configuration provenance remain saved.
- Usability ranks first by severity sum: 1,302 complaint/cancellation reviews, score 3,267. Playback has 626 such reviews, score 2,088. These are sample findings, not full-corpus estimates.
- Historical compact-v2 semantic adversarial results were 5/7. Subsequent guarded-v5 and batched Luna tests each passed 31/31 synthetic cases; these do not establish corpus accuracy. The user authorized the full run after required checkpoint measurements. The assistant-added 85% agreement cutoff was removed because the assignment specifies no minimum; actual agreement remains reported.
- The supplied checker still reports review required: 87 cache aliases have direct originals outside this sample, some failed calls have unavailable usage, and a valid interruption/resume recording remains outstanding. Supporting cache originals are preserved separately, never substituted or fabricated.

See [checkpoint evidence](evals/checkpoint-10000/README.md), [checker report](evals/checkpoint-10000/self-check.json), [cache origins](evals/checkpoint-10000/grading-support/cache-origins.json), and [human evaluation](evals/frozen-compact-v2/review.md). Human golden answers are never model inputs. Original human judgments are retained.

## Costs and offline replay

The user ceiling is **$10 per 100,000 input reviews**, including retries, verification and recommendations. This is a ceiling, not permission to automatically launch the full run.

Known 10,000-checkpoint API subtotal: $0.439282466, with nine calls whose charges remain unknown. The shared experiment ledger last measured $0.500230117 including reservations. These are not reconciled provider bills. Infrastructure and local-compute costs are unmeasured.

The default calculator uses the measured compact-v2 experiment. It includes saved adjudication usage and reprices every saved attempt. It requires no credentials and makes no network calls:

```sh
python3 -B cost/calculator.py
python3 -B -m unittest discover -s tests -v
```

Editable dated rates, cold/warm 100-review evidence, and updated full-run scenarios are in [cost/experiments/compact-v2](cost/experiments/compact-v2/). Known-usage estimates with exact reuse are about $27.79 base and $39.77 conservative for the full corpus. Unknown charges keep complete totals unresolved. Runtime scenarios are serial-equivalent capacity estimates, not promises of concurrent elapsed time; recovered run intervention time is unmeasured. Separate adjudication request durations are included. Parallelism measurements are in [cost/throughput](cost/throughput/).

Preparation and exact-text deduplication precede classification. Python/SQLite handles deterministic work; Jev classifies, Luna blindly verifies and writes recommendations after aggregation. The 1/2/4/8-worker benchmark measured throughput, but the recovered 10k run used four workers after timeouts. Shared spend/rate reservations and bounded queues apply across workers. No request exceeds 50 reviews; Jev requests use one, verification batches use ten. Stronger-model automatic fallback remains disabled; the small-model adjudication route was separately capped.

## Dashboard and backend

[Open the private Spotify Review Observatory](https://spotify-review-evidence-joanne.joanne-e-tamayo.chatgpt.site).

Sign in using the ChatGPT account that owns the Site. Access remains private; graders need explicitly granted access before submission. The published checkpoint update displays checkpoint rankings, grounded recommendations, exact evidence, verification limitations and full-source coverage. Publication succeeded on October 24, 2026; the exact version and commit are recorded in `deployment.json`. The 10,000-record import and backend were verified locally. The hosted database import also completed: production logs confirm the final chunk and subsequent metrics read returned HTTP 200. Sign in as the owner to view it.

The backend serves `/api/metrics`, `/api/evidence?issue=playback`, and the updated backend adds `/api/reviews?offset=0`, with 100 processed records per page. “Load latest snapshot” imports the checked checkpoint in bounded chunks into Cloudflare D1. The final chunk publishes the snapshot only after every chunk is present. Source fields, IDs, source hashes and cache references are preserved. The local SQLite database remains the comprehensive execution ledger. No credentials are shipped in the browser or data seed.

Regenerate the checkpoint snapshot offline:

```sh
python3 -B -m pipeline.snapshot --db data/compact-v2.sqlite
```

Rebuild and publish through the Sites workflow to update the live version. Rankings cover only the checkpoint; full-source rating/month charts are descriptive metadata. No revenue, churn or causal effects are inferred.

## Credentials and paid execution

Keep only the keys used in a local `.env`: `OPENAI_API_KEY` and `TYPESAFE_API_KEY`. The blank `.env.example` also lists `ANTHROPIC_API_KEY`. Never submit `.env`. The paid runner loads environment variables through its dotenv loader. Offline replay needs no keys.

Paid execution requires an explicit `execute-paid` command or `--execute-paid` flag. Do not rerun the completed experiments or launch the full corpus merely to regenerate reports. A full-run budget must be selected after quality review and provider-balance checks; an offline replay never authorizes spending.

Before pushing, verify `.env` is ignored and only the blank example is tracked:

```sh
git check-ignore .env
git ls-files -- .env '.env.*'
```

The root project is not yet a published submission repository. Do not claim those Git checks passed until a root repository exists and its staged contents have been inspected.

## Submission status

The root `grading/` remains the incomplete full-corpus export. The checkpoint export is separate at `evals/checkpoint-10000/grading/`. Do not present the checkpoint as full coverage. The checker is read-only and makes no API calls:

```sh
python3 -B supplied/check_submission.py check --reference local-reference.json --submission grading --out self-check.json
```

Remaining work: finish remeasurement of the selected classifier before full scaling; reconcile unavailable usage; demonstrate and record actual interruption/resume; complete all required nonempty classifications; export and independently check full coverage, deterministic rankings and cited memo; finish hosted-data verification and grading access; publish a secret-free submission repository/artifact.
