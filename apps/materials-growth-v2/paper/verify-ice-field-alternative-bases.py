"""Independent positive periodic-position and field check of alternative bases.

Enumerates independent bounded periodic images, checks their cell bounds, and
evaluates a signed Gaussian quadratic form in world coordinates. Does not prove
absence of alternatives or completeness of the producer's Procrustes proposals.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import numpy as np

coordinates,cover_path,dictionary_path,library_path,transfer_path,rescue_path,prior_check_path,output=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus,cover,dictionary,library,transfer,rescue,priorcheck=[json.loads(p.read_text()) for p in [coordinates,cover_path,dictionary_path,library_path,transfer_path,rescue_path,prior_check_path]]
for path in [coordinates,cover_path,dictionary_path,library_path,transfer_path]:assert rescue['sourceHashes'][path.name]==sha(path)
assert priorcheck['resultHash']==sha(transfer_path) and priorcheck['libraryHash']==sha(library_path)
cc={c['id']:c for c in corpus['configurations']};cv={c['id']:c for c in cover['results']};dd={c['id']:c for c in dictionary['configurations']};tt={c['id']:c for c in transfer['results']}
allowed={p['motif'] for reg in library['trainingRegistrations'] if reg['id'] in transfer['fitFrames'] for p in reg['selected']}
images=np.array(list(itertools.product(range(-4,5),repeat=3)));checked=0;maxpos=0.;maxfield=0.;complete=0
assert [r['id'] for r in rescue['results']]==[r['id'] for r in transfer['results'] if r['split']=='developmental']
for row in rescue['results']:
    cid=row['id'];c=cc[cid];old=tt[cid];assert old['split']=='developmental'
    failures=[w['edge'] for w in old['matches'] if w['radius'] is None or w['radius']>transfer['summary']['diagnosticThreshold']]
    assert [a['edge'] for a in row['repairs']]==failures
    pos=np.asarray(c['positions']);cell=np.asarray(c['cell']);inv=np.linalg.inv(cell);smin=np.linalg.svd(cell,compute_uv=False)[-1];shifts=images@cell
    assert all(c.get('pbc',[True]*3));cache={};success=0
    def mic(delta):
        wrapped=delta-np.round(delta@inv)@cell;options=wrapped+shifts;v=options[np.argmin(np.linalg.norm(options,axis=1))]
        assert 5*smin-np.linalg.norm(wrapped)>np.linalg.norm(v)+1e-10
        return v
    for attempt in row['repairs']:
        w=attempt['witness']
        if w is None:continue
        assert w['motif'] in allowed
        m=library['motifs'][w['motif']];assert m['base']==w['base'];b=library['baseMotifs'][w['base']];o=dd[cid]['occurrences'][attempt['edge']]
        assert b['t']==[1]*len(o['ids']) and set(w['roots'])==set(cv[cid]['componentPairs'][attempt['edge']]) and len(w['roots'])==2
        perm=w['permutation'];assert sorted(perm)==list(range(len(o['ids'])))
        atoms=[o['ids'][j] for j in perm];assert [c['species'][a] for a in atoms]==b['species']
        R=np.asarray(w['rotationRow']);assert np.max(np.abs(R.T@R-np.eye(3)))<1e-10 and abs(np.linalg.det(R)-1)<1e-10
        pred=np.asarray(b['anchors'])@R+w['translation'];err=max(np.linalg.norm(mic(pred[j]-pos[a])) for j,a in enumerate(atoms));assert err<=library['positionToleranceAngstrom']+1e-9;maxpos=max(maxpos,float(err))
        for side,root in enumerate(w['roots']):
            ids=cv[cid]['components'][root];assert {atoms[j] for j in b['componentSites'][side]}==set(ids)
            if root not in cache:
                lifted=np.array([pos[ids[0]]+mic(pos[a]-pos[ids[0]]) for a in ids]);center=lifted.mean(axis=0)
                for j,a in enumerate(ids):
                    for k,bb in enumerate(ids):assert np.linalg.norm(lifted[k]-lifted[j]-mic(pos[bb]-pos[a]))<1e-9
                frac=(pos-center)@inv;frac-=np.round(frac);wrapped=frac@cell;assert 5*smin-max(np.linalg.norm(wrapped,axis=1))>4+1e-10
                x=[];labels=[];amps=[]
                for shift in shifts:
                    points=wrapped+shift
                    for j in np.flatnonzero(np.linalg.norm(points,axis=1)<4):
                        x.append(points[j]);labels.append(c['species'][j]);amps.append((1-float(np.dot(points[j],points[j]))/16)**3)
                cache[root]=(x,labels,amps)
            x,labels,amps=cache[root];v=m['fieldM'][side];assert v['sigma']==.4
            points=np.vstack([np.asarray(v['vectors'])@R,x]);weights=np.r_[v['amplitudes'],-np.asarray(amps)];colors=np.r_[v['colors'],labels]
            d=points[:,None,:]-points[None,:,:];terms=weights[:,None]*weights[None,:]*np.exp(-np.sum(d*d,axis=2)/.32)*(colors[:,None]==colors[None,:])
            squared=math.fsum(map(float,terms.ravel()));assert squared>=-1e-10
            distance=math.sqrt(max(0.,squared));assert abs(distance-w['endpointDistances'][side])<1e-8 and distance<=transfer['summary']['diagnosticThreshold'];maxfield=max(maxfield,distance);checked+=1
        success+=1
    assert row['rescued']==success and row['accepted']==old['accepted']+success and row['complete']==(row['accepted']==old['occurrences'])
    complete+=row['complete']
assert checked==2*rescue['summary']['rescued'] and complete==rescue['summary']['complete']
report=dict(scope=__doc__,rescueHash=sha(rescue_path),priorWitnessCheckHash=sha(prior_check_path),libraryHash=sha(library_path),verifierHash=sha(Path(__file__)),
            rescuedOccurrences=checked//2,checkedEndpointFields=checked,completeCoverWitnesses=complete,maxPeriodicPositionErrorAngstrom=maxpos,maxEndpointFieldDistance=maxfield,
            limits='Positive composed witnesses only. Failure absence and all-continuous-pose completeness not verified. Retains broad ineffective-pruning field radius. No search reconstruction, negative specificity or condition provenance claim.')
with output.open('x') as out:json.dump(report,out,indent=2)
print(json.dumps(report))
