"""Explicit paid synthetic test of measured Luna configuration; no answers in inputs."""
import sys,json,fcntl,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pipeline.core import *
from pipeline.runner import Provider
from pipeline.env import load_local_env
if '--execute-paid' not in sys.argv:raise SystemExit('Offline default: paid test requires --execute-paid')
p=ROOT/'evals/quality-review/luna-synthetic';p.mkdir(exist_ok=True);cfg=json.loads((ROOT/'config.luna-batched-v2.json').read_text());cfg['budget_usd']=1;dbpath='/private/tmp/spotify-evaluation/compact-v2.sqlite';db=connect(dbpath);cid=config_id(cfg);inputs=json.loads((ROOT/'evals/quality-review/retest-v5/inputs.json').read_text());results=[];started=time.perf_counter()
with open(dbpath+'.worker.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);load_local_env(ROOT/'.env');provider=Provider(db,cfg,'luna-batched-v2-synthetic')
 try:
  for i in range(0,len(inputs),10):
   batch=inputs[i:i+10];key=digest(['luna-synthetic-v1',cid,batch]);saved=db.execute('SELECT body FROM artifacts WHERE key=?',(key,)).fetchone()
   if saved:result=json.loads(saved[0])
   else:
    rows=[{'id':x['review_id'],'text':x['review_text']} for x in batch];result=provider.call('enrich',cfg['model'],cfg['effort'],(ROOT/'pipeline/rubric.txt').read_text(),batch,[r['id'] for r in rows],cid,lambda x:validate(x.get('records'),rows))
    with db:db.execute('INSERT INTO artifacts VALUES(?,?,?)',(key,'synthetic',canonical(result)))
   results.extend(result);save_json(p/'predictions.json',results)
 finally:
  events=[json.loads(r[0]) for r in db.execute("SELECT event FROM calls WHERE run_id='luna-batched-v2-synthetic' ORDER BY started")];atomic(p/'calls.jsonl',''.join(canonical(e)+'\n' for e in events));save_json(p/'summary.json',dict(completed=len(results),known_api_usd=sum(e.get('api_usd') or 0 for e in events),unknown_calls=sum(e.get('api_usd') is None for e in events),seconds=time.perf_counter()-started))
