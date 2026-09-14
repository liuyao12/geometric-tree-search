"""Direct vector residual and eigen-equation check, without the sparse solver."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
results=[]
for fold in range(6):
    raw=(Path(sys.argv[1])/f'{fold}.json').read_bytes();d=json.loads(raw)
    f=json.loads((Path(sys.argv[2])/f'{fold}.json').read_text());s=f['summary']
    assert f['holonomyHash']==hashlib.sha256(raw).hexdigest()
    nodes=f['nodes'];assert nodes==max(d['components'],key=lambda c:len(c['members']))['members']
    index={v:i for i,v in enumerate(nodes)};vectors=np.array(f['vectors']);gradient=np.zeros_like(vectors);residuals=[]
    for a,ra,b,rb in d['constraints']:
        if a not in index:continue
        ra=np.array(ra);rb=np.array(rb);i,j=index[a],index[b]
        error=ra@vectors[i]-rb@vectors[j];residuals.append(float(np.linalg.norm(error)))
        gradient[i]+=ra.T@error;gradient[j]-=rb.T@error
    norms=np.linalg.norm(vectors,axis=1);assert abs(np.mean(norms**2)-1)<1e-9
    eigen_residual=np.linalg.norm(gradient-s['smallestComputedEigenvalue']*vectors)/np.sqrt(len(nodes))
    assert eigen_residual<1e-6
    expected={'overlapRmsMismatch':float(np.sqrt(np.mean(np.square(residuals)))),
        'overlapMaximumMismatch':max(residuals),'participationFraction':float(sum(norms**2)**2/(len(nodes)*sum(norms**4))),
        'maximumSiteNorm':max(norms),'siteNormAbovePointOne':int(sum(norms>.1))}
    assert all(abs(s[k]-v)<1e-8 for k,v in expected.items())
    results.append({'fold':fold,'verifiedEigenEquation':True,**expected})
out={'scope':__doc__,'results':results};print(json.dumps(out,indent=2))
if len(sys.argv)>3:
    with Path(sys.argv[3]).open('x') as file:json.dump(out,file,indent=2)
