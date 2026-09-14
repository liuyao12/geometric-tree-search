"""Global unit-RMS vector fit on each largest training overlap component.

Sparse smallest-eigenvector diagnostic; no held-out data, no search claim.
Participation fraction reports whether a small residual is obtained by
concentrating vector magnitude on a few site variables.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.sparse import coo_matrix,eye
from scipy.sparse.linalg import eigsh

dest=Path(sys.argv[2]);dest.mkdir();summaries=[]
for fold in range(6):
    raw=(Path(sys.argv[1])/f'{fold}.json').read_bytes();d=json.loads(raw)
    component=max(d['components'],key=lambda c:len(c['members']));nodes=component['members'];index={v:i for i,v in enumerate(nodes)}
    rows=[];cols=[];values=[];count=0
    for a,ra,b,rb in d['constraints']:
        if a not in index:continue
        assert b in index
        for v,R,sign in ((a,ra,1),(b,rb,-1)):
            for i in range(3):
                for j in range(3):rows.append(3*count+i);cols.append(3*index[v]+j);values.append(sign*R[i][j])
        count+=1
    B=coo_matrix((values,(rows,cols)),shape=(3*count,3*len(nodes))).tocsr();H=(B.T@B).tocsc()
    eigenvalues,vectors=eigsh(H,k=1,sigma=-1e-8,which='LM',tol=1e-9,v0=np.ones(H.shape[0])/np.sqrt(H.shape[0]))
    v=vectors[:,0];eigenvalue=float(eigenvalues[0]);eigen_residual=float(np.linalg.norm(H@v-eigenvalue*v))
    assert eigen_residual<1e-6
    v*=np.sqrt(len(nodes));site=v.reshape(-1,3);residual=(B@v).reshape(-1,3)
    magnitudes=np.linalg.norm(site,axis=1);norm2=magnitudes**2
    summary={'fold':fold,'variables':len(nodes),'constraints':count,'smallestComputedEigenvalue':eigenvalue,
        'eigenResidual':eigen_residual,'unitRmsSiteNorm':float(np.sqrt(np.mean(norm2))),
        'overlapRmsMismatch':float(np.sqrt(np.mean(np.sum(residual**2,axis=1)))),
        'overlapMaximumMismatch':float(np.max(np.linalg.norm(residual,axis=1))),
        'participationFraction':float(np.sum(norm2)**2/(len(nodes)*np.sum(norm2**2))),
        'maximumSiteNorm':float(max(magnitudes)),'siteNormAbovePointOne':int(sum(magnitudes>.1))}
    with (dest/f'{fold}.json').open('x') as f:json.dump({'scope':__doc__,'holonomyHash':hashlib.sha256(raw).hexdigest(),
        'nodes':nodes,'vectors':site.tolist(),'summary':summary},f)
    summaries.append(summary);print(json.dumps(summary),flush=True)
(dest/'summary.json').write_text(json.dumps({'scope':__doc__,'results':summaries},indent=2))
