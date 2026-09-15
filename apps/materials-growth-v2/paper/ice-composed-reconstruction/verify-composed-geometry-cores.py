"""Independent ordered integer proof-DAG checker; no producer imports."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
modelp,resultp,out=map(Path,sys.argv[1:]);raw=modelp.read_bytes();model=json.loads(raw)['models'][0]['model'];result=json.loads(resultp.read_text())
assert result['sourceHash']==hashlib.sha256(raw).hexdigest()
geometry={}
for c in model['candidates']:
    t={v['point']:v['value'] for v in c['t']};assert len(t)==len(c['t']) and all(isinstance(v,int) and v>0 for v in t.values())
    if c['base'] in geometry:assert geometry[c['base']]==t
    geometry[c['base']]=t
verified=[];totalblockers=0;composed=0;depth=[]
for index,core in enumerate(result['cores']):
    used=set(core['owners']);assert used and len(used)==len(core['owners']) and used<=geometry.keys() and core['point'] in model['required']
    totals=Counter()
    for g in used:totals.update(geometry[g])
    assert max(totals.values())<=model['capacity'] and totals[core['point']]<model['capacity']
    assert not any(p<=used for p in verified)
    blockers={b['inventory']:b for b in core['blockers']};expected={g for g,t in geometry.items() if core['point'] in t}
    assert set(blockers)==expected and len(blockers)==len(core['blockers']);dependencies=set()
    for g,b in blockers.items():
        if b['reason']=='consumed':assert g in used
        elif b['reason']=='capacity':assert b['point'] in geometry[g] and totals[b['point']]+geometry[g][b['point']]>model['capacity']
        else:
            assert b['reason']=='prior-core' and isinstance(b['dependency'],int) and 0<=b['dependency']<index
            assert verified[b['dependency']]<=used|{g};dependencies.add(b['dependency'])
        totalblockers+=1
    assert set(core['dependencies'])==dependencies and len(core['dependencies'])==len(dependencies)
    composed+=bool(dependencies);depth.append(1+max([depth[d] for d in dependencies],default=0));verified.append(used)
report=dict(resultHash=hashlib.sha256(resultp.read_bytes()).hexdigest(),modelHash=hashlib.sha256(raw).hexdigest(),verifierHash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),verifiedCores=len(verified),composedCores=composed,checkedBlockers=totalblockers,maximumProofDepth=max(depth,default=0),limits='Exact integer t-capacity and consumed inventory leaves, with strictly earlier verified exclusions. Certifies exclusions for this finite pool only, not search chronology, timing, marked-state equivalence, pose completeness or transfer to other data.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
