"""Verify cross-frame nearest distances using independent bipartite matching.

Enumerates every same-base candidate with a signature lower bound capable of
beating the reported distance. Checks minimality within 1e-8 Angstrom, not an
exact-real certificate. The compiler's nearest-neighbor traversal is not used.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist

source,result_path,output=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('cloud',Path(__file__).with_name('portable-cloud-markings.py'))
cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)
library=json.loads(source.read_text());report=json.loads(result_path.read_text());assert report['libraryHash']==sha(source)
motifs=library['motifs'];frames=defaultdict(set);groups=defaultdict(list)
for row in library['trainingRegistrations']:
    for p in row['selected']:frames[p['motif']].add(row['id'])
for i,m in enumerate(motifs):groups[m['base']].append(i)
assert [r['motif'] for r in report['results']]==list(range(len(motifs)))
checks=0;missing=0
for base,ids in groups.items():
    lower=np.full((len(ids),len(ids)),np.inf)
    for side in range(2):
        buckets=defaultdict(list);features={}
        for local,i in enumerate(ids):
            c=motifs[i]['cloudM'][side];parts=defaultdict(list)
            for label,v in zip(c['colors'],c['vectors'],strict=True):parts[json.dumps(label,sort_keys=True)].append(v)
            layout=tuple((k,len(parts[k])) for k in sorted(parts));buckets[layout].append(local)
            features[local]=np.concatenate([np.sort(parts[k],axis=0).T.ravel() for k in sorted(parts)])
        for local_ids in buckets.values():
            x=np.array([features[i] for i in local_ids]);at=np.ix_(local_ids,local_ids)
            lower[at]=np.minimum(lower[at],cdist(x,x,metric='chebyshev'))
    for local,i in enumerate(ids):
        row=report['results'][i];best=row['distanceAngstrom'];j=row['neighbor']
        assert row['base']==base and row['sourceFrames']==sorted(frames[i])
        eligible=[k for k,other in enumerate(ids) if not frames[i]&frames[other]]
        if best is None:
            missing+=1;assert j is None and not row['neighborFrames']
            assert all(not np.isfinite(lower[local,k]) for k in eligible)
            continue
        assert j in ids and not frames[i]&frames[j] and row['neighborFrames']==sorted(frames[j])
        assert any(cloud.contains(motifs[i]['cloudM'][s],motifs[j]['cloudM'][s],best) is not None for s in range(2))
        if best<=1e-8:continue
        for k in eligible:
            if lower[local,k]>best+1e-8:continue
            other=ids[k];checks+=1
            assert all(cloud.contains(motifs[i]['cloudM'][s],motifs[other]['cloudM'][s],best-1e-8) is None for s in range(2)), 'Closer eligible context exists'
finite=[r['distanceAngstrom'] for r in report['results'] if r['distanceAngstrom'] is not None]
assert report['summary']['noCrossFrameContext']==missing
assert report['summary']['withinExistingTolerance']==sum(d<=library['markingRadiusAngstrom']+1e-10 for d in finite)
for q,value in report['summary']['quantilesAngstrom'].items():assert abs(value-float(np.quantile(finite,float(q))))<1e-12
result=dict(libraryHash=sha(source),reportHash=sha(result_path),verifierHash=sha(Path(__file__)),
            verifiedContexts=len(motifs),minimalityToleranceAngstrom=1e-8,eligibleComparisons=checks,summary=report['summary'],
            limits=__doc__+' Does not refit the dictionary or certify scientific transfer.')
with output.open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
