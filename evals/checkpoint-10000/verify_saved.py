"""Independent offline verification of the checkpoint and supporting origins."""
import csv, hashlib, json
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
    folder=Path(__file__).resolve().parent
    source={r['review_id']:r for r in csv.DictReader((ROOT/'supplied/analysis_10000.csv').open(encoding='utf-8-sig'))}
    rows=[json.loads(x) for x in (folder/'grading/records.jsonl').read_text().splitlines()]
    assert Counter(r['review_id'] for r in rows)==Counter({k:1 for k in source})
    origins=json.loads((folder/'grading-support/cache-origins.json').read_text()); external={x['alias_id']:x for x in origins}
    by_id={r['review_id']:r for r in rows}; tally=defaultdict(lambda:[0,0]); fields=['topic','intent','severity','sentiment','entities','evidence_quote','needs_review']
    for r in rows:
        raw=source[r['review_id']]; values=[raw[k] for k in ('review_id','review_text','review_rating','review_likes','app_version','review_timestamp')]
        assert hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==r['source_sha256']
        assert r['evidence_quote'] and r['evidence_quote'] in raw['review_text']
        if r.get('cache_source_id'):
            if r['cache_source_id'] in by_id:
                original=by_id[r['cache_source_id']]; text=source[original['review_id']]['review_text']
            else:
                item=external[r['review_id']]; original=dict(item['classification'],label_config=item['label_config']);text=item['source']['review_text']
            assert not original.get('cache_source_id') and text==raw['review_text']
            assert original['label_config']==r['label_config']
            assert all(original[k]==r[k] for k in fields)
        if r['intent'] in ('complaint','cancellation'):
            tally[r['topic']][0]+=1;tally[r['topic']][1]+=r['severity']
    ranking=list(csv.DictReader((folder/'grading/ranking.csv').open()))
    expected=sorted(tally,key=lambda k:(-tally[k][1],k))
    for i,(issue,r) in enumerate(zip(expected,ranking),1):
        n,s=tally[issue];assert r==dict(rank=str(i),issue_id=issue,complaint_count=str(n),severity_sum=str(s),mean_severity=str((Decimal(s)/n).quantize(Decimal('.000001'),rounding=ROUND_HALF_UP)),priority_score=str(s))
    assert len(ranking)==len(expected)
    result=dict(status='passed',records=len(rows),external_origin_aliases=len(external),ranking_recomputed=True,scope='Saved-data structural verification only; does not certify semantic correctness, billing or full-corpus completion')
    (folder/'independent-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
