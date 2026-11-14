"""Explicit capped adjudication; source-only inputs and unchanged original evidence."""
import sys,json,uuid,fcntl
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.core import *
from pipeline.runner import Provider
from pipeline.env import load_local_env
if '--execute-paid' not in sys.argv:raise SystemExit('Requires --execute-paid')
cfg=json.loads((ROOT/'config.jev-compact.json').read_text());cfg.update(budget_usd=1.0,workers=1)
path=Path('/private/tmp/spotify-evaluation/compact-v2.sqlite');db=connect(path);parent=config_id(cfg);prep=ingest(db,ROOT/'supplied/analysis_10000.csv');out=ROOT/'evals/checkpoint-10000'
with open(str(path)+'.worker.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 approved=set(cfg.get('reviewed_http429_resume_ids',[])+cfg.get('reviewed_timeout_resume_ids',[])+cfg.get('reviewed_connection_reset_resume_ids',[]))
 if any(r[0] not in approved for r in db.execute('SELECT id FROM calls WHERE actual IS NULL')):raise RuntimeError('Unreviewed uncertain charge')
 policyfile=out/'adjudication-policy.json'
 if policyfile.exists():policy=json.loads(policyfile.read_text());ids=policy['ids']
 else:
  ids=[r['review_id'] for r in records(db,prep['checksum'],parent) if r['status']=='pending']
  if len(ids)>200:raise RuntimeError('Two-percent adjudication cap exceeded')
  policy={'ids':ids,'maximum_records':200,'actual_records':len(ids),'fraction':len(ids)/10000,'parent_config':parent,'model':cfg['verify_model'],'effort':'none','batch_size':10,'maximum_attempts':2,'budget_usd':1.0,'unknown_charges':'Reservations retained, not reconciled','scope':'Only these unresolved 10k development records; no general stronger-model fallback enabled'};save_json(policyfile,policy)
 child=digest([parent,'bounded-luna-10k-adjudication-v3-short-ids',ids]);load_local_env(ROOT/'.env');provider=Provider(db,cfg,'adjudication-10k-'+str(uuid.uuid4()),'resume')
 instruction=(ROOT/'pipeline/rubric.txt').read_text()+' Resolve ambiguous text conservatively. Keep fields mutually consistent. Mark needs_review when ambiguous. Never infer functional harm from emojis or a feature name alone.'
 remaining={r['review_id'] for r in records(db,prep['checksum'],parent) if r['status']=='pending'}
 allrows=[db.execute('SELECT * FROM sources WHERE id=?',(rid,)).fetchone() for rid in ids if rid in remaining]
 from pipeline.adjudication import restore as checked
 save_json(out/'adjudication-response-policy-v3.json',{'child_config':child,'remaining_ids':[r['id'] for r in allrows],'evidence_quote':'Deterministic full original source text replaces generated quote before validation; raw model output remains in call log','changes_to_labels':'None; only evidence extraction is deterministic'})
 reuse(db,child,allrows);seen=set();todo=[]
 for row in allrows:
  if row['text_hash'] in seen or db.execute('SELECT 1 FROM labels WHERE config=? AND id=?',(child,row['id'])).fetchone():continue
  seen.add(row['text_hash']);todo.append(row)
 for i in range(0,len(todo),10):
  batch=todo[i:i+10];result=provider.call('enrich',cfg['verify_model'],'none',instruction+' In output review_id use only the supplied response_id such as R1. Code restores original source IDs.',[{'review_id':r['id'],'response_id':'R'+str(j+1),'review_text':r['text']} for j,r in enumerate(batch)],[r['id'] for r in batch],child,lambda x:checked(x,batch));persist_labels(db,child,batch,result);reuse(db,child,allrows)
  with db:
   for row in allrows:
    if db.execute('SELECT 1 FROM labels WHERE config=? AND id=?',(child,row['id'])).fetchone():db.execute('INSERT OR REPLACE INTO adjudications VALUES(?,?,?,?)',(parent,row['id'],child,'Bounded adjudication after exhausted invalid-output attempts'))
  print('Saved adjudication batch',i//10+1,flush=True)
 save_json(out/'adjudication-result.json',{'child_config':child,'records':len(ids),'complete':sum(r['status']=='completed' for r in records(db,prep['checksum'],parent))})
