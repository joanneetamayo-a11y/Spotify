"""Offline scoring only. Expected labels never enter model requests."""
import argparse,csv,json,hashlib,collections
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--predictions',required=True);p.add_argument('--expected',default='evals/human/golden_50_human_labels.csv');p.add_argument('--out',default='evals/comparison.json');a=p.parse_args()
 human=list(csv.DictReader(open(a.expected,encoding='utf-8-sig',newline='')))
 predictions=[json.loads(line) for line in open(a.predictions) if line.strip()]
 ids=[r['review_id'] for r in predictions]; expected_ids={r['review_id'] for r in human}
 if len(set(ids))!=len(ids) or set(ids)-expected_ids:raise ValueError('Duplicate or foreign prediction IDs')
 by_id={r['review_id']:r for r in predictions}; cases=[]; confusion=collections.Counter()
 for h in human:
  r=by_id.get(h['review_id']);ok=bool(r and r.get('status')=='completed');c={'review_id':h['review_id'],'completed':ok,'expected':{k:h[k] for k in ('topic','intent','severity','sentiment','entities','evidence_quote','needs_review')},'prediction':r}
  for k in ('topic','intent'):c[k+'_agrees']=bool(ok and r.get(k)==h[k])
  c['severity_agrees']=bool(ok and r.get('severity')==int(h['severity']))
  c['severity_absolute_error']=abs(r['severity']-int(h['severity'])) if ok else None
  c['sentiment_absolute_error']=abs(r['sentiment']-float(h['sentiment'])) if ok else None
  c['quote_exact']=bool(ok and r.get('evidence_quote') and r['evidence_quote'] in h['review_text'])
  c['needs_review_agrees']=bool(ok and r.get('needs_review')==(h['needs_review']=='true'))
  confusion[(h['topic'],r.get('topic') if ok else 'MISSING')]+=1;cases.append(c)
 n=len(human);complete=sum(c['completed'] for c in cases)
 report={'expected_count':n,'completed':complete,'missing_or_incomplete':n-complete,'human_ambiguous_count':sum(h['needs_review']=='true' for h in human),'metrics':{k:sum(c[k] for c in cases)/n for k in ('topic_agrees','intent_agrees','severity_agrees','quote_exact','needs_review_agrees')},'topic_counts':dict(collections.Counter(h['topic'] for h in human)),'topic_confusion':[{'expected':x,'predicted':y,'count':v} for (x,y),v in sorted(confusion.items())],'cases':cases,'limitations':'50 diagnostic cases, not population accuracy. Missing predictions count as disagreements. MAE is over completed cases only. Entity support and quote meaning require human inspection; exact substring is not semantic validation. No label tuning from these results.'}
 for k in ('severity_absolute_error','sentiment_absolute_error'):report['metrics'][k+'_completed_only']=sum(c[k] for c in cases if c[k] is not None)/complete if complete else None
 report['expected_sha256']=hashlib.sha256(Path(a.expected).read_bytes()).hexdigest();report['predictions_sha256']=hashlib.sha256(Path(a.predictions).read_bytes()).hexdigest()
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(out)
 print(json.dumps({'completed':complete,'expected':n,'report':str(out)}))
if __name__=='__main__':main()
