"""Frozen-weight held-out finite candidate pools and subset feasibility control.

Every training type and every site permutation gets a proper Kabsch fit to each
known-coordinate three-site support. This is not exhaustive continuous-pose
search. Candidate identity is (template, decorated target-ID point map), with
one use per identity. No one-candidate-per-observed-support constraint is added.
MILP selection is a diagnostic, not the master GCTS tree search.
"""
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('triples',HERE/'boron-triple-precheck.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def run(args):
    source,folder,index,destination,domain=args
    raw=Path(source).read_bytes();c=json.loads(raw)['results'][index]
    frozen=(Path(folder)/str(index)/'training-dictionary.json').read_bytes();data=json.loads(frozen)
    weights=list(map(Fraction,data['results'][-1]['weights']));labels=data['results'][-1]['labels']
    assert len(set(labels))==1, 'This subset control does not encode nonconstant marking conflicts.'
    types=data['types'];eps=data['epsilonAngstrom']
    bound=max(t['lengths'][1] for t in types)+2*eps if domain=='library-bound' else None
    radius,supports=m.propose_supports(c,bound)
    lengths_array=np.array([t['lengths'] for t in types]);candidates=[];seen=set();matched=set();fits=0
    for ids,positions in sorted(supports.items()):
        lengths=np.sort([np.linalg.norm(positions[a]-positions[b]) for a,b in ((0,1),(0,2),(1,2))])
        for it in np.flatnonzero(np.max(np.abs(lengths_array-lengths),axis=1)<=2*eps):
            t=types[int(it)]
            for perm in m.PERMS:
                fit=m.geom.fit(t['positions'],positions,np.array([perm]),eps)
                if fit is None:continue
                fits+=1;matched.add(ids)
                point_values=sorted((ids[p],str(weights[3*t['id']+u]),labels[3*t['id']+u]) for u,p in enumerate(fit['permutation']))
                key=(t['id'],tuple(point_values))
                if key in seen:continue
                seen.add(key);candidates.append({'ids':ids,'type':t['id'],'liftedPositions':positions.tolist(),**fit})
    totals=[Fraction(0)]*c['atoms'];rows=[];cols=[];values=[]
    for j,o in enumerate(candidates):
        for u,p in enumerate(o['permutation']):
            v=weights[3*o['type']+u];point=o['ids'][p];totals[point]+=v
            rows.append(point);cols.append(j);values.append(float(v))
    deficits=[{'point':i,'availableTotal':str(v)} for i,v in enumerate(totals) if v<1]
    summary={'heldOut':c['file'],'proposalDomain':domain,'radius':radius,'supports':len(supports),'matchedSupports':len(matched),
        'acceptedFits':fits,'distinctCandidates':len(candidates),'underCapacityPoints':len(deficits),
        'status':'exact finite-pool capacity obstruction' if deficits else 'not run'}
    selected=[]
    if not deficits:
        A=coo_matrix((values,(rows,cols)),shape=(c['atoms'],len(candidates))).tocsc()
        start=time.monotonic()
        result=milp(np.ones(len(candidates)),integrality=np.ones(len(candidates)),
            bounds=Bounds(0,1),constraints=LinearConstraint(A,1,1),options={'time_limit':30,'mip_rel_gap':0})
        summary.update(solverStatus=result.message,seconds=time.monotonic()-start)
        if result.x is None:summary['status']='numerical finite-pool infeasibility' if result.status==2 else 'unknown: subset budget'
        else:
            selected=np.flatnonzero(result.x>.5).tolist();sums=[Fraction(0)]*c['atoms']
            for j in selected:
                o=candidates[j]
                for u,p in enumerate(o['permutation']):sums[o['ids'][p]]+=weights[3*o['type']+u]
            summary.update(selected=len(selected),exactlyFilled=sum(v==1 for v in sums))
            summary['status']='exact finite-pool subset witness' if all(v==1 for v in sums) else 'unknown: numerical subset fails exact verification'
    artifact={'scope':__doc__,'sourceHash':hashlib.sha256(raw).hexdigest(),
        'frozenDictionaryHash':hashlib.sha256(frozen).hexdigest(),'epsilonAngstrom':eps,
        'summary':summary,'testConfiguration':{'file':c['file'],'atoms':c['atoms'],'radius':radius,'occurrences':candidates},
        'capacityDeficits':deficits,'selected':selected}
    with (Path(destination)/f'{index}.json').open('x') as out:json.dump(artifact,out)
    print(json.dumps(summary),flush=True);return summary

if __name__=='__main__':
    destination=Path(sys.argv[3]).resolve();destination.mkdir()
    with ProcessPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run,[(str(Path(sys.argv[1]).resolve()),str(Path(sys.argv[2]).resolve()),i,str(destination),
            sys.argv[4] if len(sys.argv)>4 else 'original') for i in range(6)]))
    (destination/'summary.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2))
