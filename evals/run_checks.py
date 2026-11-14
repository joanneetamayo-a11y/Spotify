"""Explicit paid, resumable evaluation; human answer files are never opened here."""
import argparse,json,sys,time,uuid,fcntl
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.core import *
from pipeline.runner import Provider,UncertainCharge
from pipeline.env import load_local_env

def main():
 p=argparse.ArgumentParser();p.add_argument('--execute-paid',action='store_true');p.add_argument('--budget',type=float);p.add_argument('--db',type=Path,default=ROOT/'data/compact-v2.sqlite');a=p.parse_args()
 if not a.execute_paid or a.budget is None or not 0<a.budget<=.05:p.error('Requires --execute-paid --budget, maximum $0.05 cumulative shared experiment budget')
 cfg=json.loads((ROOT/'config.jev-compact.json').read_text());cfg['budget_usd']=a.budget
 out=ROOT/'evals/frozen-compact-v2';out.mkdir(parents=True,exist_ok=True)
 frozen={'config':cfg,'label_config':config_id(cfg),'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'pipeline/jev.py',ROOT/'pipeline/rubric.txt']},'human_labels_in_inputs':False}
 fp=out/'frozen.json'
 if fp.exists() and json.loads(fp.read_text())!=frozen:raise ValueError('Frozen evaluation configuration changed')
 save_json(fp,frozen);load_local_env(ROOT/'.env')
 dbpath=a.db;db=connect(dbpath)
 with open(str(dbpath)+'.worker.lock','w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if db.execute('SELECT count(*) FROM calls WHERE actual IS NULL').fetchone()[0]:raise UncertainCharge('Unresolved spend: stop before dispatch')
  run_id='evaluation-'+str(uuid.uuid4());provider=Provider(db,cfg,run_id);cid=config_id(cfg);started=time.perf_counter();error=None
  prep=ingest(db,ROOT/'evals/blind/input.csv');rows=scoped(db,prep['checksum']);rubric=(ROOT/'pipeline/rubric.txt').read_text();before=len([r for r in records(db,prep['checksum'],cid) if r['status']=='completed'])
  save_json(out/'checkpoint_before.json',{'completed_ids':[r['review_id'] for r in records(db,prep['checksum'],cid) if r['status']=='completed']})
  try:
   exhausted=[]
   for row in rows:
    if db.execute('SELECT 1 FROM labels WHERE config=? AND id=?',(cid,row['id'])).fetchone():continue
    prior=db.execute("SELECT count(*) FROM calls WHERE run_id LIKE 'evaluation-%' AND state='failed' AND json_extract(event,'$.label_config')=? AND json_extract(event,'$.review_ids[0]')=?",(cid,row['id'])).fetchone()[0]
    if prior>=2:
     exhausted.append({'review_id':row['id'],'reason':'invalid_output_after_one_retry'});continue
    inp=[{'review_id':row['id'],'review_text':row['text']}]
    try:
     result=provider.call('enrich',cfg['model'],cfg['effort'],rubric,inp,[row['id']],cid,lambda x:validate(x.get('records'),[row]))
    except ValueError as e:
     exhausted.append({'review_id':row['id'],'reason':str(e)});continue
    persist_labels(db,cid,[row],result)
    atomic(out/'predictions.jsonl',''.join(canonical(r)+'\n' for r in records(db,prep['checksum'],cid)))
    print('Saved golden prediction',row['id'],flush=True)
   save_json(out/'unresolved-records.json',exhausted)
   tests=json.loads((ROOT/'tests/adversarial.json').read_text());outcomes=[]
   for i,t in enumerate(tests):
    rid='synthetic-adversarial-'+str(i+1);row={'id':rid,'text':t['review_text']};key='evaluation:'+cid+':'+digest(row)
    saved=db.execute('SELECT body FROM artifacts WHERE key=?',(key,)).fetchone()
    if saved:result=json.loads(saved[0])
    else:
     result=provider.call('enrich',cfg['model'],cfg['effort'],rubric,[{'review_id':rid,'review_text':row['text']}],[rid],cid,lambda x:validate(x.get('records'),[row]))[0]
     with db:db.execute('INSERT INTO artifacts VALUES(?,?,?)',(key,'synthetic-evaluation',canonical(result)))
    outcomes.append({'id':rid,'text':row['text'],'expected':t['expected'],'prediction':result,'passed':all(result[k]==v for k,v in t['expected'].items()),'synthetic':True})
    save_json(out/'adversarial.json',outcomes)
   # A wrong but schema-valid label is compared with a blind re-label, never shown to verifier.
   rid='synthetic-planted-error';row={'id':rid,'text':'I cannot log in at all.'};planted={'topic':'billing','intent':'complaint','severity':2}
   key='evaluation:'+cid+':planted-blind-v1';saved=db.execute('SELECT body FROM artifacts WHERE key=?',(key,)).fetchone()
   if saved:result=json.loads(saved[0])
   else:
    result=provider.call('verify',cfg['verify_model'],cfg['verify_effort'],rubric,[{'review_id':rid,'review_text':row['text']}],[rid],cid,lambda x:validate(x.get('records'),[row]))[0]
    with db:db.execute('INSERT INTO artifacts VALUES(?,?,?)',(key,'synthetic-evaluation',canonical(result)))
   save_json(out/'planted-error.json',{'synthetic':True,'text':row['text'],'planted':planted,'verifier':result,'detected':any(result[k]!=v for k,v in planted.items()),'expected':{'topic':'access','intent':'complaint','severity':4},'verifier_matches_expected':result['topic']=='access' and result['intent']=='complaint' and result['severity']==4,'first_prediction_shown_to_verifier':False})
  except Exception as e:error=type(e).__name__+': '+str(e)
  finally:
   preds=list(records(db,prep['checksum'],cid));atomic(out/'predictions.jsonl',''.join(canonical(r)+'\n' for r in preds))
   events=[json.loads(r[0]) for r in db.execute("SELECT event FROM calls WHERE run_id LIKE 'evaluation-%' AND event IS NOT NULL ORDER BY started")]
   atomic(out/'calls.jsonl',''.join(canonical(e)+'\n' for e in events))
   save_json(out/'checkpoint_after.json',{'completed_ids':[r['review_id'] for r in preds if r['status']=='completed']})
   summary={'run_id':run_id,'seconds':time.perf_counter()-started,'completed':sum(r['status']=='completed' for r in preds),'new_completed':sum(r['status']=='completed' for r in preds)-before,'error':error,'evaluation_api_subtotal_usd':sum(e['api_usd'] or 0 for e in events),'unresolved_calls':sum(e['api_usd'] is None for e in events),'cumulative_experiment_spent_plus_reserved':db.execute('SELECT sum(coalesce(actual,reserved)) FROM calls').fetchone()[0],'budget_usd':a.budget}
   save_json(out/'runs'/f'{run_id}.json',summary);print(canonical(summary),flush=True)
  if error:raise RuntimeError(error)
if __name__=='__main__':main()
