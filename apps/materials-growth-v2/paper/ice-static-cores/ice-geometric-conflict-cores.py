"""Shrink finite-pool t-only dead-point witnesses; no learned generalization."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
import time
modelp,profilep,checkp,out=map(Path,sys.argv[1:]);raw=modelp.read_bytes();model=json.loads(raw)['models'][0]['model'];profile=json.loads(profilep.read_text());check=json.loads(checkp.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert check['profileHash']==sha(profilep) and check['modelHash']==profile['sourceHash']==sha(modelp)
geometry={}
for c in model['candidates']:
    support={t['point']:t['value'] for t in c['t']}
    if c['base'] in geometry:assert geometry[c['base']]==support
    geometry[c['base']]=support
def dead(owners,point):
    totals=Counter()
    for g in owners:totals.update(geometry[g])
    if totals[point]>=model['capacity'] or any(t>model['capacity'] for t in totals.values()):return False
    return not any(point in t and g not in owners and all(totals[p]+v<=model['capacity'] for p,v in t.items()) for g,t in geometry.items())
start=time.monotonic();cores=[];seen=set()
for run in profile['results']:
    for state in run['deadStates']:
        for w in state['examples']:
            point=w['point'];key=(tuple(state['owners']),point)
            if key in seen:continue
            seen.add(key);owners=set(state['owners']);assert dead(owners,point)
            for g in sorted(owners):
                if dead(owners-{g},point):owners.remove(g)
            assert owners and all(not dead(owners-{g},point) for g in owners)
            totals=Counter()
            for g in owners:totals.update(geometry[g])
            blockers=[]
            for g,t in geometry.items():
                if point not in t:continue
                if g in owners:blockers.append(dict(inventory=g,reason='consumed'))
                else:
                    p=next(p for p,v in t.items() if totals[p]+v>model['capacity'])
                    blockers.append(dict(inventory=g,reason='capacity',point=p,current=totals[p],contribution=t[p]))
            cores.append(dict(owners=sorted(owners),point=point,sourceOwners=len(state['owners']),blockers=blockers))
report=dict(scope=__doc__,modelHash=sha(modelp),profileHash=sha(profilep),priorCheckHash=sha(checkp),codeHash=sha(Path(__file__)),cores=cores,seconds=time.monotonic()-start,limits='Inclusion-minimal for the chosen dead-point predicate and deletion order, not minimum cardinality. Pool-specific integer contradiction valid for all decorations of these inventory supports. Not a transferable material marking or an exclusion inferred merely from a timeout.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(cores),flush=True)
