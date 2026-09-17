"""Independent periodic replay of learned anchors and rationalized t-values.

Checks training and unused calibration frames with supplied original covers.
Does not import the learner or trust its atom correspondence lists.
"""
import hashlib
import itertools
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree

coordp,dictp,libp,resultp,out=map(Path,sys.argv[1:6])
posep=Path(sys.argv[6]) if len(sys.argv)>6 else None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coords,dictionary,library,result=[json.loads(p.read_text()) for p in [coordp,dictp,libp,resultp]]
for p in [coordp,dictp,libp]:assert result['sourceHashes'][p.name]==sha(p)
overrides=None
if posep:
    proposal=json.loads(posep.read_text())
    for p in [coordp,dictp,libp,resultp]:assert proposal['sourceHashes'][p.name]==sha(p)
    overrides={(r['configuration'],r['edge']):r for r in proposal['poses']}
    assert len(overrides)==len(proposal['poses'])
    expected={(r['id'],s['edge']) for r in library['trainingRegistrations'] if r['coverVariant']=='original' for s in r['selected']}
    assert set(overrides)==expected
cc={c['id']:c for c in coords['configurations']};dd={c['id']:c for c in dictionary['configurations']}
anchors=defaultdict(list)
for a in result['anchors']:
    w=Fraction(a['t']).limit_denominator(1000000)
    assert 0<w<=1 and abs(float(w)-a['t'])<=1e-12
    anchors[a['type']].append((a,w))
rows=[]
fitted_types={p['type'] for p in result['poses']}
retired_types=fitted_types-set(anchors)
for reg in library['trainingRegistrations']:
    if reg['coverVariant']!='original':continue
    cid=reg['id'];c=cc[cid];cell=np.asarray(c['cell']);inv=np.linalg.inv(cell)
    tolerance=result['positionTolerance']
    assert np.linalg.svd(cell,compute_uv=False)[-1]>tolerance
    pos=(np.asarray(c['positions'])@inv%1)@cell
    shifts=np.asarray(list(itertools.product([-1,0,1],repeat=3)))@cell
    trees={}
    for species in set(c['species']):
        ids=np.flatnonzero(np.asarray(c['species'])==species)
        cloud=(pos[ids,None,:]+shifts[None,:,:]).reshape(-1,3)
        trees[species]=(cKDTree(cloud),np.repeat(ids,27),cloud)
    totals=[Fraction(0) for _ in pos];bad=0;missing=0;inactive=0;maximum=0.;seen=set()
    for selected in reg['selected']:
        edge=selected['edge'];assert edge not in seen;seen.add(edge)
        pose=dd[cid]['occurrences'][edge]
        if overrides is not None:
            replacement=overrides[cid,edge];assert replacement['type']==pose['type'];pose=replacement
        R=np.asarray(pose['rotationRow']);tr=np.asarray(pose['translation'])
        assert abs(np.linalg.det(R)-1)<1e-8 and np.max(np.abs(R.T@R-np.eye(3)))<1e-8
        if pose['type'] in retired_types:inactive+=1;continue
        if pose['type'] not in anchors:missing+=1;continue
        assigned=set()
        for a,w in anchors[pose['type']]:
            predicted=((np.asarray(a['position'])@R+tr)@inv%1)@cell
            tree,ids,cloud=trees[a['species']]
            hits=tree.query_ball_point(predicted,tolerance+1e-9)
            if len(hits)!=1:bad+=1;continue
            hit=hits[0];atom=int(ids[hit]);assert atom not in assigned;assigned.add(atom)
            totals[atom]+=w;maximum=max(maximum,float(np.linalg.norm(cloud[hit]-predicted)))
    full=sum(v==1 for v in totals);over=sum(v>1 for v in totals)
    training=cid in result['trainingFrames'];valid=bad==0 and missing==0 and full==len(pos)
    if training:assert valid,(cid,bad,missing,full,len(pos),over)
    rows.append(dict(id=cid,training=training,atoms=len(pos),fullyFilled=full,overfilled=over,
                     failedAnchorMappings=bad,missingTypes=missing,retiredOccurrences=inactive,valid=valid,maxErrorAngstrom=maximum))
report=dict(resultHash=sha(resultp),poseHash=sha(posep) if posep else None,codeHash=sha(Path(__file__)),rows=rows,retiredTypes=sorted(retired_types),
            trainingPassed=sum(r['valid'] for r in rows if r['training']),trainingTotal=sum(r['training'] for r in rows),
            calibrationPassed=sum(r['valid'] for r in rows if not r['training']),calibrationTotal=sum(not r['training'] for r in rows),
            limits='Independent source-coordinate matching and exact rational t sums for supplied poses. No m-values or search. Calibration frames were previously seen by upstream geometric dictionary; not fully held-out validation. No certificate of proposal enumeration or cardinality optimality.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
