"""Local rigid registration to frozen learned anchors; no weight/support edits.

Original occurrence identities initialize an ICP/minimax proposal. This is not
complete pose enumeration, a fresh decomposition search, or m-learning.
"""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

coordp,dictp,libp,supportp,out=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coords,dictionary,library,support=[json.loads(p.read_text()) for p in [coordp,dictp,libp,supportp]]
for p in [coordp,dictp,libp]:assert support['sourceHashes'][p.name]==sha(p)
cc={c['id']:c for c in coords['configurations']};dd={r['id']:r for r in dictionary['configurations']}
groups=defaultdict(list)
for a in support['anchors']:groups[a['type']].append(a)
tol=support['positionTolerance'];poses=[];counts=defaultdict(int)
for reg in library['trainingRegistrations']:
    if reg['coverVariant']!='original':continue
    cid=reg['id'];c=cc[cid];cell=np.asarray(c['cell']);inv=np.linalg.inv(cell)
    assert np.linalg.svd(cell,compute_uv=False)[-1]>2*tol
    pos=(np.asarray(c['positions'])@inv%1)@cell;shifts=np.asarray(list(itertools.product([-1,0,1],repeat=3)))@cell
    trees={}
    for species in set(c['species']):
        ids=np.flatnonzero(np.asarray(c['species'])==species);cloud=(pos[ids,None,:]+shifts[None,:,:]).reshape(-1,3)
        trees[species]=cKDTree(cloud),np.repeat(ids,27),cloud
    for chosen in reg['selected']:
        edge=chosen['edge'];o=dd[cid]['occurrences'][edge];R=np.asarray(o['rotationRow']);tr=np.asarray(o['translation'])
        anchors=groups[o['type']];record=dict(configuration=cid,edge=edge,type=o['type'],rotationRow=R.tolist(),translation=tr.tolist())
        if not anchors:record['status']='no-learned-support';poses.append(record);continue
        X=np.asarray([a['position'] for a in anchors])
        def match(R,tr):
            pred=X@R+tr;targets=[];ids=[];errors=[];unique=True
            for i,a in enumerate(anchors):
                shift=np.floor(pred[i]@inv)@cell;wrapped=pred[i]-shift;tree,indices,cloud=trees[a['species']]
                distance,j=tree.query(wrapped);targets.append(cloud[j]+shift);ids.append(int(indices[j]));errors.append(float(distance))
                if len(tree.query_ball_point(wrapped,tol+1e-9))>1:unique=False
            return np.asarray(targets),max(errors),unique and len(ids)==len(set(ids))
        target,initial,unique=match(R,tr);best=(initial,R.copy(),tr.copy(),unique)
        if initial<=tol+1e-9 and unique:record['status']='unchanged-valid'
        elif initial>2*tol:record['status']='outside-local-basin'
        else:
            for iteration in range(12):
                target,error,unique=match(R,tr)
                if not unique:break
                xc=X.mean(axis=0);yc=target.mean(axis=0);u,s,vt=np.linalg.svd((X-xc).T@(target-yc))
                correction=np.eye(3);correction[2,2]=np.linalg.det(u@vt)
                newR=u@correction@vt;newtr=yc-xc@newR
                _,error,unique=match(newR,newtr)
                if unique and error<best[0]:best=(error,newR.copy(),newtr.copy(),True)
                stop=np.max(np.abs(newR-R))<1e-10 and np.max(np.abs(newtr-tr))<1e-10
                R,tr=newR,newtr
                if stop:break
            error,R,tr,unique=best;target,_,_=match(R,tr)
            if error>tol+1e-9 and unique:
                def posed(z):return R@Rotation.from_rotvec(z[:3]).as_matrix(),tr+z[3:6]
                def residual(z):
                    rr,tt=posed(z);return z[6]-np.sum((X@rr+tt-target)**2,axis=1)
                fit=minimize(lambda z:z[6],np.r_[np.zeros(6),error**2],method='SLSQP',
                             bounds=[(-.2,.2)]*3+[(-2*tol,2*tol)]*3+[(0,None)],
                             constraints={'type':'ineq','fun':residual},options={'ftol':1e-12,'maxiter':100})
                newR,newtr=posed(fit.x);_,error,unique=match(newR,newtr)
                if unique and error<best[0]:best=(error,newR,newtr,True)
            error,R,tr,unique=best;record.update(rotationRow=R.tolist(),translation=tr.tolist())
            record['status']='locally-recovered' if unique and error<=tol+1e-9 else 'still-unmatched'
        record.update(initialMaxError=initial,finalMaxError=best[0]);counts[record['status']]+=1;poses.append(record)
report=dict(sourceHashes={p.name:sha(p) for p in [coordp,dictp,libp,supportp]},codeHash=sha(Path(__file__)),poses=poses,counts=dict(counts),
            limits=__doc__+' Valid input poses preserved. Invalid poses use nearest same-label matching, proper Kabsch rotations and bounded local minimax refinement. Frozen .15 Å final tolerance; a failed local fit is not impossibility. Coverage and weights require independent replay.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report['counts']))
