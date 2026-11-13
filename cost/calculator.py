#!/usr/bin/env python3
"""Offline by default. Reprices saved usage; never imports/calls a network provider."""
import argparse, csv, json, sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.core import ROOT, save_json, save_csv, atomic

def price_call(event,rates):
    usage=event.get('raw_usage')
    if usage is None: return None,[]
    details=usage.get('input_tokens_details') or {}; cached=details.get('cached_tokens',0); writes=details.get('cache_creation_tokens',0)
    if usage.get('input_tokens') is None or usage.get('output_tokens') is None: return None,[]
    units={'input':usage['input_tokens']-cached-writes,'cached_input':cached,'cache_write':writes,'output':usage['output_tokens']}
    if min(units.values())<0: raise ValueError('Negative billed units')
    items=[]
    for item,n in units.items():
        rate=rates.get((event['model'],event.get('tier','default'),item))
        if rate is None: return None,items
        items.append({'request_id':event['request_id'],'run_id':event['run_id'],'role':event['role'],'model':event['model'],'item':item,'units':n,'unit':'token','price_per_unit':str(rate),'api_usd':str(Decimal(n)*rate)})
    return sum(Decimal(r['api_usd']) for r in items),items

def calculate(folder,scenarios,rate_multiplier=Decimal(1)):
    folder=Path(folder)
    with (folder/'rates.csv').open(newline='') as f: rates={(r['model'],r['tier'],r['item']):Decimal(r['price_per_unit'])*rate_multiplier for r in csv.DictReader(f)}
    call_path=folder/('all_calls.jsonl' if (folder/'all_calls.jsonl').exists() else 'pilot_calls.jsonl')
    events=[json.loads(x) for x in call_path.read_text().splitlines() if x.strip()] if call_path.exists() else []
    runs=[json.loads(p.read_text()) for p in sorted((folder/'runs').glob('*.json'))]
    # Every saved attempt is repriced, including adjudication runs outside the runner table.
    usage=[]; all_known=Decimal(0); all_unknown=0
    for event in events:
        amount,items=price_call(event,rates); usage.extend(items)
        if amount is None: all_unknown+=1
        else: all_known+=amount
    measures=[]
    for run in runs:
        calls=[e for e in events if e['run_id']==run['run_id']]; total=Decimal(0); unknown=0; stage=defaultdict(lambda:{'api_usd':0.,'seconds':0.,'attempts':0,'reviews':0,'unresolved':0})
        for e in calls:
            cost,items=price_call(e,rates); unknown+=cost is None
            if cost is not None: total+=cost
            s=stage[e['role']]; s['api_usd']+=float(cost or 0); s['seconds']+=e['seconds']; s['attempts']+=1; s['reviews']+=len(e['review_ids']); s['unresolved']+=cost is None
        m={k:run.get(k) for k in ('run_id','kind','checksum','rows','completed','failed','unique_texts','cache_hits_at_start','seconds','stage_seconds','error','verification_agreement','label_config')}
        m.update(api_usd=None if unknown else float(total),known_api_subtotal_usd=float(total),unresolved_attempts=unknown,attempts=len(calls),stages=dict(stage),throughput_rows_per_second=run['rows']/run['seconds'] if run['seconds'] else None,cost_per_1000_input_rows=None if unknown else float(total)*1000/run['rows'],cost_per_completed_record=None if unknown or not run['completed'] else float(total)/run['completed'])
        measures.append(m)
    pilot=[m for m in measures if m['rows']==100 and m['kind']=='cold']
    completed=[m for m in measures if m['rows'] in (100,500,10000) and m['kind']!='warm' and not m['error'] and m['completed']==m['rows']]
    projections=[]; recovery_basis=None
    if pilot and completed:
        import copy
        chosen=max(completed,key=lambda m:m['rows'])
        legs=[m for m in measures if m['rows']==chosen['rows'] and m['kind']!='warm' and m.get('label_config')==chosen.get('label_config') and m.get('checksum')==chosen.get('checksum')]
        cold=copy.deepcopy(chosen); cold['stages']={}; cold['stage_seconds']={}
        for leg in legs:
            for role,stage in leg['stages'].items():
                combined=cold['stages'].setdefault(role,{'api_usd':0.,'seconds':0.,'attempts':0,'reviews':0,'unresolved':0})
                for field in combined:
                    combined[field]+=max(stage[field],(leg.get('stage_seconds') or {}).get(role,0)) if field=='seconds' else stage[field]
            for role,seconds in (leg.get('stage_seconds') or {}).items():
                cold['stage_seconds'][role]=cold['stage_seconds'].get(role,0)+seconds
        # Work counts exclude retried IDs; their costs and durations remain included.
        leg_ids={leg['run_id'] for leg in legs}
        supplemental=[e for e in events if e['run_id'].startswith(('adjudication-10k-','luna-repair-10k-')) and chosen['rows']==10000 and e.get('label_config')==chosen.get('label_config')]
        for e in supplemental:
            amount,_=price_call(e,rates)
            stage=cold['stages'].setdefault('adjudication',{'api_usd':0.,'seconds':0.,'attempts':0,'reviews':0,'unresolved':0})
            stage['api_usd']+=float(amount or 0); stage['seconds']+=e['seconds']; stage['attempts']+=1; stage['unresolved']+=amount is None
        for role,stage in cold['stages'].items():
            if role=='adjudication':
                stage['reviews']=len({rid for e in supplemental for rid in e['review_ids']}); continue
            stage['reviews']=len({rid for event in events if event['run_id'] in leg_ids and event['role']==role for rid in event['review_ids']})
        recovery_basis={'run_ids':sorted(leg_ids),'measured_active_wall_seconds':sum(leg['seconds'] for leg in legs),'supplemental_adjudication_run_ids':sorted({e['run_id'] for e in supplemental}),'runtime_method':'Serial-equivalent sum of request durations; conservative capacity estimate, not measured concurrent wall time. Supplemental adjudication wall time unavailable.','intervention_time':'excluded and unmeasured; this is a recovered cold experiment, not one uninterrupted run','stages':cold['stages']}
        for name in ('base','conservative'):
            assumptions=scenarios[name]
            for reuse in (True,False):
                unique=scenarios['unique_nonempty_texts'] if reuse else scenarios['nonempty_rows']; est_cost=0.; est_seconds=0.; unresolved=False; detail={}
                for role,s in cold['stages'].items():
                    if role=='enrich': work=unique; factor=work/max(1,s['reviews'])
                    elif role=='adjudication': work=scenarios['nonempty_rows']*max(s['reviews']/chosen['rows'],assumptions.get('adjudication_fraction',0)); factor=work/max(1,s['reviews'])
                    elif role=='verify': work=scenarios['nonempty_rows']*assumptions['verification_fraction']; factor=work/max(1,s['reviews'])
                    else: work=1; factor=1 # grouping/memo fixed once, never multiplied per row
                    retry_multiplier=1+assumptions['retry_fraction']
                    cost=s['api_usd']*factor*retry_multiplier; seconds=s['seconds']*factor*retry_multiplier/assumptions['throughput_factor']
                    unresolved|=bool(s['unresolved']); est_cost+=cost; est_seconds+=seconds
                    detail[role]={'projected_work':work,'estimated_api_usd':cost,'estimated_seconds':seconds}
                enrich=cold['stages'].get('enrich'); fallback=assumptions['fallback_fraction']
                if enrich:
                    fc=enrich['api_usd']/max(1,enrich['reviews'])*unique*fallback*assumptions['fallback_cost_multiplier']*(1+assumptions['retry_fraction'])
                    ft=enrich['seconds']/max(1,enrich['reviews'])*unique*fallback*(1+assumptions['retry_fraction'])/assumptions['throughput_factor']
                    est_cost+=fc; est_seconds+=ft; detail['fallback']={'estimated_api_usd':fc,'estimated_seconds':ft,'status':'hypothetical only; production fallback cap is zero'}
                # Preparation is input work; aggregation input work; local fixed overhead added once.
                stage_times=cold.get('stage_seconds') or {}; local=sum(stage_times.get(k,0) for k in ('prepare','aggregate'))*scenarios['total_rows']/cold['rows']
                est_seconds+=local
                per100k=est_cost*100000/scenarios['total_rows']; hourly=scenarios.get('local_compute_usd_per_hour')
                projections.append({'scenario':name,'exact_text_reuse':reuse,'estimated_api_usd':None if unresolved else est_cost,'known_usage_based_api_estimate_usd':est_cost,'known_usage_based_usd_per_100000':per100k,'estimated_seconds':est_seconds,'estimated_usd_per_100000':None if unresolved else per100k,'over_budget':None if unresolved else est_cost>scenarios['budget_usd'],'exceeds_user_10_usd_per_100000_ceiling':None if unresolved else per100k>10,'local_compute_usd':None if hourly is None else est_seconds/3600*hourly,'stages':detail,'assumptions':assumptions})
    return {'all_saved_attempts':len(events),'all_saved_known_api_subtotal_usd':float(all_known),'all_saved_unknown_usage_attempts':all_unknown,'status':('measured_with_recovery' if any(m['error'] for m in measures) else 'measured') if pilot and completed else 'blocked_no_completed_real_cold_pilot','recovery_basis':recovery_basis,'measurements':measures,'projections':projections,'scenarios':scenarios,'local_compute':'unknown unless explicitly priced','infrastructure_cost':'unknown','account_usage_reconciliation':'not performed','user_ceiling_usd_per_100000':10},usage

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--folder',type=Path,default=ROOT/'cost/experiments/compact-v2'); p.add_argument('--scenarios',type=Path); p.add_argument('--rate-multiplier',type=Decimal,default=Decimal(1)); a=p.parse_args()
    scenario=json.loads((a.scenarios or a.folder/'scenarios.json').read_text()); report,usage=calculate(a.folder,scenario,a.rate_multiplier)
    save_json(a.folder/'report.json',report); save_csv(a.folder/'usage.csv',usage,['request_id','run_id','role','model','item','units','unit','price_per_unit','api_usd'])
    lines=['# Cost and runtime calculator','',f"Status: **{report['status']}**.",'','Real provider runs are required for measured cost and runtime. Missing measurements remain unavailable, never zero. Local compute and hosting cost are unknown. Default replay does not access the network.','', 'User ceiling: $10 per 100,000 input reviews. No scaling without a completed checkpoint and quality review.','', '## Saved measurements','', '| Run | Rows | Completed | Failed | Seconds | API USD |', '|---|---:|---:|---:|---:|---:|']
    for r in report['measurements']: lines.append(f"| {r['kind']} | {r['rows']} | {r['completed']} | {r['failed']} | {r['seconds']:.3f} | {r['api_usd']} |")
    if not report['measurements']: lines+=['','No model experiment has run. `pilot_calls.jsonl` and `usage.csv` have no call/usage rows.']
    lines+=['','## Full-run scenarios','','| Scenario | Reuse | API USD (estimate) | Hours (estimate) | Over budget |', '|---|---|---:|---:|---|']
    for r in report['projections']: lines.append(f"| {r['scenario']} | {r['exact_text_reuse']} | {r['estimated_api_usd']} | {r['estimated_seconds']/3600:.2f} | {r['over_budget']} |")
    lines+=['','Recovered cold execution is displayed as separate measured legs; intervention time is excluded. Unknown rejected-attempt charges keep the complete cost unresolved. Scenario known-usage estimates are partial, not confirmed totals. Target counts and editable assumptions remain in `scenarios.json`. See `report.json` for all formulas and uncertainty.','', 'Formula: uncached input = total input − cache reads − separately reported cache writes. Sum each mutually exclusive billed unit × dated rate; output already includes reasoning tokens. Repricing changes costs, never measured time. Enrich scales by distinct texts (or nonempty rows without reuse), verification by its sample count, group/memo once, local preparation/aggregation by rows. Conservative retries, fallback and throughput are assumptions, not observations.','', 'Runtime projections sum request durations as serial-equivalent capacity estimates, not concurrent elapsed-time predictions. Adjudication is included at the observed rate or the configured higher rate. No unmeasured concurrency speedup is claimed. Conservative fallback is a what-if; the executable runner caps stronger fallbacks at zero until measured benefit is established.']
    atomic(a.folder/'report.md','\n'.join(lines)+'\n'); print(json.dumps({'status':report['status'],'measured_runs':len(report['measurements']),'scenarios':len(report['projections'])}))
if __name__=='__main__':main()
