"""Independent all-pair signature enumeration and assignment-based relation check."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment

source,relation_path,output=map(Path,sys.argv[1:4])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
library=json.loads(source.read_text());relation=json.loads(relation_path.read_text())
assert relation['libraryHash']==sha(source)
radius=relation['radiusAngstrom']
if 'calibration' in relation:
    cp,kp=map(Path,sys.argv[4:]);calibration=json.loads(cp.read_text());check=json.loads(kp.read_text())
    assert relation['calibration']['reportHash']==check['reportHash']==sha(cp)
    assert relation['calibration']['checkHash']==sha(kp)
    assert calibration['libraryHash']==check['libraryHash']==sha(source)
    finite=[r['distanceAngstrom'] for r in calibration['results'] if r['distanceAngstrom'] is not None]
    assert relation['calibration']['quantile']==.95 and radius==float(np.quantile(finite,.95))
    assert relation['markingRadiusAngstrom']==library['markingRadiusAngstrom']
else:assert radius==library['markingRadiusAngstrom']
motifs=library['motifs'];expected=[{i} for i in range(len(motifs))];checks=0
for side in range(2):
    buckets=defaultdict(list);features={};colors={};vectors={}
    for i,m in enumerate(motifs):
        c=m['cloudM'][side];v=np.asarray(c['vectors']);labels=[json.dumps(k,sort_keys=True) for k in c['colors']]
        groups=defaultdict(list)
        for label,x in zip(labels,v,strict=True):groups[label].append(x)
        layout=tuple((k,len(groups[k])) for k in sorted(groups))
        buckets[m['base'],layout].append(i)
        features[i]=np.concatenate([np.sort(groups[k],axis=0).T.ravel() for k in sorted(groups)])
        colors[i]=np.array(labels);vectors[i]=v
    for ids in buckets.values():
        # Enumerate the full pair matrix, independently of the compiler's KD tree.
        distances=cdist(np.array([features[i] for i in ids]),np.array([features[i] for i in ids]),metric='chebyshev')
        for a,b in np.argwhere(np.triu(distances<=radius+1e-8,k=1)):
            i,j=ids[a],ids[b];checks+=1
            allowed=(colors[i][:,None]==colors[j][None,:])&(cdist(vectors[i],vectors[j])<=radius+1e-10)
            rows,cols=linear_sum_assignment(~allowed)
            if allowed[rows,cols].all():expected[i].add(j);expected[j].add(i)
assert relation['neighbors']==[sorted(ns) for ns in expected]
for row in relation['witnesses']:
    i,j,side=row['a'],row['b'],row['side'];a=motifs[i]['cloudM'][side];b=motifs[j]['cloudM'][side];p=row['permutation']
    assert sorted(p)==list(range(len(b['vectors'])))
    assert all(a['colors'][k]==b['colors'][p[k]] for k in range(len(p)))
    assert np.linalg.norm(np.asarray(a['vectors'])-np.asarray(b['vectors'])[p],axis=1).max()<=radius+1e-10
report=dict(libraryHash=sha(source),relationHash=sha(relation_path),verifierHash=sha(Path(__file__)),
            independentAllPairEnumeration=True,assignmentChecks=checks,directedPairs=sum(map(len,expected)),
            witnesses=len(relation['witnesses']),limits='Floating-point declared tolerance; verifies only the explicit one-step substitution hypothesis, not physical validity or transfer.')
with output.open('x') as stream:json.dump(report,stream,indent=2)
print(json.dumps(report))
