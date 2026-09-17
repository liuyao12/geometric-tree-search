"""Training-graph distance coordinates with interval-valued markings.

Observed graph edges have channel differences <=1. Each scalar assignment
represents an interval of radius 1/2; channels use Cartesian products (L-inf).
No calibration frames or negative-connection labels choose landmarks.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import shortest_path,connected_components

supportp,graphp,checkp,out=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
support,graph,check=[json.loads(p.read_text()) for p in [supportp,graphp,checkp]]
assert graph['supportHash']==sha(supportp) and check['markingHash']==sha(graphp)
anchors=support['anchors'];n=len(anchors);edges=graph['observedEqualityEdges']
rr=[a for a,b in edges]+[b for a,b in edges];cc=[b for a,b in edges]+[a for a,b in edges]
A=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(n,n)).tocsr()
count,labels=connected_components(A,directed=False);D=shortest_path(A,directed=False,unweighted=True)
V=np.zeros((n,8),dtype=int);landmarks=[]
for label in range(count):
    ids=np.flatnonzero(labels==label);d=D[np.ix_(ids,ids)]
    first=int(np.argmax(d.max(axis=1)));chosen=[first]
    while len(chosen)<min(8,len(ids)):
        distances=d[:,chosen].min(axis=1);distances[chosen]=-1
        chosen.append(int(np.argmax(distances)))
    for channel in range(8):V[ids,channel]=d[:,chosen[channel%len(chosen)]].astype(int)
    landmarks.append(dict(component=int(label),anchors=ids[chosen].tolist(),diameter=int(d.max())))
species=np.asarray([a['species'] for a in anchors]);weights=np.asarray([a['t'] for a in anchors])
eligible=(species[:,None]==species[None,:])&(weights[:,None]+weights[None,:]<=1+1e-12)&np.triu(np.ones((n,n),dtype=bool))
runs=[]
for channels in [1,2,4,8]:
    values=V[:,:channels];assert all(np.max(np.abs(values[a]-values[b]))<=1 for a,b in edges)
    differences=np.max(np.abs(values[:,None,:]-values[None,:,:]),axis=2)
    runs.append(dict(channels=channels,values=values.tolist(),compatibleAnchorPairs=int(eligible.sum()),
                     separatedAbstractPairs=int(np.sum(eligible&(differences>1)))))
report=dict(scope=__doc__,sourceHashes={p.name:sha(p) for p in [supportp,graphp,checkp]},codeHash=sha(Path(__file__)),
            radius=.5,norm='L-infinity Cartesian-product intervals',landmarks=landmarks,runs=runs,
            limits='Conditional graph-distance construction, not joint support/value optimization. Abstract anchor-pair separation is not rejection of a geometrically realizable or physically invalid connection. Disjoint components share arbitrary gauges. No calibration fitting, motif variants, learned mark-only support or tree-search speedup.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps([dict(channels=r['channels'],pairs=r['compatibleAnchorPairs'],separated=r['separatedAbstractPairs']) for r in runs]))
