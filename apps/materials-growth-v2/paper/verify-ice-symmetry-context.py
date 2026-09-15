"""Independent base-map enumeration plus direct positive context-witness replay."""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.transform import Rotation
library_path,maps_path,coverage_path,nearest_path,output=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
library,maps,coverage,nearest=[json.loads(p.read_text()) for p in [library_path,maps_path,coverage_path,nearest_path]]
assert maps['libraryHash']==coverage['libraryHash']==nearest['libraryHash']==sha(library_path)
assert coverage['mapsHash']==sha(maps_path) and coverage['nearestHash']==sha(nearest_path)
assert len(maps['results'])==len(library['baseMotifs'])
tested=0;verified=0
for row in maps['results']:
    base=library['baseMotifs'][row['base']];x=np.asarray(base['anchors']);center=x.mean(axis=0);xc=x-center
    expected=set();parts=[set(s) for s in base['componentSites']]
    for p in itertools.permutations(range(len(x))):
        if any(base['species'][i]!=base['species'][j] or base['t'][i]!=base['t'][j] for i,j in enumerate(p)):continue
        if any({p[i] for i in s} not in parts for s in parts):continue
        tested+=1;y=xc[list(p)];rot,_=Rotation.align_vectors(y,xc)
        error=np.linalg.norm(rot.apply(xc)-y,axis=1).max()
        if error<=library['positionToleranceAngstrom']+1e-10:expected.add(tuple(p))
    assert {tuple(m['permutation']) for m in row['maps']}==expected
    for m in row['maps']:
        p=m['permutation'];r=np.asarray(m['rotationRow']);t=np.asarray(m['translation'])
        assert np.max(np.abs(r.T@r-np.eye(3)))<1e-8 and abs(np.linalg.det(r)-1)<1e-8
        error=float(np.linalg.norm(x@r+t-x[p],axis=1).max())
        assert abs(error-m['maxResidualAngstrom'])<1e-8
        assert (error<=1e-8)==m['numericallyExact']
        assert m['endpointMap']==[parts.index({p[i] for i in s}) for s in parts]
        verified+=1
motifs=library['motifs'];frames=defaultdict(set)
for row in library['trainingRegistrations']:
    for p in row['selected']:frames[p['motif']].add(row['id'])
initial={r['motif'] for r in nearest['results'] if r['distanceAngstrom'] is not None and r['distanceAngstrom']<=library['markingRadiusAngstrom']+1e-10}
new=set()
for w in coverage['witnesses']:
    i,j=w['motif'],w['donor'];assert i not in initial|new and not frames[i]&frames[j];new.add(i)
    assert motifs[i]['base']==motifs[j]['base']==w['base']
    pose=maps['results'][w['base']]['maps'][w['pose']];target=w['endpoint'];source=pose['endpointMap'].index(target)
    a=motifs[i]['cloudM'][target];b=motifs[j]['cloudM'][source];r=np.asarray(pose['rotationRow']);p=w['fit']['permutation']
    assert sorted(p)==list(range(len(b['vectors'])))
    assert all(a['colors'][k]==b['colors'][p[k]] for k in range(len(p)))
    residual=np.linalg.norm(np.asarray(a['vectors'])-(np.asarray(b['vectors'])@r)[p],axis=1).max()
    assert residual<=library['markingRadiusAngstrom']+1e-10
    assert abs(residual-w['fit']['maxResidual'])<1e-8
assert len(new)==coverage['summary']['additionalCovered']
assert len(initial)==coverage['summary']['originalCovered']
assert len(new|initial)==coverage['summary']['totalCovered']
report=dict(libraryHash=sha(library_path),mapsHash=sha(maps_path),coverageHash=sha(coverage_path),nearestHash=sha(nearest_path),
            verifierHash=sha(Path(__file__)),independentlyEnumeratedPermutations=tested,verifiedMaps=verified,
            verifiedAdditionalContexts=len(new),summary=coverage['summary'],
            limits='Numerical Procrustes proposal enumeration, not continuous max-error feasibility. Directly checks every additional positive witness; does not certify absence of further context matches. No search or physical validity conclusion.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
