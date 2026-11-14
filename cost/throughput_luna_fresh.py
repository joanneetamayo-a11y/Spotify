"""Explicit paid concurrency benchmark; no saved production labels overwritten."""
import sys,json,time,uuid,csv,threading,fcntl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.core import *
from pipeline.runner import Provider
from pipeline.env import load_local_env

from pipeline.workers import bounded_map

def main():
 if '--execute-paid' not in sys.argv:raise SystemExit('Use --execute-paid for the benchmark. Saved report is cost/throughput/report.json.')
 cfg=json.loads((ROOT/'config.luna-batched-v2.json').read_text());cfg.update(budget_usd=66.06)
 cfg['model_limits']['jev-1.14.0']={'requests_per_second':80,'tokens_per_second':100000,'requests_per_minute':4800,'tokens_per_minute':6000000}
 path=Path('/private/tmp/spotify-evaluation/compact-v2.sqlite');out=ROOT/'cost/throughput-luna-fresh';out.mkdir(exist_ok=True)
 budget_db=connect(path); spent=budget_db.execute('SELECT coalesce(sum(coalesce(actual,reserved)),0) FROM calls').fetchone()[0]; budget_db.close(); cfg['budget_usd']=min(66.06,spent+.10)
 load_local_env(ROOT/'.env');rows=[{'id':r['review_id'],'text':r['review_text']} for r in csv.DictReader((ROOT/'supplied/cost_100.csv').open())];rubric=(ROOT/'pipeline/rubric.txt').read_text();summaries=[];baseline=None
 with open(str(path)+'.worker.lock','w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for workers in [4]:
   cfg['workers']=workers;run_id='throughput-'+str(uuid.uuid4());local=threading.local();connections=[];guard=threading.Lock();started=time.perf_counter();results=[];error=None
   def task(batch):
    if not hasattr(local,'db'):
     # Schema exists; one SQLite connection per worker, shared transactions/ledger.
     import sqlite3
     local.db=sqlite3.connect(path,timeout=60);local.db.row_factory=sqlite3.Row
    provider=Provider(local.db,cfg,run_id)
    try:
     result=provider.call('enrich',cfg['model'],cfg['effort'],rubric,[{'review_id':row['id'],'review_text':row['text']} for row in batch],[row['id'] for row in batch],digest(config_id(cfg)+run_id),lambda x:validate(x.get('records'),batch))
     return [{'id':r['review_id'],'prediction':r,'valid':True} for r in result]
    except ValueError as e:return [{'id':r['id'],'valid':False,'error':str(e)} for r in batch]
   try:
    for result in bounded_map(task,[rows[i:i+10] for i in range(0,len(rows),10)],workers):
     results.extend(result);atomic(out/f'workers-{workers}-predictions.jsonl',''.join(canonical(r)+'\n' for r in results))
   except Exception as e:error=type(e).__name__+': '+str(e)
   seconds=time.perf_counter()-started;db=connect(path);events=[json.loads(r[0]) for r in db.execute('select event from calls where run_id=?',(run_id,))]
   predictions={r['id']:r.get('prediction') for r in results}
   if baseline is None:baseline=predictions
   comparable=[rid for rid in baseline if baseline[rid] and predictions.get(rid)]
   agree=sum(all(baseline[rid][k]==predictions[rid][k] for k in ('topic','intent','severity')) for rid in comparable)
   report={'run_id':run_id,'workers':workers,'input_reviews':100,'completed':sum(r['valid'] for r in results),'seconds':seconds,'reviews_per_minute':len(results)*60/seconds,'attempts':len(events),'known_api_usd':sum(e.get('api_usd') or 0 for e in events),'unresolved_charges':sum(e.get('api_usd') is None for e in events),'agreement_with_one_worker':agree/len(comparable) if comparable else None,'comparable':len(comparable),'error':error,'cache':'empty result cache for each run; no result reuse','settings':cfg.copy()}
   summaries.append(report);save_json(out/'report.json',summaries);atomic(out/f'workers-{workers}-calls.jsonl',''.join(canonical(e)+'\n' for e in events));db.close();print(canonical(report),flush=True)
   if error:break
if __name__=='__main__':main()
