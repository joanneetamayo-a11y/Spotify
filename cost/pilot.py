#!/usr/bin/env python3
"""Explicit real cold/warm 100-review execution; replay remains the default."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.core import ROOT,connect
from pipeline.runner import run
from cost.calculator import main as replay
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-paid',action='store_true');p.add_argument('--budget',type=float);p.add_argument('--config',type=Path,default=ROOT/'config.jev-pilot.json');p.add_argument('--db',type=Path,default=ROOT/'data/pilot.sqlite');a=p.parse_args()
    if not a.execute_paid:
        sys.argv=[sys.argv[0]];replay()
    else:
        if a.budget is None or a.budget<=0:p.error('Explicit positive --budget required')
        cfg=json.loads(a.config.read_text());cfg['budget_usd']=a.budget
        db=connect(a.db)
        import fcntl
        with open(str(a.db)+'.worker.lock','w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
            cold=run(db,cfg,ROOT/'supplied/cost_100.csv','cold')
            warm=run(db,cfg,ROOT/'supplied/cost_100.csv','warm')
            assert warm['enrichment_calls']==0, 'Warm-run enrichment cache failure'
        sys.argv=[sys.argv[0]];replay()
