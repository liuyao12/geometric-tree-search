"""Data-derived support count/coordinates/t under supplied motif poses.

No inherited anchors, t-values, occurrence atom lists or permutations are read.
Finite proposal/MILP pilot, not unrestricted joint anchor-and-marking learning.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint, minimize
from scipy.sparse import coo_matrix, hstack, eye, vstack

coordp, dictp, libp, transferp, out = map(Path, sys.argv[1:6])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
coords, dictionary, library, transfer = [json.loads(p.read_text()) for p in [coordp, dictp, libp, transferp]]
assert dictionary['coordinateHash'] == sha(coordp)
assert library['sourceHashes']['dictionary'] == sha(dictp)
assert transfer['libraryHash'] == sha(libp)
fit = set(transfer['fitFrames'])
cc = {c['id']: c for c in coords['configurations']}
dd = {c['id']: c for c in dictionary['configurations']}
training = [r for r in library['trainingRegistrations'] if r['id'] in fit and r['coverVariant'] == 'original']
assert len({r['id'] for r in training}) == len(training)
radius, tolerance = 4., .15
clouds, offsets, required = {}, {}, 0
poses = []
for reg in training:
    cid = reg['id']; c = cc[cid]; pos = np.asarray(c['positions']); cell = np.asarray(c['cell'])
    inv = np.linalg.inv(cell); shifts = np.asarray(list(itertools.product(range(-2,3),repeat=3))) @ cell
    smin = np.linalg.svd(cell, compute_uv=False)[-1]
    offsets[cid] = required; required += len(pos)
    for selected in reg['selected']:
        o = dd[cid]['occurrences'][selected['edge']]
        R, tr = np.asarray(o['rotationRow']), np.asarray(o['translation'])
        assert np.max(np.abs(R.T@R-np.eye(3))) < 1e-8 and np.linalg.det(R)>0
        d = pos-tr; d -= np.round(d@inv)@cell
        images = d[:,None,:]+shifts[None,:,:]
        idx = np.argmin(np.sum(images**2,axis=2),axis=1)
        nearest = images[np.arange(len(pos)),idx]
        # Certify omitted image shells cannot be nearer for these displacements.
        assert np.all(3*smin-np.linalg.norm(d,axis=1)>np.linalg.norm(nearest,axis=1)+1e-9)
        local = nearest @ R.T
        keep = np.flatnonzero(np.linalg.norm(local,axis=1)<=radius)
        obs = dict(cid=cid, edge=selected['edge'], type=o['type'], xyz=local[keep],
                   ids=keep, species=np.asarray(c['species'])[keep])
        clouds.setdefault(o['type'],[]).append(obs)
        poses.append(dict(configuration=cid,edge=selected['edge'],type=o['type'],rotationRow=R.tolist(),translation=tr.tolist()))

proposals=[]; rejected=0
for typ, observations in sorted(clouds.items()):
    seed=observations[0]; signatures=set()
    for x0, species in zip(seed['xyz'],seed['species']):
        x=x0.copy(); assignments=[]
        for iteration in range(8):
            assignments=[]; matches=[]
            for obs in observations:
                choices=np.flatnonzero(obs['species']==species)
                if not len(choices):break
                distances=np.linalg.norm(obs['xyz'][choices]-x,axis=1)
                order=np.argsort(distances)
                # Ambiguity is not silently resolved by atom index.
                if len(order)>1 and distances[order[1]]<=2*tolerance:break
                j=choices[order[0]]
                if distances[order[0]]>2*tolerance:break
                assignments.append((obs['cid'],int(obs['ids'][j])))
                matches.append(obs['xyz'][j])
            if len(assignments)!=len(observations):break
            new=np.mean(matches,axis=0)
            if np.linalg.norm(new-x)<1e-10:x=new;break
            x=new
        if len(assignments)==len(observations) and max(np.linalg.norm(v-x) for v in matches)>tolerance:
            # A mean need not lie in the intersection of all tolerance balls.
            # Fit a minimum enclosing ball; still enforce the original .15 Å.
            pts=np.asarray(matches)
            def constraints(z):return z[3]-np.sum((pts-z[:3])**2,axis=1)
            fitball=minimize(lambda z:z[3],np.r_[x,max(np.sum((pts-x)**2,axis=1))],
                             method='SLSQP',bounds=[(None,None)]*3+[(0,None)],
                             constraints={'type':'ineq','fun':constraints},options={'ftol':1e-12,'maxiter':100})
            if fitball.success:x=fitball.x[:3]
        if len(assignments)!=len(observations) or max(np.linalg.norm(v-x) for v in matches)>tolerance+1e-9:
            rejected+=1;continue
        signature=tuple(assignments)
        if signature in signatures:continue
        signatures.add(signature)
        proposals.append(dict(type=typ,species=str(species),position=x.tolist(),initialPosition=x0.tolist(),
                              observations=assignments,maxResidual=max(float(np.linalg.norm(v-x)) for v in matches)))

n=len(proposals); rr=[];jj=[]
for j,p in enumerate(proposals):
    for cid,a in p['observations']:rr.append(offsets[cid]+a);jj.append(j)
A=coo_matrix((np.ones(len(rr)),(rr,jj)),shape=(required,n)).tocsr()
# Minimize the number of positive anchors. Each weight has its own binary gate;
# no equal-weight or prescribed coordination constraint is imposed.
constraints=LinearConstraint(vstack([hstack([A,coo_matrix(A.shape)]),hstack([eye(n),-eye(n)])]).tocsr(),
                             np.r_[np.ones(required),np.full(n,-np.inf)],np.r_[np.ones(required),np.zeros(n)])
start=time.monotonic()
r=milp(np.r_[np.zeros(n),np.ones(n)],integrality=np.r_[np.zeros(n),np.ones(n)],
       bounds=Bounds(np.zeros(2*n),np.ones(2*n)),constraints=constraints,options={'time_limit':30})
weights=None if r.x is None else r.x[:n]
active=[] if weights is None else [dict(proposals[i],t=float(w)) for i,w in enumerate(weights) if w>1e-8]
residual=None if weights is None else float(np.max(np.abs(A@weights-1)))
report=dict(scope=__doc__,sourceHashes={p.name:sha(p) for p in [coordp,dictp,libp,transferp]},codeHash=sha(Path(__file__)),
            trainingFrames=[r['id'] for r in training],poses=poses,requiredAtoms=required,proposalCount=n,rejectedProposals=rejected,
            selectedAnchorCount=len(active),anchors=active,uncoveredRows=int(np.sum(np.asarray(A.sum(axis=1)).ravel()==0)),solverStatus=int(r.status),solverMessage=r.message,
            solverSeconds=time.monotonic()-start,maxFillingResidual=residual,neighborhoodRadius=radius,positionTolerance=tolerance,
            limits='Supplied occurrence selection, motif types and poses; finite atom-derived proposals within fixed reach. Locations refined by cloud means/minimax; minimum count only within this proposal pool if optimal. Float weights, not exact certificates. No learned m-values, off-atom marking support, held-out reconstruction, independent-condition provenance or tree-search result.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:report[k] for k in ['requiredAtoms','proposalCount','rejectedProposals','selectedAnchorCount','solverStatus','solverSeconds','maxFillingResidual']}))
