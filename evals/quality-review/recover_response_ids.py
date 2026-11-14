"""Offline revalidation of saved responses; retains original events and all charges."""
import sys,json,time,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pipeline.core import *
from pipeline.adjudication import restore
p=ROOT/'evals/checkpoint-500-luna';p.mkdir(exist_ok=True)
dbpath='/private/tmp/spotify-evaluation/compact-v2.sqlite';db=connect(dbpath);cfg=json.loads((ROOT/'config.luna-batched-v2.json').read_text());cid=config_id(cfg);recovered=[]
with open(dbpath+'.worker.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for call in list(db.execute("SELECT id,event FROM calls WHERE state='failed' AND json_extract(event,'$.label_config')=? AND json_extract(event,'$.error')='Unknown response reference' ORDER BY started",(cid,))):
  e=json.loads(call['event']);ids=e['review_ids'];rows=[dict(db.execute('SELECT * FROM sources WHERE id=?',(rid,)).fetchone()) for rid in ids]
  if all(db.execute('SELECT 1 FROM labels WHERE config=? AND id=?',(cid,rid)).fetchone() for rid in ids):continue
  sent=json.loads(e['request']['input'].split('\n',1)[1]);assert {x['review_id']:x['review_text'] for x in sent}=={r['id']:r['text'] for r in rows}
  text=''.join(part.get('text','') for output in e['response'].get('output',[]) for part in output.get('content',[]) if part.get('type')=='output_text')
  try:result=restore(json.loads(text),rows,accept_original_ids=True)
  except ValueError:continue
  original=dict(e);key='original-validation-failure:'+call['id']
  with db:db.execute('INSERT OR IGNORE INTO artifacts VALUES(?,?,?)',(key,'validation-audit',canonical(original)))
  persist_labels(db,cid,rows,result)
  e.update(outcome='succeeded',initial_outcome='failed',validation_recovery={'method':'Exact original IDs accepted alongside short references; full schema and source checks passed offline','at':time.time(),'original_event_artifact':key,'new_api_call':False})
  with db:db.execute('UPDATE calls SET state=?,event=? WHERE id=?',('succeeded',canonical(e),call['id']))
  recovered.append(dict(request_id=call['id'],review_ids=ids,original_event=original))
 save_json(p/'id-validation-recovery.json',dict(new_api_calls=0,recovered=recovered,records=sum(len(x['review_ids']) for x in recovered),note='Initial validation failure events retained verbatim. Existing request IDs and usage preserved; no new success call invented. Calls now reflect successful offline revalidation.'))
 print('Offline recovered records:',sum(len(x['review_ids']) for x in recovered))
