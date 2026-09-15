"""Independent orientation-free compatibility bound for nonnegative fields.

Gaussian kernels and all amplitudes are nonnegative, so <a,Rb> >= 0 for any
relative rotation R. Therefore ||a-Rb||² <= ||a||²+||b||². Compare this bound
with (2r)². This is sufficient compatibility, not a necessary condition.
Numerical self norms have an engineering guard, not interval certification.
"""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

library_path,transfer_path,output=map(Path,sys.argv[1:])
library=json.loads(library_path.read_text());transfer=json.loads(transfer_path.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert transfer['libraryHash']==sha(library_path)
fit=set(transfer['fitFrames']);allowed={p['motif'] for r in library['trainingRegistrations'] if r['id'] in fit for p in r['selected']}
norms=[];bybase=defaultdict(list)
for i in sorted(allowed):
    motif=library['motifs'][i]
    for side,value in enumerate(motif['fieldM']):
        x=np.asarray(value['vectors']);w=np.asarray(value['amplitudes']);c=np.asarray(value['colors']);sigma=value['sigma']
        assert x.shape==(len(w),3) and len(c)==len(w) and np.isfinite(x).all() and np.isfinite(w).all() and np.all(w>=0) and sigma>0
        # No producer helper or scipy distance routine is used.
        terms=[]
        for j,v in enumerate(x):
            d=x-v
            terms.extend((w[j]*w*np.exp(-np.einsum('ij,ij->i',d,d)/(2*sigma*sigma))*(c==c[j])).tolist())
        norm=math.fsum(terms);guard=256*np.finfo(float).eps*max(1.,math.fsum(w)**2)
        row=dict(motif=i,base=motif['base'],side=side,squaredNorm=norm,upperSquaredNorm=norm+guard)
        norms.append(row);bybase[motif['base'],side].append(row)
maximum=max(norms,key=lambda x:x['upperSquaredNorm']);radius=transfer['summary']['diagnosticThreshold']
upper=2*maximum['upperSquaredNorm'];bound=(2*radius)**2
rows=[dict(base=base,side=side,maximumUpperSquaredNorm=max(x['upperSquaredNorm'] for x in values),decorations=len(values)) for (base,side),values in sorted(bybase.items())]
summary=dict(fittingDecorations=len(allowed),endpointFields=len(norms),radius=radius,
             maximumSquaredNorm=maximum['squaredNorm'],maximumNormWitness=maximum,
             universalSquaredDistanceUpperBound=upper,pairSquaredThreshold=bound,
             allFittingEndpointPairsCompatibleAtEveryRotation=bool(upper<bound),
             universallySufficientRadius=math.sqrt(upper)/2)
report=dict(scope=__doc__,libraryHash=sha(library_path),transferHash=sha(transfer_path),codeHash=sha(Path(__file__)),summary=summary,byBase=rows,norms=norms,
            limits='Nonnegative Gaussian-field pair compatibility only; other t constraints, geometry and multi-assignment common intersections are not certified. Floating-point bound is guarded but not interval-certified. Does not establish physical validity or useful search.')
serialized=json.dumps(report,indent=2)
with output.open('x') as f:f.write(serialized)
print(json.dumps(summary),flush=True)
