"""Training-selected occurrences with a shared reciprocal-weight hypothesis.

Choose the smallest feasible k from (2,3,4,6,12), using five training inputs
only; every site of every motif has t=1/k. Require binary selected occurrences
to give integer incidence k at every atom. Test the frozen hypothesis on the
held-out finite alternative-match pool. Unmarked MILP control, not base GCTS.
"""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

def selection(c,k):
    rows=[];cols=[];seen=set();pool=[]
    # Uniform scalar t and no marking: within a template, site permutations
    # have the same point function in this target-ID model.
    for original,o in enumerate(c['occurrences']):
        key=(o['type'],tuple(sorted(o['ids'])))
        if key in seen:continue
        seen.add(key);pool.append(original)
        rows.extend(o['ids']);cols.extend([len(pool)-1]*3)
    n=c['atoms']
    if (n*k)%3:return {'status':'exact divisibility obstruction','selected':[]}
    counts=np.bincount(rows,minlength=n)
    if np.any(counts<k):return {'status':'exact incidence obstruction','selected':[]}
    A=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,len(pool))).tocsc()
    started=time.monotonic()
    fit=milp(np.zeros(len(pool)),integrality=np.ones(len(pool)),bounds=Bounds(0,1),
        constraints=LinearConstraint(A,k,k),options={'time_limit':30,'mip_rel_gap':0})
    out={'status':'unknown','solverStatus':fit.message,'seconds':time.monotonic()-started,'selected':[]}
    if fit.x is None:
        out['status']='numerical restricted infeasibility' if fit.status==2 else 'unknown: budget';return out
    chosen=np.flatnonzero(fit.x>.5);exact=np.zeros(n,dtype=int)
    parent=list(range(n))
    def root(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for j in chosen:
        ids=c['occurrences'][pool[j]]['ids'];exact[ids]+=1
        for p in ids[1:]:parent[root(p)]=root(ids[0])
    out['selected']=[pool[j] for j in chosen]
    out['status']='exact integer coverage witness' if np.all(exact==k) else 'unknown: integer verification failed'
    out['positiveComponents']=len({root(i) for i in range(n)})
    return out

def run(args):
    folder,pools,destination,i=args
    raw=(Path(folder)/str(i)/'training-dictionary.json').read_bytes();d=json.loads(raw)
    trials=[];chosen=None
    for k in (2,3,4,6,12):
        # A cheap exact necessary test over every training configuration.
        if any((c['atoms']*k)%3 for c in d['configurations']):
            trials.append({'k':k,'status':'exact training divisibility obstruction'});continue
        fits=[{'file':c['file'],**selection(c,k)} for c in d['configurations']]
        passed=all(r['status']=='exact integer coverage witness' for r in fits)
        trials.append({'k':k,'status':'training passed' if passed else 'training unresolved','fits':fits})
        if passed:chosen=k;break
    # Read held-out pool only after selecting the training hypothesis.
    pool_raw=(Path(pools)/f'{i}.json').read_bytes();pool=json.loads(pool_raw)
    assert pool['frozenDictionaryHash']==hashlib.sha256(raw).hexdigest()
    result=selection(pool['testConfiguration'],chosen) if chosen else {'status':'training unresolved','selected':[]}
    summary={'heldOut':pool['summary']['heldOut'],'learnedDenominator':chosen,
        'testStatus':result['status'],'selected':len(result['selected']),
        'positiveComponents':result.get('positiveComponents'),'markingsTested':False}
    out={'scope':__doc__,'trainingDictionaryHash':hashlib.sha256(raw).hexdigest(),
        'testPoolHash':hashlib.sha256(pool_raw).hexdigest(),'trainingTrials':trials,'test':result,'summary':summary}
    with (Path(destination)/f'{i}.json').open('x') as f:json.dump(out,f)
    print(json.dumps(summary),flush=True);return summary

if __name__=='__main__':
    dest=Path(sys.argv[3]).resolve();dest.mkdir()
    with ProcessPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run,[(sys.argv[1],sys.argv[2],str(dest),i) for i in range(6)]))
    (dest/'summary.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2))
