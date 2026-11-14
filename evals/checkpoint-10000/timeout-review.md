# Review of interrupted 10,000-review run

3,255 rows have valid saved classifications; 6,745 remain unresolved or unprocessed. The run is stopped. Database integrity check passed.

Eight calls timed out: six connection timeouts and two SSL-handshake timeouts. None returned HTTP429. This does not establish whether local connectivity, sleep, network routing or provider availability caused the incident. Timing out before a response also does not prove zero provider cost. The previous 100-review concurrency benchmark was too short to establish sustained reliability.

Known API cost for this run is $0.085141854. Eight unknown-charge reservations total $0.00131544 and remain in the shared ledger. Neither figure is a reconciled account bill.

Separately, 78 attempts failed intent/severity validation. 35 distinct reviews exhausted two invalid-output attempts; they must not receive a third unchanged attempt. Some further records had invalid output followed by a timeout. Original logs and retry history must be checked per ID on resume.

Recommended recovery: preserve uncertain reservations; use a separately documented bounded retry decision for these exact request IDs, never mark them free. Resume at four measured workers to test sustained reliability, dispatch only missing records, and stop again on uncertain outcomes. This is a conservative experiment, not proof that eight workers caused the failure. Keep the $1 cumulative cap. Resolve exhausted records through a capped, provenance-preserving adjudication path rather than relabeling completed IDs. Verification has not started.

No paid calls or resume were started during this review.
