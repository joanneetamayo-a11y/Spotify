"""Offline scoring only. Expected answers never enter paid run.py."""
import json
from pathlib import Path
P=Path(__file__).parent
expected={r['review_id']:r for r in json.loads((P/'expected.json').read_text())}
pred=json.loads((P/'predictions.json').read_text());rows=[];counts={}
for r in pred:
 e=expected[r['review_id']];passed=bool(r['prediction'] and all(r['prediction'][k]==v for k,v in e['expected'].items()));rows.append(dict(**r,expected=e['expected'],group=e['group'],passed=passed));c=counts.setdefault(r['arm'],{}).setdefault(e['group'],dict(passed=0,total=0,missing=0));c['total']+=1;c['passed']+=passed;c['missing']+=r['prediction'] is None
report=dict(results=counts,rows=rows,limitation='Small synthetic diagnostic comparison, not human or representative corpus accuracy. Candidate was informed by known failures; fresh cases were authored before this run. Expected answers are separate from model inputs.',full_run_approved=False)
(P/'scored.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(counts))
