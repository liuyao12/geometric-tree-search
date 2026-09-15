"""Independent source-coordinate verification of supplied Gaussian-field covers.

Does not import the field producer, its rotation helper, or its image extractor.
Fixed image boxes have per-cell singular-value completeness checks. Verifies
integer t totals and a single coordinate-derived field shared at each anchor.
Numerical residuals are reported; no zero-tolerance/exact real-field claim.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

coordinates,cover_path,dictionary_path,prior_path,library_path,output=map(Path,sys.argv[1:])
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus,cover,dictionary,prior,library=map(read,[coordinates,cover_path,dictionary_path,prior_path,library_path])
assert library['priorLibraryHash']==sha(prior_path)
for name,path in [('coordinates',coordinates),('cover',cover_path),('dictionary',dictionary_path)]:
    assert library['sourceHashes'][name]==sha(path)
assert library['baseMotifs']==prior['baseMotifs'] and library['capacity']==2
R=library['supportRadiusAngstrom'];sigma=library['kernelWidthAngstrom']
assert R>0 and sigma>0
cc={c['id']:c for c in corpus['configurations']};cv={c['id']:c for c in cover['results']};dd={c['id']:c for c in dictionary['configurations']}
images=np.array(list(itertools.product(range(-4,5),repeat=3)))
short=np.array(list(itertools.product(range(-2,3),repeat=3)))
cache={};checked=0;max_error=0.;max_amplitude_error=0.;occurrences={};atom_totals=0;common_values=0
for registration,old in zip(library['trainingRegistrations'],prior['trainingRegistrations'],strict=True):
    assert registration['id']==old['id'] and registration['coverVariant']==old['coverVariant']
    cid=registration['id'];c=cc[cid];v=cv[cid];assert dd[cid]['training'] and all(c.get('pbc',[True]*3))
    if cid not in cache:
        cell=np.array(c['cell']);inv=np.linalg.inv(cell);positions=np.array(c['positions']);smin=np.linalg.svd(cell,compute_uv=False)[-1]
        def mic(d):
            wrapped=d-np.round(d@inv)@cell;options=wrapped+short@cell
            chosen=options[np.argmin(np.linalg.norm(options,axis=1))]
            assert 3*smin-np.linalg.norm(wrapped)>np.linalg.norm(chosen)+1e-10
            return chosen
        expected={}
        for root,ids in enumerate(v['components']):
            # Direct unwrapping is checked against every pair. Thus it cannot
            # silently disagree with the producer's spanning-tree lift.
            lifted=np.array([positions[ids[0]]+mic(positions[i]-positions[ids[0]]) for i in ids])
            for a,i in enumerate(ids):
                for b,j in enumerate(ids):assert np.linalg.norm(lifted[b]-lifted[a]-mic(positions[j]-positions[i]))<1e-9
            center=lifted.mean(axis=0);fractional=(positions-center)@inv
            fractional-=np.round(fractional);wrapped=fractional@cell
            assert 5*smin-max(np.linalg.norm(wrapped,axis=1))>R+1e-10
            points=[];labels=[];weights=[]
            for shift in images@cell:
                x=wrapped+shift
                for i in np.flatnonzero(np.linalg.norm(x,axis=1)<R):
                    points.append(x[i]);labels.append(c['species'][i]);weights.append((1-float(np.dot(x[i],x[i]))/R**2)**3)
            expected[root]=(np.array(points),labels,np.array(weights))
        cache[cid]=expected
        print(json.dumps(dict(verifiedFrame=cid,frames=len(cache))),flush=True)
    total=np.zeros(len(c['positions']),dtype=int);seen=set();root_counts={}
    for placed,previous in zip(registration['selected'],old['selected'],strict=True):
        assert placed['edge']==previous['edge'] and placed['roots']==previous['roots']
        edge=placed['edge'];assert edge not in seen;seen.add(edge)
        o=dd[cid]['occurrences'][edge];assert len(o['ids'])==len(set(o['ids']));total[o['ids']]+=1
        motif=library['motifs'][placed['motif']];assert motif['base']==prior['motifs'][previous['motif']]['base']
        key=(cid,edge)
        if key in occurrences:assert occurrences[key]==placed['motif']
        occurrences[key]=placed['motif']
        atom_of_site=[o['ids'][p] for p in o['permutation']];base=library['baseMotifs'][motif['base']]
        rotation=np.asarray(o['rotationRow']);assert np.max(np.abs(rotation.T@rotation-np.eye(3)))<1e-10 and abs(np.linalg.det(rotation)-1)<1e-10
        for side,root in enumerate(placed['roots']):
            assert {atom_of_site[i] for i in base['componentSites'][side]}==set(v['components'][root])
            value=motif['fieldM'][side];expected,colors,weights=cache[cid][root]
            assert value['sigma']==sigma and len(value['vectors'])==len(expected)
            points=np.asarray(value['vectors'])@rotation
            distances=cdist(points,expected);compatible=np.asarray(value['colors'])[:,None]==np.asarray(colors)[None,:]
            a,b=linear_sum_assignment(np.where(compatible,distances,np.inf))
            error=float(distances[a,b].max());amplitude_error=float(np.max(np.abs(np.asarray(value['amplitudes'])[a]-weights[b])))
            assert error<1e-8 and amplitude_error<1e-10
            max_error=max(max_error,error);max_amplitude_error=max(max_amplitude_error,amplitude_error);checked+=1
            root_counts[root]=root_counts.get(root,0)+1
    assert np.all(total==2) and set(root_counts)==set(range(len(v['components']))) and all(n==2 for n in root_counts.values())
    atom_totals+=len(total);common_values+=len(root_counts)
assert checked==library['summary']['checkedEndpointTransports']
report=dict(scope=__doc__,libraryHash=sha(library_path),verifierHash=sha(Path(__file__)),
            verifiedCovers=len(library['trainingRegistrations']),trainingConfigurations=len(cache),verifiedAssignments=checked,
            commonAnchorFields=common_values,checkedAtomTotals=atom_totals,maxCoordinateResidualAngstrom=max_error,
            maxAmplitudeResidual=max_amplitude_error,coverIndependentOccurrences=len(occurrences),
            limits='Independent positive checks on supplied covers, with inherited anchors/t halves and fixed field parameters. No learned uncertainty radius, proof of forbidden joins, search reconstruction, same-condition certification or transfer.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report),flush=True)
