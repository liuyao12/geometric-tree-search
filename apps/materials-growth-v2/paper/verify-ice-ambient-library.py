"""Replay ambient markings against source atoms without the ambient constructor.

Independent minimum-image proposals enumerate a 5x5x5 image neighborhood
around fractional wrapping. Checks cover the supplied bounded ice cells only,
not arbitrary skew-cell closest-vector completeness. Exact t uses integer halves.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np
coordinates,cover_path,dictionary_path,prior_path,library_path,output=map(Path,sys.argv[1:])
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus,cover,dictionary,prior,library=map(read,[coordinates,cover_path,dictionary_path,prior_path,library_path])
assert library['priorLibraryHash']==sha(prior_path)
assert library['sourceHashes']['coordinates']==sha(coordinates)
assert library['sourceHashes']['cover']==sha(cover_path) and library['sourceHashes']['dictionary']==sha(dictionary_path)
assert library['baseMotifs']==prior['baseMotifs']
cc={c['id']:c for c in corpus['configurations']};cv={c['id']:c for c in cover['results']};dd={c['id']:c for c in dictionary['configurations']}
images=np.array(list(itertools.product(range(-2,3),repeat=3)));cache={};checked=0;max_error=0.;occurrences={};totals_checked=0
for registration,old in zip(library['trainingRegistrations'],prior['trainingRegistrations'],strict=True):
    assert registration['id']==old['id'] and registration['coverVariant']==old['coverVariant']
    cid=registration['id'];c=cc[cid];v=cv[cid];assert dd[cid]['training']
    if cid not in cache:
        cell=np.array(c['cell']);inv=np.linalg.inv(cell);positions=np.array(c['positions']);shifts=images@cell
        def mic(d):
            wrapped=d-np.round(d@inv)@cell;options=wrapped+shifts
            return options[np.argmin(np.linalg.norm(options,axis=1))]
        groups=[];center=[];local=[];labels=[]
        for part in v['components']:
            ids=sorted(part,key=lambda i:(c['species'][i],i));x=np.array([positions[ids[0]]+mic(positions[i]-positions[ids[0]]) for i in ids])
            groups.append(ids);center.append(x.mean(axis=0));local.append(x-x.mean(axis=0));labels.append([c['species'][i] for i in ids])
        neighbors=[set() for _ in groups]
        for a,b in v['componentPairs']:neighbors[a].add(b);neighbors[b].add(a)
        expected={}
        for root in range(len(groups)):
            ns=sorted(neighbors[root],key=lambda i:(labels[i],i))
            points=np.vstack([local[root],*[local[i]+mic(center[i]-center[root]) for i in ns]])
            colors=[[0,s] for s in labels[root]]+[[1,s] for i in ns for s in labels[i]]
            expected[root]=(points,colors)
        cache[cid]=expected
    total=np.zeros(len(c['positions']),dtype=int);seen=set()
    for placed,previous in zip(registration['selected'],old['selected'],strict=True):
        assert placed['edge']==previous['edge'] and placed['roots']==previous['roots']
        edge=placed['edge'];assert edge not in seen;seen.add(edge)
        o=dd[cid]['occurrences'][edge];total[o['ids']]+=1
        motif=library['motifs'][placed['motif']];assert motif['base']==prior['motifs'][previous['motif']]['base']
        key=(cid,edge)
        if key in occurrences:assert occurrences[key]==placed['motif']
        occurrences[key]=placed['motif']
        atom_of_site=[o['ids'][p] for p in o['permutation']];base=library['baseMotifs'][motif['base']]
        for side,root in enumerate(placed['roots']):
            assert {atom_of_site[i] for i in base['componentSites'][side]}==set(v['components'][root])
            value=motif['cloudM'][side];expected,colors=cache[cid][root]
            assert value['colors']==colors
            error=float(np.linalg.norm(np.asarray(value['vectors'])@np.asarray(o['rotationRow'])-expected,axis=1).max())
            assert error<=1e-8;max_error=max(max_error,error);checked+=1
    assert np.all(total==2);totals_checked+=len(total)
assert checked==library['summary']['verifiedTransportAssignments']
report=dict(scope=__doc__,libraryHash=sha(library_path),priorLibraryHash=sha(prior_path),verifierHash=sha(Path(__file__)),
            verifiedCovers=len(library['trainingRegistrations']),verifiedAssignments=checked,checkedAtomTotals=totals_checked,
            maxCoordinateResidualAngstrom=max_error,coverIndependentOccurrences=len(occurrences),summary=library['summary'],
            limits='Supplied-cover positive verification only. Reconstructs geometric neighbor clouds from source positions; no search, transfer, negative-rule or arbitrary-cell guarantee.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
