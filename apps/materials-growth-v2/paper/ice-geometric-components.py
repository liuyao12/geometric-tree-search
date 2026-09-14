"""Data-derived distance-gap components; no molecule or coordination rules.

Use training nearest-neighbor distances to define a scale, and the largest gap
among sorted training pair distances below 2.5 times that scale as a threshold.
This is a restricted component proposal, not general motif or marking learning.
"""
import json
import sys
from pathlib import Path
from collections import Counter
import numpy as np
from ase import Atoms
from scipy.sparse.csgraph import connected_components

def distances(c):
    a=Atoms(c['species'],positions=c['positions'],cell=c['cell'],pbc=True)
    d=a.get_all_distances(mic=True);np.fill_diagonal(d,np.inf)
    return d

if __name__=='__main__':
    data=json.loads(Path(sys.argv[1]).read_text())['configurations']
    metadata=json.loads(Path(sys.argv[2]).read_text())['configurations']
    train={c['id'] for c in metadata if c['split']=='train'}
    ds={c['id']:distances(c) for c in data}
    scale=float(np.median(np.concatenate([d.min(axis=1) for key,d in ds.items() if key in train])))
    values=np.sort(np.concatenate([d[(d<2.5*scale)&(d>0)] for key,d in ds.items() if key in train]))
    gap=int(np.argmax(np.diff(values)));threshold=float((values[gap]+values[gap+1])/2)
    results=[]
    for c in data:
        d=ds[c['id']];count,labels=connected_components(d<threshold,directed=False)
        compositions=Counter();diameters=[]
        for k in range(count):
            ids=np.flatnonzero(labels==k)
            compositions[str(sorted(Counter(c['species'][i] for i in ids).items()))]+=1
            diameters.append(float(np.max(np.where(np.isfinite(d[np.ix_(ids,ids)]),d[np.ix_(ids,ids)],0))))
        r={'id':c['id'],'atoms':len(labels),'components':count,'compositions':dict(compositions),
           'maxComponentDiameterAngstrom':max(diameters),'allAtomsCovered':True,
           'positiveOverlapComponentsIfDisjointUnitTiles':count,
           'growthReady':False}
        results.append(r);print(json.dumps(r),flush=True)
    Path(sys.argv[3]).write_text(json.dumps({'scope':__doc__,'trainingIds':sorted(train),
        'scale':scale,'threshold':threshold,'gapEndpoints':[float(values[gap]),float(values[gap+1])],
        'results':results},indent=2))
