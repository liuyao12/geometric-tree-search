"""Geometry-only union-of-components proposal with a shared weight diagnostic.

Not a motif dictionary: one common weight is a restricted hypothesis across all
proposed unions; their rigid-isometry classification is a subsequent gate.
"""
from fractions import Fraction
import json
import sys
from pathlib import Path
import numpy as np
from ase import Atoms
from scipy.sparse.csgraph import connected_components


def prepare(c, threshold):
    atoms=Atoms(c['species'],positions=c['positions'],cell=c['cell'],pbc=True)
    distances=atoms.get_all_distances(mic=True);np.fill_diagonal(distances,np.inf)
    n,labels=connected_components(distances<threshold,directed=False)
    parts=[np.flatnonzero(labels==i).tolist() for i in range(n)]
    cross=np.full((n,n),np.inf)
    for i in range(n):
        for j in range(i+1,n):
            cross[i,j]=cross[j,i]=np.min(distances[np.ix_(parts[i],parts[j])])
    return parts,cross


if __name__=='__main__':
    raw=Path(sys.argv[1]).read_bytes();corpus=json.loads(raw)['configurations']
    prior=json.loads(Path(sys.argv[2]).read_text());training=set(prior['trainingIds'])
    prepared={c['id']:prepare(c,prior['threshold']) for c in corpus}
    nearest=np.concatenate([d.min(axis=1) for key,(_,d) in prepared.items() if key in training])
    scale=float(np.median(nearest))
    # Freeze on training data, never prescribe a coordination number or bond type.
    candidates=np.sort(np.concatenate([d[d<1.5*scale] for key,(_,d) in prepared.items() if key in training]))
    gap=int(np.argmax(np.diff(candidates)))
    threshold=float((candidates[gap]+candidates[gap+1])/2)
    strategy=sys.argv[4] if len(sys.argv)>4 else 'largest-gap'
    assert strategy in ('largest-gap','first-common-regular','radius-upper')
    if strategy=='radius-upper':
        # Explicit broader geometric proposal pool, not a learned connection rule.
        threshold=1.5*scale
    if strategy=='first-common-regular':
        # A declared hypothesis-selection control, not a chemical degree rule.
        # Enumerate training distance events; select the earliest connected cover
        # admitting a common positive symmetric weight. Never inspect test degrees.
        train_arrays=[d for key,(_,d) in prepared.items() if key in training]
        degrees=[np.zeros(len(d),dtype=int) for d in train_arrays]
        events=sorted((float(d[i,j]),f,i,j) for f,d in enumerate(train_arrays)
                      for i in range(len(d)) for j in range(i+1,len(d)) if d[i,j]<1.5*scale)
        index=0;selected=None
        while index<len(events):
            value=events[index][0]
            while index<len(events) and events[index][0]==value:
                _,f,i,j=events[index];degrees[f][i]+=1;degrees[f][j]+=1;index+=1
            flat=np.concatenate(degrees)
            if flat.min()>0 and np.all(flat==flat[0]):
                proposed=(value+(events[index][0] if index<len(events) else 1.5*scale))/2
                if all(connected_components(d<proposed,directed=False)[0]==1 for d in train_arrays):
                    selected=proposed;break
        if selected is None:
            failure={'status':'no common regular connected training cover in enumerated radius range',
                     'scope':'uniform weight over all proposed unions only; not a general t infeasibility claim',
                     'radiusUpperBound':1.5*scale,'distanceEvents':len(events),'trainingIds':sorted(training)}
            with open(sys.argv[3],'x') as out:json.dump(failure,out,indent=2)
            print(json.dumps(failure));sys.exit(0)
        threshold=selected
    all_rows=[];results=[]
    for c in corpus:
        parts,cross=prepared[c['id']]
        pairs=[[i,j] for i in range(len(parts)) for j in range(i+1,len(parts)) if cross[i,j]<threshold]
        degrees=[sum(i in p for p in pairs) for i in range(len(parts))]
        if c['id'] in training:all_rows.extend(degrees)
        unions=[sorted(parts[i]+parts[j]) for i,j in pairs]
        n,labels=connected_components(cross<threshold,directed=False)
        results.append({'id':c['id'],'components':parts,'componentPairs':pairs,
                        'supports':unions,'degrees':degrees,'positiveOverlapComponents':int(n)})
    # Exact shared equation d*w=1; no occurrence-dependent renormalization.
    weight=Fraction(1,all_rows[0]) if all_rows and all_rows[0]>0 and len(set(all_rows))==1 else None
    for c,r in zip(corpus,results):
        totals=[Fraction(0) for _ in c['positions']]
        if weight is not None:
            for support in r['supports']:
                for p in support:totals[p]+=weight
        r['exactFilling']=weight is not None and all(t==1 for t in totals)
        r['filledAtoms']=sum(t==1 for t in totals)
        print(json.dumps({'id':r['id'],'supports':len(r['supports']),
              'componentDegreeCounts':{str(d):r['degrees'].count(d) for d in set(r['degrees'])},
              'weight':str(weight),'exactFilling':r['exactFilling'],
              'positiveOverlapComponents':r['positiveOverlapComponents']}),flush=True)
    import hashlib
    with open(sys.argv[3],'x') as out:
        json.dump({'scope':__doc__,'coordinateHash':hashlib.sha256(raw).hexdigest(),
            'trainingIds':sorted(training),'componentThreshold':prior['threshold'],
            'thresholdStrategy':strategy,
            'interfaceThreshold':threshold,'interfaceGap':[float(candidates[gap]),float(candidates[gap+1])],
            'sharedWeight':str(weight) if weight is not None else None,'results':results},out,indent=2)
