"""Explicit, capped single-review repairs; original failed attempts stay intact."""
import sys,json,time,uuid,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pipeline.core import *
from pipeline.runner import Provider,run
from pipeline.adjudication import restore
from pipeline.env import load_local_env
if '--execute-paid' not in sys.argv:raise SystemExit('Requires --execute-paid; no API calls made')
folder=ROOT/'evals/checkpoint-10000-luna';folder.mkdir(exist_ok=True)
dbpath='/private/tmp/spotify-evaluation/compact-v2.sqlite'
with open(dbpath+'.worker.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 db=connect(dbpath);cfg=json.loads((ROOT/'config.luna-batched-v2.json').read_text());cid=config_id(cfg)
 prep=ingest(db,ROOT/'supplied/analysis_10000.csv');rows=scoped(db,prep['checksum']);reuse(db,cid,rows)
 missing=[r for r in rows if not db.execute('SELECT 1 FROM labels WHERE config=? AND id=?',(cid,r['id'])).fetchone()]
 policy=folder/'repair-policy.json'
 if policy.exists():p=json.loads(policy.read_text())
 else:
  spent=db.execute('SELECT coalesce(sum(coalesce(actual,reserved)),0) FROM calls').fetchone()[0]
  p={'run_id':'luna-repair-10k-'+str(uuid.uuid4()),'initial_ids':[r['id'] for r in missing],'shared_cap':min(2,spent+.25),'max_attempts_per_review':2,'model':cfg['model'],'effort':'none','reason':'Missing records or severity/intent schema inconsistency; no golden answers in inputs'};save_json(policy,p)
 cfg['budget_usd']=p['shared_cap'];load_local_env(ROOT/'.env');provider=Provider(db,cfg,p['run_id'],phase='bounded-repair');failed=[]
 for r in missing:
  if r['id'] not in p['initial_ids']:raise RuntimeError('Repair scope expanded')
  previous=db.execute("SELECT count(*) FROM calls,json_each(calls.event,'$.review_ids') j WHERE run_id=? AND j.value=?",(p['run_id'],r['id'])).fetchone()[0]
  if previous>=2:failed.append(r['id']);continue
  cfg['max_attempts']=2-previous
  instructions=(ROOT/'pipeline/rubric.txt').read_text()+' Return exactly ONE record with review_id R1. Intent praise/request/unclear MUST have severity 1. Code restores original ID and exact source quote.'
  try:
   result=provider.call('adjudicate',cfg['model'],'none',instructions,[{'review_id':'R1','review_text':r['text']}],[r['id']],cid,lambda output:restore(output,[r]))
   persist_labels(db,cid,[r],result)
  except ValueError:failed.append(r['id'])
  print(json.dumps({'repair_saved':db.execute("SELECT count(*) FROM calls WHERE run_id=? AND state='succeeded'",(p['run_id'],)).fetchone()[0],'failed':len(failed)}),flush=True)
 reuse(db,cid,rows)
 save_json(folder/'repair-result.json',{'run_id':p['run_id'],'failed_ids':failed,'remaining':sum(not db.execute('SELECT 1 FROM labels WHERE config=? AND id=?',(cid,r['id'])).fetchone() for r in rows)})
 cfg=json.loads((ROOT/'config.luna-batched-v2.json').read_text());cfg['budget_usd']=2
 result=run(db,cfg,ROOT/'supplied/analysis_10000.csv','resume',None)
 print(json.dumps({k:result.get(k) for k in ['run_id','completed','failed','verification_agreement']}),flush=True)
