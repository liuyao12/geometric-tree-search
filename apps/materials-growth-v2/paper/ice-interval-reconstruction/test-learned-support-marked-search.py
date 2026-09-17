"""Reject malformed exports and a geometrically capacity-compatible m conflict."""
import copy,hashlib,json,subprocess,sys,tempfile
from collections import defaultdict
from pathlib import Path

coord,support,mark,base,poolpath,resultpath=sys.argv[1:]
pool=json.loads(Path(poolpath).read_text());result=json.loads(Path(resultpath).read_text())
verifier=Path(__file__).with_name('verify-learned-support-marked-search.py')
entry=pool['models'][0];by_point=defaultdict(list)
for c in entry['model']['candidates']:
    for m in c['m']:by_point[m['point'],m['channel']].append((c,m))
pair=None
for group in by_point.values():
    for i,(a,ma) in enumerate(group):
        for b,mb in group[i+1:]:
            if a['id']==b['id'] or max(ma['lo'],mb['lo'])<=min(ma['hi'],mb['hi']):continue
            totals=defaultdict(int)
            for c in [a,b]:
                for t in c['t']:totals[t['point']]+=t['value']
            if max(totals.values())<=entry['model']['capacity']:pair=[a['id'],b['id']];break
        if pair:break
    if pair:break
assert pair,'This control needs an actual t-compatible m-conflicting pair'
with tempfile.TemporaryDirectory(prefix='gcts-mark-controls-') as tmp:
    for kind in ['missing-channel','shifted-value','t-change','interval-conflict']:
        pp=copy.deepcopy(pool);rr=copy.deepcopy(result)
        c=pp['models'][0]['model']['candidates'][0]
        if kind=='missing-channel':c['m'].pop()
        elif kind=='shifted-value':c['m'][0]['lo']+=10;c['m'][0]['hi']+=10
        elif kind=='t-change':c['t'][0]['value']=2 if c['t'][0]['value']==1 else 1
        else:rr['results'][0].update(selected=pair,complete=False,status='budget-unknown')
        p=Path(tmp)/'pool.json';p.write_text(json.dumps(pp));rr['poolHash']=hashlib.sha256(p.read_bytes()).hexdigest()
        r=Path(tmp)/'result.json';r.write_text(json.dumps(rr))
        child=subprocess.run([sys.executable,str(verifier),coord,support,mark,base,str(p),str(r),str(Path(tmp)/f'{kind}-check.json')],capture_output=True,text=True)
        assert child.returncode!=0 and 'AssertionError' in child.stderr,child.stderr
        print(kind,'rejected',flush=True)
