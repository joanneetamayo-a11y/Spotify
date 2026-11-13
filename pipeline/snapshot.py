"""Offline checkpoint snapshot; no API calls or credentials."""
import argparse, datetime, json
from .core import ROOT, connect, records, aggregate, save_json, canonical

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default=str(ROOT/'data/compact-v2.sqlite'))
    p.add_argument('--checkpoint',default=str(ROOT/'evals/checkpoint-10000'))
    a=p.parse_args(); checkpoint=__import__('pathlib').Path(a.checkpoint)
    meta=json.loads((checkpoint/'grading/run.json').read_text()); summary=json.loads((checkpoint/'summary.json').read_text())
    db=connect(a.db); checksum=meta['analysis_sha256']
    row=db.execute('SELECT config FROM runs WHERE checksum=? ORDER BY rowid DESC LIMIT 1',(checksum,)).fetchone()
    if not row: raise ValueError('No saved run for checkpoint')
    cfg=row[0]; recs=list(records(db,checksum,cfg)); agg,_=aggregate(db,checksum,cfg)
    profile=json.loads((ROOT/'grading/ingestion.json').read_text()); total=profile['counts']['records']; empty=profile['counts']['empty_review_text']
    completed=sum(r['status']=='completed' for r in recs)
    snapshot=dict(source_sha256='1fc85de68a304dd8978b537cfa58793d5f41cbaf417fa32cb53899f83a2fcef6',analysis_sha256=checksum,analysisCount=len(recs),total=total,nonempty=total-empty,quarantined=empty,distinct=484189,completed=completed,pending=total-empty-completed,months=profile['reviews_by_month'],ratings=profile['reviews_by_rating'],ranking=agg['ranking'],evidence=agg['evidence'],claims=agg['claims'],recommendations=json.loads((checkpoint/'memo.json').read_text())['recommendations'],pilotStatus='Real cold/warm 100, 500 and 10,000 completed',apiSpend=None,knownApiSubtotal=summary['known_checkpoint_api_subtotal_usd'],unknownCalls=summary['unknown_checkpoint_calls'],verificationAgreement=summary['verification_agreement'],verificationSample=summary['verification_sample'],qualityStatus='Development results: 74.8% verifier agreement; two adversarial failures; export review required. Full run not started.',updatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save_json(ROOT/'dashboard/lib/snapshot.json',snapshot)
    save_json(ROOT/'data/dashboard-snapshot.json',snapshot)
    # Server-only seed: all processed checkpoint records, including exact original source.
    processed=[]
    for r in recs:
        source=json.loads(db.execute('SELECT raw FROM sources WHERE id=?',(r['review_id'],)).fetchone()[0]); processed.append(dict(**r,source=source))
    save_json(ROOT/'dashboard/lib/processed-reviews.json',processed)
    with db: db.execute('INSERT OR REPLACE INTO artifacts VALUES(?,?,?)',('dashboard-snapshot','dashboard',canonical(snapshot)))
    print(canonical(dict(completed=completed,scope=len(recs),full_run=False)))
if __name__=='__main__':main()
