"""Independent audit: recompute hashes, coverage, quote spans, cache references and ranking."""
import argparse,csv,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from .core import ROOT,save_json

def audit(source,folder):
    source_rows={}
    with open(source,newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            encoded=json.dumps([row[k] for k in ('review_id','review_text','review_rating','review_likes','app_version','review_timestamp')],ensure_ascii=False,separators=(',',':')).encode()
            source_rows[row['review_id']]=(hashlib.sha256(encoded).hexdigest(),row['review_text'])
    errors=Counter(); labels={}; status=Counter(); rank=defaultdict(lambda:[0,0])
    for line in (Path(folder)/'records.jsonl').read_text().splitlines():
        r=json.loads(line); rid=r['review_id'];status[r['status']]+=1
        if rid in labels:errors['duplicate_id']+=1
        labels[rid]=r
        if rid not in source_rows or r['source_sha256']!=source_rows[rid][0]:errors['source_hash']+=1;continue
        if r['status']=='pending':errors['unclassified']+=1
        if r['status']=='quarantined' and source_rows[rid][1].strip(): errors['nonempty_quarantine']+=1
        if r['status']=='completed':
            if not r['evidence_quote'] or r['evidence_quote'] not in source_rows[rid][1]:errors['quote']+=1
            if r['intent'] in ('complaint','cancellation'):
                rank[r['topic']][0]+=1;rank[r['topic']][1]+=r['severity']
    errors['missing_ids']=len(source_rows.keys()-labels.keys())
    for rid,r in labels.items():
        if r.get('cache_source_id'):
            original=labels.get(r['cache_source_id']); compare=('topic','intent','sentiment','severity','entities','evidence_quote','needs_review','label_config')
            if not original or original.get('cache_source_id') or source_rows[rid][1]!=source_rows[r['cache_source_id']][1] or any(r[k]!=original[k] for k in compare):errors['cache_provenance']+=1
    with (Path(folder)/'ranking.csv').open() as f: reported=list(csv.DictReader(f))
    expected=sorted(rank,key=lambda k:(-rank[k][1],k))
    if [r['issue_id'] for r in reported]!=expected:errors['ranking_order']+=1
    for r in reported:
        if [int(r['complaint_count']),int(r['priority_score'])]!=rank[r['issue_id']]:errors['ranking_value']+=1
    return dict(status='passed' if not any(errors.values()) else 'incomplete_or_failed',source_rows=len(source_rows),export_rows=len(labels),counts=dict(status),errors={k:v for k,v in errors.items() if v})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default=ROOT/'supplied/spotify_reviews_18months.csv');p.add_argument('--grading',default=ROOT/'grading');p.add_argument('--out',default=ROOT/'independent-check.json');a=p.parse_args();r=audit(a.input,a.grading);save_json(a.out,r);print(json.dumps(r))
