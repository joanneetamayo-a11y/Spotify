"""Offline summary by default. Paid execution requires --execute-paid."""
import argparse,json,sys,time,fcntl,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from pipeline.core import connect,config_id,digest,canonical,save_json,atomic,validate,sha
from pipeline.runner import Provider,UncertainCharge
from pipeline.env import load_local_env
OUT=Path(__file__).parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--execute-paid',action='store_true');p.add_argument('--db',default='/private/tmp/spotify-evaluation/compact-v2.sqlite');a=p.parse_args()
 if not a.execute_paid:
  print((OUT/'summary.json').read_text() if (OUT/'summary.json').exists() else 'Not executed. Use --execute-paid for the authorized $0.25 maximum retest.');return
 db=connect(a.db)
 with open(a.db+'.worker.lock','w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  inputs=json.loads((OUT/'inputs.json').read_text());assert all(set(r)=={'review_id','review_text'} for r in inputs)
  cfg=json.loads((ROOT/'config.jev-compact.json').read_text());cfg.update(workers=1,max_attempts=2)
  manifest_path=OUT/'manifest.json'
  if manifest_path.exists():manifest=json.loads(manifest_path.read_text())
  else:
   baseline=db.execute('SELECT coalesce(sum(coalesce(actual,reserved)),0) FROM calls').fetchone()[0]
   manifest=dict(initial_ledger_usd=baseline,new_spend_cap_usd=.25,cumulative_limit_usd=baseline+.25,previous_unresolved_ids=[r[0] for r in db.execute('SELECT id FROM calls WHERE actual IS NULL')],input_sha256=sha(OUT/'inputs.json'),code_sha256=sha(ROOT/'pipeline/jev.py'),started_at=time.time())
   save_json(manifest_path,manifest)
  assert manifest['input_sha256']==sha(OUT/'inputs.json') and manifest['code_sha256']==sha(ROOT/'pipeline/jev.py'),'Frozen retest changed'
  unknown={r[0] for r in db.execute('SELECT id FROM calls WHERE actual IS NULL')}
  if unknown-set(manifest['previous_unresolved_ids']):raise UncertainCharge('New unresolved call: no automatic retry')
  cfg['budget_usd']=manifest['cumulative_limit_usd'];load_local_env(ROOT/'.env');results=[];error=None;started=time.perf_counter()
  try:
   for arm in ('baseline','candidate'):
    settings=dict(cfg)
    if arm=='candidate':settings.update(jev_prompt_style='guarded-v3',prompt_version='spotify-jev-guarded-v3')
    cid=config_id(settings);provider=Provider(db,settings,'quality-retest-v1-'+arm)
    save_json(OUT/(arm+'-config.json'),settings)
    for item in inputs:
     key='quality-retest-v1:'+digest([arm,cid,item]);saved=db.execute('SELECT body FROM artifacts WHERE key=?',(key,)).fetchone();prediction=None;failure=None
     if saved:prediction=json.loads(saved[0])
     else:
      row={'id':item['review_id'],'text':item['review_text']}
      try:prediction=provider.call('enrich',settings['model'],settings['effort'],'',[item],[item['review_id']],cid,lambda x:validate(x.get('records'),[row]))[0]
      except ValueError as e:failure=str(e)
      if prediction:
       with db:db.execute('INSERT OR REPLACE INTO artifacts VALUES(?,?,?)',(key,'quality-retest',canonical(prediction)))
     results.append(dict(arm=arm,review_id=item['review_id'],prediction=prediction,error=failure))
     save_json(OUT/'predictions.json',results);print(arm,item['review_id'],'saved' if prediction else 'failed',flush=True)
  except Exception as e:error=type(e).__name__+': '+str(e)
  finally:
   events=[json.loads(r[0]) for r in db.execute("SELECT event FROM calls WHERE run_id IN ('quality-retest-v1-baseline','quality-retest-v1-candidate') ORDER BY started")]
   atomic(OUT/'calls.jsonl',''.join(canonical(e)+'\n' for e in events))
   spent=db.execute('SELECT sum(coalesce(actual,reserved)) FROM calls').fetchone()[0]
   save_json(OUT/'summary.json',dict(status='complete' if len(results)==2*len(inputs) and not error else 'stopped',predictions=len(results),error=error,seconds_this_invocation=time.perf_counter()-started,known_api_subtotal_usd=sum(e.get('api_usd') or 0 for e in events),unknown_calls=sum(e.get('api_usd') is None for e in events),new_ledger_spend_plus_reserved_usd=spent-manifest['initial_ledger_usd'],maximum_new_usd=.25,full_run_started=False))
  if error:raise RuntimeError(error)
if __name__=='__main__':main()
