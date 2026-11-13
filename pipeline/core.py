"""Standard-library storage, validation, and deterministic aggregation. No network."""
import csv, hashlib, json, math, os, sqlite3, tempfile, time
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from supplied.check_submission import row_sha, sha, FIELDS
ROOT = Path(__file__).resolve().parents[1]
TOPICS = ('access','usability','playback','downloads','catalog','billing','support','other')
INTENTS = ('cancellation','complaint','request','praise','unclear')
def canonical(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',',':'), allow_nan=False)
def digest(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def atomic(path, content):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as f:
            f.write(content); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def save_json(path,obj): atomic(path,json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save_csv(path,rows,fields):
    import io
    f=io.StringIO(newline=''); w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader(); w.writerows(rows); atomic(path,f.getvalue())
def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=60); db.row_factory=sqlite3.Row
    db.execute('PRAGMA cache_size=-131072'); db.execute('PRAGMA cache_size=-131072'); db.execute('PRAGMA journal_mode=WAL'); db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, text TEXT NOT NULL, text_hash TEXT NOT NULL, source_hash TEXT NOT NULL, raw TEXT NOT NULL, status TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS text_lookup ON sources(text_hash);
    CREATE TABLE IF NOT EXISTS inputs(checksum TEXT PRIMARY KEY,path TEXT NOT NULL,rows INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS scope(checksum TEXT, id TEXT REFERENCES sources(id), ordinal INTEGER,PRIMARY KEY(checksum,id));
    CREATE TABLE IF NOT EXISTS labels(config TEXT,id TEXT REFERENCES sources(id),body TEXT NOT NULL,cache_source_id TEXT,PRIMARY KEY(config,id));
    CREATE TABLE IF NOT EXISTS cache(config TEXT,text_hash TEXT,text TEXT,source_id TEXT,body TEXT,PRIMARY KEY(config,text_hash));
    CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY,run_id TEXT,role TEXT,state TEXT,started REAL,reserved REAL,actual REAL,tokens INTEGER,event TEXT);
    CREATE INDEX IF NOT EXISTS calls_started ON calls(started);
    CREATE INDEX IF NOT EXISTS calls_unresolved ON calls(id) WHERE actual IS NULL;
    CREATE INDEX IF NOT EXISTS calls_failed_role ON calls(role,state) WHERE state='failed';
    CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,checksum TEXT,config TEXT,kind TEXT,state TEXT,body TEXT);
    CREATE TABLE IF NOT EXISTS artifacts(key TEXT PRIMARY KEY,kind TEXT,body TEXT);
    CREATE TABLE IF NOT EXISTS verification(config TEXT,id TEXT,body TEXT,PRIMARY KEY(config,id));
    CREATE TABLE IF NOT EXISTS adjudications(parent_config TEXT,id TEXT,child_config TEXT,reason TEXT,PRIMARY KEY(parent_config,id));
    CREATE TABLE IF NOT EXISTS gates(size INTEGER,config TEXT,body TEXT,PRIMARY KEY(size,config));
    '''); return db

def ingest(db,path):
    started=time.perf_counter(); path=Path(path); checksum=sha(path)
    manifest=json.loads((ROOT/'supplied/manifest.json').read_text())
    if path.name in manifest['files'] and checksum!=manifest['files'][path.name]['sha256']: raise ValueError('Pinned input checksum mismatch')
    existing=db.execute('SELECT rows FROM inputs WHERE checksum=?',(checksum,)).fetchone()
    if existing: return {'checksum':checksum,'rows':existing[0],'seconds':time.perf_counter()-started,'ingestion_cache_hit':True}
    manifest=json.loads((ROOT/'supplied/manifest.json').read_text())
    if path.name in manifest['files'] and checksum!=manifest['files'][path.name]['sha256']: raise ValueError('Pinned input checksum mismatch')
    existing=db.execute('SELECT rows FROM inputs WHERE checksum=?',(checksum,)).fetchone()
    if existing: return {'checksum':checksum,'rows':existing[0],'seconds':time.perf_counter()-started,'ingestion_cache_hit':True}
    # Only the six source fields ever enter the data store. Extra/golden answer columns are rejected.
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or []) != FIELDS: raise ValueError('Require exactly the six original columns; golden/answer columns prohibited')
        with db:
            n=0
            for n,r in enumerate(reader,1):
                rid=r['review_id']; h=row_sha(r); text=r['review_text']
                if not rid or None in r or any(v is None for v in r.values()): raise ValueError('Malformed source row')
                old=db.execute('SELECT source_hash FROM sources WHERE id=?',(rid,)).fetchone()
                if old and old[0]!=h: raise ValueError('Conflicting source ID '+rid)
                db.execute('INSERT OR IGNORE INTO sources VALUES(?,?,?,?,?,?)',(rid,text,hashlib.sha256(text.encode()).hexdigest(),h,canonical(r),'pending' if text.strip() else 'quarantined'))
                db.execute('INSERT INTO scope VALUES(?,?,?) ON CONFLICT(checksum,id) DO UPDATE SET ordinal=excluded.ordinal',(checksum,rid,n))
            count=db.execute('SELECT count(*) FROM scope WHERE checksum=?',(checksum,)).fetchone()[0]
            if count!=n: raise ValueError('Duplicate IDs')
            db.execute('INSERT OR REPLACE INTO inputs VALUES(?,?,?)',(checksum,str(path.resolve()),n))
    return {'checksum':checksum,'rows':n,'seconds':time.perf_counter()-started}

def scoped(db,checksum):
    return db.execute('SELECT s.* FROM sources s JOIN scope q ON q.id=s.id WHERE q.checksum=? ORDER BY q.ordinal',(checksum,)).fetchall()

def config_id(cfg):
    # Sampling, budget and worker changes do not change semantic cache identity.
    return digest({k:cfg[k] for k in ('provider','model','effort','prompt_version','schema_version','max_output_tokens')} | {'prompt_sha256':sha(ROOT/'pipeline'/'rubric.txt')})

def validate(records,rows):
    by_id={r['id']:r for r in rows}
    if not isinstance(records,list) or len(records)!=len(rows): raise ValueError('Response cardinality mismatch')
    seen=set()
    for r in records:
        if not isinstance(r,dict): raise ValueError('Invalid record')
        rid=r.get('review_id')
        if rid not in by_id or rid in seen: raise ValueError('Unknown/duplicate response ID')
        seen.add(rid)
        if r.get('topic') not in TOPICS or r.get('intent') not in INTENTS: raise ValueError('Invalid labels')
        if type(r.get('severity')) is not int or not 1<=r['severity']<=5: raise ValueError('Invalid severity')
        if type(r.get('sentiment')) not in (int,float) or not math.isfinite(r['sentiment']) or not -1<=r['sentiment']<=1: raise ValueError('Invalid sentiment')
        if type(r.get('needs_review')) is not bool: raise ValueError('Invalid review flag')
        if not isinstance(r.get('entities'),list) or any(not isinstance(x,str) for x in r['entities']): raise ValueError('Invalid entities')
        q=r.get('evidence_quote')
        if not isinstance(q,str) or not q or q not in by_id[rid]['text']: raise ValueError('Invented evidence quote')
        if r['intent'] in ('praise','request','unclear') and r['severity']!=1: raise ValueError('Severity inconsistent with intent')
    return records

def persist_labels(db,cfg_id,rows,records):
    validate(records,rows); by_id={r['id']:r for r in rows}
    with db:
        for r in records:
            source=by_id[r['review_id']]
            body={k:r[k] for k in ('topic','intent','severity','sentiment','entities','evidence_quote','needs_review')}
            db.execute('INSERT OR REPLACE INTO labels VALUES(?,?,?,NULL)',(cfg_id,source['id'],canonical(body)))
            db.execute('INSERT OR IGNORE INTO cache VALUES(?,?,?,?,?)',(cfg_id,source['text_hash'],source['text'],source['id'],canonical(body)))

def reuse(db,cfg_id,rows):
    # Bulk exact-text join avoids a Python lookup per source row on every batch.
    with db:
        db.execute("""INSERT OR IGNORE INTO labels(config,id,body,cache_source_id)
        SELECT ?,s.id,c.body,c.source_id FROM sources s JOIN cache c ON c.text_hash=s.text_hash AND c.text=s.text AND c.config=?
        JOIN labels original ON original.config=c.config AND original.id=c.source_id AND original.cache_source_id IS NULL AND original.body=c.body
        WHERE s.status='pending'""",(cfg_id,cfg_id))
    ids={r['id'] for r in rows}
    return sum(1 for r in db.execute('SELECT id FROM labels WHERE config=?',(cfg_id,)) if r[0] in ids)

def records(db,checksum,cfg_id):
    for r in db.execute('SELECT s.*,coalesce(child.body,l.body) AS body,CASE WHEN child.body IS NOT NULL THEN child.cache_source_id ELSE l.cache_source_id END AS cache_source_id,CASE WHEN child.body IS NOT NULL THEN a.child_config ELSE ? END AS effective_config FROM sources s JOIN scope q ON q.id=s.id LEFT JOIN labels l ON l.id=s.id AND l.config=? LEFT JOIN adjudications a ON a.id=s.id AND a.parent_config=? LEFT JOIN labels child ON child.id=s.id AND child.config=a.child_config WHERE q.checksum=? ORDER BY q.ordinal',(cfg_id,cfg_id,cfg_id,checksum)):
        out={'review_id':r['id'],'source_sha256':r['source_hash']}
        if r['status']=='quarantined': out.update(status='quarantined',reason='empty_review_text')
        elif r['body']:
            out.update(json.loads(r['body']),status='completed',label_config=r['effective_config'])
            if r['cache_source_id']: out['cache_source_id']=r['cache_source_id']
        else: out.update(status='pending',reason='classification_not_executed')
        yield out

def aggregate(db,checksum,cfg_id):
    members=[]; totals={}; evidence={}
    for r in records(db,checksum,cfg_id):
        if r['status']!='completed' or r['intent'] not in ('complaint','cancellation'): continue
        issue=r['topic']; members.append({'issue_id':issue,'review_id':r['review_id']})
        n,s=totals.get(issue,(0,0)); totals[issue]=(n+1,s+r['severity'])
        evidence.setdefault(issue,[]).append({'review_id':r['review_id'],'quote':r['evidence_quote'],'severity':r['severity']})
    ranking=[]; claims=[]
    for rank,(issue,(n,s)) in enumerate(sorted(totals.items(),key=lambda x:(-x[1][1],x[0])),1):
        mean=str((Decimal(s)/n).quantize(Decimal('0.000001'),rounding=ROUND_HALF_UP))
        row=dict(rank=rank,issue_id=issue,complaint_count=n,severity_sum=s,mean_severity=mean,priority_score=s); ranking.append(row)
        for metric in ('complaint_count','severity_sum','mean_severity','priority_score'):
            claims.append(dict(claim_id=f'{issue}.{metric}',issue_id=issue,metric=metric,value=str(row[metric])))
        evidence[issue]=sorted(evidence[issue],key=lambda e:(-e['severity'],e['review_id']))[:3]
    result=dict(ranking=ranking,claims=claims,evidence=evidence)
    with db: db.execute('INSERT OR REPLACE INTO artifacts VALUES(?,?,?)',(digest([checksum,cfg_id,'aggregate']), 'aggregate', canonical(result)))
    return result,members

def export(db,checksum,cfg_id,out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    # Stream large exports to a temporary file, then atomic rename.
    target=out/'records.jsonl'; tmp=target.with_suffix('.tmp')
    counts={}
    with tmp.open('w',encoding='utf-8') as f:
        for r in records(db,checksum,cfg_id):
            counts[r['status']]=counts.get(r['status'],0)+1; f.write(canonical(r)+'\n')
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp,target)
    save_json(out/'run.json',dict(version='a5-audit-v1',analysis_count=sum(counts.values()),analysis_sha256=checksum,classification_input_fields=['review_text'],allow_multi_issue=False,completion_status=counts))
    agg,members=aggregate(db,checksum,cfg_id)
    save_csv(out/'membership.csv',members,['issue_id','review_id'])
    save_csv(out/'ranking.csv',agg['ranking'],['rank','issue_id','complaint_count','severity_sum','mean_severity','priority_score'])
    save_csv(out/'claims.csv',agg['claims'],['claim_id','issue_id','metric','value'])
    scope_ids={r[0] for r in db.execute('SELECT id FROM scope WHERE checksum=?',(checksum,))}
    scoped=[]; supporting=[]; excluded=[]
    roots={r.get('cache_source_id') for r in records(db,checksum,cfg_id)}-scope_ids-{None}
    run_ids={r[0] for r in db.execute('SELECT id FROM runs WHERE checksum=?',(checksum,))}
    for row in db.execute('SELECT event FROM calls ORDER BY started,id'):
        if not row[0]: continue
        event=json.loads(row[0]); ids=set(event.get('review_ids',[]))
        if (ids and ids<=scope_ids) or (not ids and event.get('run_id') in run_ids): scoped.append(row[0])
        elif ids & roots: supporting.append(row[0])
        else: excluded.append(row[0])
    atomic(out/'calls.jsonl','\n'.join(scoped)+('\n' if scoped else ''))
    support=out.parent/(out.name+'-support'); support.mkdir(exist_ok=True)
    atomic(support/'external-origin-calls.jsonl','\n'.join(supporting)+('\n' if supporting else ''))
    atomic(support/'other-experiment-calls.jsonl','\n'.join(excluded)+('\n' if excluded else ''))
    originals=[]
    for alias in records(db,checksum,cfg_id):
        origin=alias.get('cache_source_id')
        if origin not in roots: continue
        r=db.execute('SELECT s.raw,s.source_hash,l.body,l.cache_source_id FROM sources s JOIN labels l ON l.id=s.id WHERE s.id=? AND l.config=?',(origin,alias['label_config'])).fetchone()
        if not r or r['cache_source_id']: raise ValueError('Missing direct original cache evidence')
        originals.append(dict(alias_id=alias['review_id'],original_id=origin,label_config=alias['label_config'],source_sha256=r['source_hash'],source=json.loads(r['raw']),classification=json.loads(r['body'])))
    save_json(support/'cache-origins.json',originals)
    save_json(support/'scope-notes.json',dict(external_originals=len(roots),aliases=len(originals),scoped_calls=len(scoped),supporting_calls=len(supporting),other_calls=len(excluded),limitation='External originals are retained outside the declared sample; the supplied checker cannot resolve them. No provenance or usage was fabricated.'))
    for which in ('before','after'):
        key=f'checkpoint_{which}:{checksum}:{cfg_id}'
        r=db.execute('SELECT body FROM artifacts WHERE key=?',(key,)).fetchone()
        save_json(out/f'checkpoint_{which}.json',json.loads(r[0]) if r else {'completed_ids':[],'status':'not_demonstrated'})
    return counts
