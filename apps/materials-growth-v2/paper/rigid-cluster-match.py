"""Proper rigid registration from distance-compatible anchor triples.

Farthest-pair/maximum-area anchors propose rotations; full-site assignment and
Kabsch refinement verify a fit. Successful fits are witnesses. Failed proposals
do not certify absence of every tolerance-feasible isometry.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment

def matches(source,target,epsilon=.03):
    """Yield distinct witnessed site maps; not an exhaustive tolerance solver."""
    x=np.asarray(source,float);y=np.asarray(target,float)
    if x.shape!=y.shape or len(x)<3:return None
    dx=np.linalg.norm(x[:,None]-x[None,:],axis=2);dy=np.linalg.norm(y[:,None]-y[None,:],axis=2)
    n=len(x);upper=np.triu_indices(n,1)
    if np.max(np.abs(np.sort(dx[upper])-np.sort(dy[upper])))>2*epsilon+1e-10:return None
    a,b=np.unravel_index(np.argmax(dx),dx.shape)
    areas=np.linalg.norm(np.cross(x-x[a],x[b]-x[a]),axis=1);c=int(np.argmax(areas))
    if areas[c]<1e-10:return None
    anchors=[a,b,c];sx=x[anchors];center=sx.mean(axis=0)
    def fit(p,q):
        pm=p.mean(axis=0);qm=q.mean(axis=0);u,_,vt=np.linalg.svd((p-pm).T@(q-qm));fix=np.eye(3);fix[2,2]=np.linalg.det(u@vt)
        R=u@fix@vt;return R,qm-pm@R
    seen=set()
    for i,j in zip(*np.where(np.abs(dy-dx[a,b])<=2*epsilon)):
        if i==j:continue
        for k in np.flatnonzero((np.abs(dy[i]-dx[a,c])<=2*epsilon)&(np.abs(dy[j]-dx[b,c])<=2*epsilon)):
            if k in (i,j):continue
            R,t=fit(sx,y[[i,j,k]])
            for _ in range(3):
                cost=np.linalg.norm((x@R+t)[:,None]-y[None,:],axis=2)
                _,permutation=linear_sum_assignment(cost);R,t=fit(x,y[permutation])
            residual=float(np.max(np.linalg.norm(x@R+t-y[permutation],axis=1)))
            key=tuple(permutation)
            if residual<=epsilon and key not in seen:
                seen.add(key)
                yield {'permutation':permutation.tolist(),'rotationRow':R.tolist(),'translation':t.tolist(),'residual':residual}

def match(source,target,epsilon=.03):
    return next(matches(source,target,epsilon),None)
