"""One-off explicitly paid adjudication of three exhausted development records."""
import sys,json,uuid,fcntl
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.core import *
from pipeline.runner import Provider
from pipeline.env import load_local_env
if '--execute-paid' not in sys.argv:raise SystemExit('Requires --execute-paid; no calls made')
cfg=json.loads((ROOT/'config.jev-compact.json').read_text());cfg['budget_usd']=.05
ids=['fe5dadcb-e99c-4675-b8c8-6c2bacb338d7','6a2cd434-9ad2-4e66-8968-ad066659d4df','e09a9cf4-7ab2-49fb-b3f9-543ab70d6aec']
parent=config_id(cfg);child=digest([parent,'bounded-luna-adjudication-v1',cfg['verify_model'],'none',ids])
load_local_env(ROOT/'.env');path=Path('/private/tmp/spotify-evaluation/compact-v2.sqlite');db=connect(path)
with open(str(path)+'.worker.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for call in db.execute('SELECT id,event FROM calls WHERE actual IS NULL'):
  e=json.loads(call['event'] or '{}')
  if call['id'] not in cfg.get('reviewed_http429_resume_ids',[]) or e.get('http_status')!=429:raise RuntimeError('Unreviewed uncertain charge')
 provider=Provider(db,cfg,'adjudication-'+str(uuid.uuid4()),'resume');out=[]
 instruction=(ROOT/'pipeline/rubric.txt').read_text()+' Resolve ambiguous text conservatively. All fields must be mutually consistent. Do not infer functional harm from a feature name or emoji. Mark needs_review when meaning remains uncertain.'
 save_json(ROOT/'evals/checkpoint-500/adjudication-policy.json',{'ids':ids,'maximum_records':3,'fraction_of_checkpoint':.006,'parent_config':parent,'child_config':child,'model':cfg['verify_model'],'effort':'none','prompt':instruction,'budget_usd':.05,'scope':'one-off development correction; general stronger fallback remains disabled'})
 for rid in ids:
  row=db.execute('SELECT * FROM sources WHERE id=?',(rid,)).fetchone()
  saved=db.execute('SELECT body FROM labels WHERE id=? AND config=?',(rid,child)).fetchone()
  if saved:result={'review_id':rid,**json.loads(saved[0])}
  else:
   result=provider.call('enrich',cfg['verify_model'],'none',instruction,[{'review_id':rid,'review_text':row['text']}],[rid],child,lambda x:validate(x.get('records'),[row]))[0]
   persist_labels(db,child,[row],[result])
  with db:db.execute('INSERT OR REPLACE INTO adjudications VALUES(?,?,?,?)',(parent,rid,child,'Explicit bounded adjudication after exhausted cross-field validation'))
  out.append(result);save_json(ROOT/'evals/checkpoint-500/adjudications.json',out)
 print('Adjudicated',len(out),'records; original failed calls preserved')
