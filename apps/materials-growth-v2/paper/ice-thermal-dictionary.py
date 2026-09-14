"""Thermal six-site motifs: proper-rotation registration and shared t/m precheck.

Known-coordinate, all-proposed-occurrences experiment. Pose matching is a
witness heuristic, not complete continuous enumeration. No growth claim.
"""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
from fractions import Fraction
from collections import Counter
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix,hstack

spec=importlib.util.spec_from_file_location('dictionary',Path(__file__).with_name('ice-motif-dictionary.py'))
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)

def run(coordinates,cover_path,epsilon,output):
    raw=Path(coordinates).read_bytes();cover_raw=Path(cover_path).read_bytes()
    corpus=json.loads(raw)['configurations'];cover=json.loads(cover_raw)
    assert hashlib.sha256(raw).hexdigest()==cover['coordinateHash']
    train=set(cover['trainingIds']);covers={c['id']:c for c in cover['results']}
    types=[];descriptors=[];configs=[];perm_cache={}
    for c in sorted(corpus,key=lambda c:(c['id'] not in train,c['id'])):
        occ=[]
        for support in covers[c['id']]['supports']:
            ids=sorted(support,key=lambda i:(c['species'][i],i));species=tuple(c['species'][i] for i in ids)
            positions=lib.lift(c,ids);n=len(ids);upper=np.triu_indices(n,1)
            descriptor=np.sort(np.linalg.norm(positions[:,None]-positions[None,:],axis=2)[upper])
            if species not in perm_cache:perm_cache[species]=lib.maps(species)
            possible=np.flatnonzero(np.max(np.abs(np.array(descriptors)-descriptor),axis=1)<=2*epsilon+1e-10) if descriptors else []
            found=None
            for ti in possible:
                t=types[ti]
                if tuple(t['species'])!=species:continue
                fit=lib.fit(t['positions'],positions,perm_cache[species],epsilon)
                if fit is not None:found=(int(ti),fit);break
            if found is None and c['id'] in train:
                center=positions.mean(axis=0);ti=len(types)
                types.append({'species':list(species),'positions':(positions-center).tolist(),'trainingOccurrences':0})
                descriptors.append(descriptor)
                found=(ti,{'permutation':list(range(n)),'rotationRow':np.eye(3).tolist(),'translation':center.tolist(),'residual':0.})
            if found is None:occ.append({'ids':ids,'matched':False});continue
            ti,fit=found
            if c['id'] in train:types[ti]['trainingOccurrences']+=1
            occ.append({'ids':ids,'matched':True,'type':ti,**fit})
        configs.append({'id':c['id'],'training':c['id'] in train,'atoms':len(c['positions']),'occurrences':occ})
        print(json.dumps({'id':c['id'],'types':len(types),'matched':sum(o['matched'] for o in occ),'proposals':len(occ)}),flush=True)
    # Shared site variables; no per-occurrence weights or normalization.
    offsets=np.cumsum([0]+[len(t['species']) for t in types]).tolist();nv=offsets[-1]
    rows=[];cols=[];row=0;parent=list(range(nv))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for c in configs:
        if not c['training']:continue
        incidence=[[] for _ in range(c['atoms'])]
        for o in c['occurrences']:
            for u,j in enumerate(o['permutation']):incidence[o['ids'][j]].append(offsets[o['type']]+u)
        for sites in incidence:
            rows.extend([row]*len(sites));cols.extend(sites);row+=1
            for site in sites[1:]:parent[root(site)]=root(sites[0])
    A=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(row,nv)).tocsr()
    # Maximize smallest site weight, with all t in [0,1].
    from scipy.sparse import eye
    result=linprog(np.r_[np.zeros(nv),-1],A_ub=hstack([-eye(nv),np.ones((nv,1))]),b_ub=np.zeros(nv),
        A_eq=hstack([A,np.zeros((row,1))]),b_eq=np.ones(row),bounds=[(0,1)]*(nv+1),method='highs')
    weights=[Fraction(float(x)).limit_denominator(4096) for x in result.x[:nv]] if result.success else None
    exact=weights is not None and all(sum((weights[int(j)]*int(v) for j,v in zip(A.indices[A.indptr[i]:A.indptr[i+1]],A.data[A.indptr[i]:A.indptr[i+1]])),Fraction())==1 for i in range(row))
    labels=[root(i) for i in range(nv)];summary=[]
    for c in configs:
        totals=[Fraction() for _ in range(c['atoms'])];marks={};conflicts=0
        for o in c['occurrences']:
            if not o['matched']:continue
            for u,j in enumerate(o['permutation']):
                p=o['ids'][j];site=offsets[o['type']]+u
                if weights is not None:totals[p]+=weights[site]
                if p in marks and marks[p]!=labels[site]:conflicts+=1
                marks[p]=labels[site]
        summary.append({'id':c['id'],'training':c['training'],'atoms':c['atoms'],'proposals':len(c['occurrences']),
            'matched':sum(o['matched'] for o in c['occurrences']),'exactlyFilledAtoms':sum(x==1 for x in totals) if exact else None,
            'markConflictIncidences':conflicts})
    out={'scope':__doc__,'epsilonAngstrom':epsilon,'coordinateHash':hashlib.sha256(raw).hexdigest(),
         'coverHash':hashlib.sha256(cover_raw).hexdigest(),'types':types,'configurations':configs,'offsets':offsets,
         'filling':{'solverStatus':int(result.status),'message':result.message,'exactTrainingEquations':exact,
                    'minimumWeight':str(min(weights)) if weights else None,'weights':[str(x) for x in weights] if weights else None},
         'scalarLabels':labels,'scalarClasses':len(set(labels)),
         'typeCount':len(types),'singletonTypes':sum(t['trainingOccurrences']==1 for t in types),'summary':summary}
    with Path(output).open('x') as f:json.dump(out,f)
    print(json.dumps({k:out[k] for k in ('typeCount','singletonTypes','scalarClasses','filling')}),flush=True)

if __name__=='__main__':run(sys.argv[1],sys.argv[2],float(sys.argv[3]),sys.argv[4])
