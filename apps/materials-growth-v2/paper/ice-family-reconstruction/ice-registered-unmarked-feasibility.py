"""Separate post-search integer feasibility diagnostic; no marking or search hint."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
modelp,out=map(Path,sys.argv[1:]);raw=modelp.read_bytes();model=json.loads(raw)['models'][0]['model']
supports={}
for c in model['candidates']:
    t={p['point']:p['value'] for p in c['t']}
    if c['base'] in supports:assert supports[c['base']]==t
    supports[c['base']]=t
keys=list(supports);required=model['required'];A=np.asarray([[supports[k].get(p,0) for k in keys] for p in required]);start=time.monotonic()
r=milp(np.zeros(len(keys)),integrality=np.ones(len(keys)),bounds=Bounds(0,1),constraints=LinearConstraint(A,model['capacity'],model['capacity']),options={'time_limit':10})
selected=[];verified=False
if r.x is not None:
    bits=np.rint(r.x).astype(int);assert set(bits)<=set([0,1]);verified=bool(np.all(A@bits==model['capacity']));selected=[k for k,b in zip(keys,bits) if b]
report=dict(scope=__doc__,sourceHash=hashlib.sha256(raw).hexdigest(),codeHash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),solverStatus=int(r.status),solverMessage=r.message,seconds=time.monotonic()-start,verifiedUnmarkedFilling=verified,selectedInventories=selected,requiredPoints=len(required),geometryInventories=len(keys),limits='Separate mixed-integer solver, not GCTS. Integer t witness only, no Gaussian marking assignment. Run after tree-search timeouts; never passed to tree search. No complete-continuous-pose or growth claim.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report),flush=True)
