"""Frozen six-site dictionary with proper rigid fits and species-preserving maps.

Known-coordinate occurrence registration only; not continuous-pose enumeration.
Greedy first acceptable training representative, maximum site residual 0.05 A.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np
from ase.geometry import find_mic
from scipy.sparse.csgraph import minimum_spanning_tree

EPS=.05

def lift(c,ids):
    p=np.array(c['positions'])[ids];cell=np.array(c['cell'])
    delta=p[None,:,:]-p[:,None,:]
    vectors,lengths=find_mic(delta.reshape(-1,3),cell,pbc=True)
    vectors=vectors.reshape(len(p),len(p),3);lengths=lengths.reshape(len(p),len(p))
    tree=minimum_spanning_tree(lengths).toarray();adj=(tree+tree.T)>0
    out=np.zeros_like(p);done={0};todo=[0];out[0]=p[0]
    while todo:
        a=todo.pop()
        for b in np.flatnonzero(adj[a]):
            if b not in done:out[b]=out[a]+vectors[a,b];done.add(int(b));todo.append(int(b))
    assert len(done)==len(p)
    return out

def maps(species):
    return np.array([p for p in itertools.permutations(range(len(species)))
                     if all(species[i]==species[p[i]] for i in range(len(species)))])

def fit(template,target,perms,epsilon=EPS):
    x=np.asarray(template);y=np.asarray(target)[perms]
    # A necessary condition for any max-point-error <= epsilon rigid fit.
    xd=np.linalg.norm(x[:,None]-x[None,:],axis=2)
    yd=np.linalg.norm(y[:,:,None]-y[:,None,:],axis=3)
    keep=np.max(np.abs(yd-xd),axis=(1,2))<=2*epsilon+1e-12
    y=y[keep];perms=perms[keep]
    if not len(y):return None
    mean=y.mean(axis=1);centered=y-mean[:,None,:]
    u,_,vt=np.linalg.svd(np.einsum('ni,pnj->pij',x,centered))
    fix=np.repeat(np.eye(3)[None],len(y),axis=0);fix[:,2,2]=np.linalg.det(u@vt)
    rotation=u@fix@vt
    residual=np.linalg.norm(x[None]@rotation+mean[:,None,:]-y,axis=2).max(axis=1)
    good=np.flatnonzero(residual<=epsilon)
    if not len(good):return None
    a=int(good[0])
    return {'permutation':perms[a].tolist(),'rotationRow':rotation[a].tolist(),
            'translation':mean[a].tolist(),'residual':float(residual[a])}

if __name__=='__main__':
    raw=Path(sys.argv[1]).read_bytes();corpus=json.loads(raw)['configurations']
    cover_raw=Path(sys.argv[2]).read_bytes();cover=json.loads(cover_raw)
    assert hashlib.sha256(raw).hexdigest()==cover['coordinateHash']
    training=set(cover['trainingIds']);types=[];registered=[]
    for c in sorted(corpus,key=lambda c:(c['id'] not in training,c['id'])):
        witness=next(r for r in cover['results'] if r['id']==c['id'])
        occurrences=[]
        for support in witness['supports']:
            ids=sorted(support,key=lambda i:(c['species'][i],i))
            species=[c['species'][i] for i in ids];positions=lift(c,ids);perms=maps(species)
            found=None
            for t in types:
                if t['species']!=species:continue
                registration=fit(t['positions'],positions,perms)
                if registration is not None:found=(t,registration);break
            if found is None and c['id'] in training:
                center=positions.mean(axis=0)
                t={'id':len(types),'species':species,'positions':(positions-center).tolist(),'trainingOccurrences':0}
                types.append(t);found=(t,{'permutation':list(range(len(ids))),
                    'rotationRow':np.eye(3).tolist(),'translation':center.tolist(),'residual':0.})
            if found is None:
                occurrences.append({'ids':ids,'matched':False});continue
            t,registration=found
            if c['id'] in training:t['trainingOccurrences']+=1
            occurrences.append({'ids':ids,'matched':True,'type':t['id'],**registration})
        summary={'id':c['id'],'training':c['id'] in training,'supports':len(occurrences),
                 'matched':sum(o['matched'] for o in occurrences),'typesSoFar':len(types)}
        print(json.dumps(summary),flush=True);registered.append({**summary,'occurrences':occurrences})
    with open(sys.argv[3],'x') as out:json.dump({'scope':__doc__,'epsilonAngstrom':EPS,
        'coordinateHash':hashlib.sha256(raw).hexdigest(),'coverHash':hashlib.sha256(cover_raw).hexdigest(),
        'sharedWeight':cover['sharedWeight'],'types':types,'configurations':registered},out)
