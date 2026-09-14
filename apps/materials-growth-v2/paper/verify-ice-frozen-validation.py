"""Independent periodic-image candidate reconstruction and frozen-pose audit."""
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from itertools import product
import sys
import numpy as np
from scipy.spatial import cKDTree

folder=Path(sys.argv[1]);d=json.loads((folder/'dictionary.json').read_text());coords=json.loads((folder/'coordinates.json').read_text())['configurations']
cover=json.loads((folder/'cover.json').read_text());byid={c['id']:c for c in cover['results']}
original_cover=json.loads(Path(sys.argv[5]).read_text());source_folder=Path(sys.argv[6])
assert cover['componentThreshold']==original_cover['componentThreshold'] and cover['interfaceThreshold']==original_cover['interfaceThreshold']
source_meta=json.loads((source_folder/'provenance.json').read_text())['configurations']
expected_meta=[c for c in source_meta if c['split']=='test' and c['sourceFrame']>=25]
assert json.loads((folder/'provenance.json').read_text())['configurations']==expected_meta
source_coordinates={c['id']:c for c in json.loads((source_folder/'coordinates.json').read_text())['configurations']}
assert len(coords)==300 and {c['id'] for c in coords}=={c['id'] for c in expected_meta}
assert all(c==source_coordinates[c['id']] for c in coords)
prior_raw=Path(sys.argv[2]).read_bytes();prior=json.loads(prior_raw);wraw=Path(sys.argv[3]).read_bytes();w=json.loads(wraw)
assert d['sourceDictionaryHash']==hashlib.sha256(prior_raw).hexdigest() and d['weightCertificateHash']==hashlib.sha256(wraw).hexdigest()
assert d['types']==prior['types'] and d['offsets']==prior['offsets'] and d['epsilonAngstrom']==prior['epsilonAngstrom']
assert d['coordinateHash']==hashlib.sha256((folder/'coordinates.json').read_bytes()).hexdigest()
assert d['coverHash']==hashlib.sha256((folder/'cover.json').read_bytes()).hexdigest()
forced={s for c in w['components'] if c['kind']=='forced-half' for s in c['sites']}
assert d['admittedTypeIds']==[i for i,(a,b) in enumerate(zip(d['offsets'],d['offsets'][1:])) if set(range(a,b))<=forced]
assert not({c['id'] for c in coords}&{c['id'] for c in prior['configurations']})
registered={c['id']:c for c in d['configurations']};images=np.array(list(product((-1,0,1),repeat=3)));matched=0;proposed=0;maxres=0
for c in coords:
    r=registered[c['id']];source=byid[c['id']];cell=np.array(c['cell']);inv=np.linalg.inv(cell);pos=(np.array(c['positions'])@inv%1)@cell;n=len(pos)
    radius=cover['interfaceThreshold'];assert radius<np.linalg.svd(cell,compute_uv=False).min()
    copies=(pos[None,:,:]+(images@cell)[:,None,:]).reshape(-1,3);tree=cKDTree(copies);parent=list(range(n));near=[]
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,neighbors in enumerate(tree.query_ball_point(pos,radius)):
        for j in neighbors:
            k=j%n
            if i==k:continue
            dist=np.linalg.norm(pos[i]-copies[j])
            if dist<radius:near.append((i,k))
            if dist<cover['componentThreshold']:parent[root(i)]=root(k)
    groups=defaultdict(list)
    for i in range(n):groups[root(i)].append(i)
    parts=sorted(groups.values(),key=min);assert parts==source['components'];component={p:i for i,part in enumerate(parts) for p in part}
    pairs=sorted({tuple(sorted((component[i],component[j]))) for i,j in near if component[i]!=component[j]})
    assert [list(x) for x in pairs]==source['componentPairs']
    supports=[sorted(parts[a]+parts[b]) for a,b in pairs];assert supports==source['supports']
    assert [sorted(o['ids']) for o in r['occurrences']]==supports and not r['training']
    proposed+=len(supports)
    for o in r['occurrences']:
        if not o['matched']:continue
        assert o['type'] in d['admittedTypeIds'];t=d['types'][o['type']];R=np.array(o['rotationRow']);perm=o['permutation'];assert sorted(perm)==list(range(6))
        assert np.allclose(R.T@R,np.eye(3),atol=1e-10) and abs(np.linalg.det(R)-1)<1e-10
        target=[o['ids'][j] for j in perm];delta=(np.array(t['positions'])@R+o['translation']-np.array(c['positions'])[target])@inv
        error=float(np.linalg.norm((delta-np.rint(delta))@cell,axis=1).max());assert error<=d['epsilonAngstrom']+1e-9
        assert t['species']==[c['species'][i] for i in target];maxres=max(maxres,error);matched+=1
assert proposed==d['summary']['proposals'] and matched==d['summary']['matched']
out={'verifiedConfigurations':len(coords),'admittedTypes':len(d['admittedTypeIds']),'proposedOccurrences':proposed,
 'verifiedRigidOccurrences':matched,'maximumResidualAngstrom':maxres,'trainingOverlap':False,
 'scope':'Frozen candidate registration on remaining author validation frames; not independent trajectories or free growth.'}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
