"""Independent periodic t replay and common-interval m checks."""
import hashlib
import itertools
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree

coordp,dictp,libp,supportp,markp,out=map(Path,sys.argv[1:7])
posep=Path(sys.argv[7]) if len(sys.argv)>7 else None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coords,dictionary,library,support,mark=[json.loads(p.read_text()) for p in [coordp,dictp,libp,supportp,markp]]
assert mark['sourceHashes'][supportp.name]==sha(supportp)
assert mark['radius']==.5 and mark['norm']=='L-infinity Cartesian-product intervals'
for p in [coordp,dictp,libp]:assert support['sourceHashes'][p.name]==sha(p)
overrides=None
if posep:
    proposal=json.loads(posep.read_text())
    for p in [coordp,dictp,libp,supportp]:assert proposal['sourceHashes'][p.name]==sha(p)
    overrides={(r['configuration'],r['edge']):r for r in proposal['poses']}
    expected={(r['id'],s['edge']) for r in library['trainingRegistrations'] if r['coverVariant']=='original' for s in r['selected']}
    assert len(overrides)==len(proposal['poses']) and set(overrides)==expected
cc={c['id']:c for c in coords['configurations']};dd={r['id']:r for r in dictionary['configurations']}
bytype=defaultdict(list)
for i,a in enumerate(support['anchors']):
    w=Fraction(a['t']).limit_denominator(1000000);assert 0<w<=1 and abs(float(w)-a['t'])<1e-12
    bytype[a['type']].append((i,a,w))
retired={p['type'] for p in support['poses']}-set(bytype)
values=[]
for run in mark['runs']:
    V=np.asarray(run['values']);assert V.shape==(len(support['anchors']),run['channels']) and np.all(V==np.rint(V))
    values.append(V.astype(int))
rows=[];training_edges=set();calibration_edges={}
for reg in library['trainingRegistrations']:
    if reg['coverVariant']!='original':continue
    cid=reg['id'];c=cc[cid];cell=np.asarray(c['cell']);inv=np.linalg.inv(cell);tol=support['positionTolerance']
    assert np.linalg.svd(cell,compute_uv=False)[-1]>tol
    pos=(np.asarray(c['positions'])@inv%1)@cell
    shifts=np.asarray(list(itertools.product([-1,0,1],repeat=3)))@cell;trees={}
    for species in set(c['species']):
        ids=np.flatnonzero(np.asarray(c['species'])==species);cloud=(pos[ids,None,:]+shifts[None,:,:]).reshape(-1,3)
        trees[species]=cKDTree(cloud),np.repeat(ids,27)
    at=defaultdict(list);totals=[Fraction(0) for _ in pos];missing=bad=0
    for chosen in reg['selected']:
        o=dd[cid]['occurrences'][chosen['edge']]
        if overrides is not None:
            replacement=overrides[cid,chosen['edge']];assert replacement['type']==o['type'];o=replacement
        R=np.asarray(o['rotationRow']);tr=np.asarray(o['translation'])
        assert np.max(np.abs(R.T@R-np.eye(3)))<1e-8 and abs(np.linalg.det(R)-1)<1e-8
        if o['type'] in retired:continue
        if o['type'] not in bytype:missing+=1;continue
        assigned=set()
        for index,a,w in bytype[o['type']]:
            x=((np.asarray(a['position'])@R+tr)@inv%1)@cell
            tree,ids=trees[a['species']];hits=tree.query_ball_point(x,tol+1e-9)
            if len(hits)!=1:bad+=1;continue
            atom=int(ids[hits[0]]);assert atom not in assigned;assigned.add(atom)
            at[atom].append(index);totals[atom]+=w
    basevalid=missing==0 and bad==0 and all(t==1 for t in totals)
    conflicts=[]
    for V in values:
        # Radius .5 intervals have a common intersection iff max-min <=1
        # in every channel. This checks a common value, not just a chain.
        conflicts.append(sum(bool(np.any(np.ptp(V[group],axis=0)>1)) for group in at.values()))
    training=cid in support['trainingFrames']
    if training:assert basevalid and not any(conflicts),(cid,basevalid,conflicts)
    observed={pair for group in at.values() for pair in itertools.combinations(sorted(set(group)),2)}
    if training:training_edges.update(observed)
    elif basevalid:calibration_edges[cid]=observed
    rows.append(dict(id=cid,training=training,tValid=basevalid,failedMappings=bad,missingTypes=missing,
                     conflictingSitesByRun=conflicts,retainedByRun=[basevalid and count==0 for count in conflicts]))
novel=set().union(*(edges-training_edges for edges in calibration_edges.values()))
novelty=[dict(id=cid,distinctOverlapPairs=len(edges),absentFromTraining=len(edges-training_edges)) for cid,edges in calibration_edges.items()]
summary=[]
for i,r in enumerate(mark['runs']):
    summary.append(dict(channels=r['channels'],trainingPassed=sum(x['retainedByRun'][i] for x in rows if x['training']),
                        trainingTotal=sum(x['training'] for x in rows),
                        calibrationTValid=sum(x['tValid'] for x in rows if not x['training']),
                        calibrationRetained=sum(x['retainedByRun'][i] for x in rows if not x['training']),
                        calibrationTotal=sum(not x['training'] for x in rows)))
report=dict(markingHash=sha(markp),supportHash=sha(supportp),poseHash=sha(posep) if posep else None,verifierHash=sha(Path(__file__)),summary=summary,rows=rows,
            trainingOverlapPairs=len(training_edges),newPairsInTValidCalibration=len(novel),calibrationConnectionNovelty=novelty,
            limits='Independent source-coordinate t and common-box m replay on supplied poses, not tree search. Calibration was already seen by the upstream geometric dictionary. No proof that rejected unobserved connections are invalid or that abstract pair counts are realizable connection counts.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(summary))
